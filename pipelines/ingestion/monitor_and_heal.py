import os
import re
import json
import logging
import warnings
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Silencia avisos internos de Automatic Function Calling (AFC) do SDK Google Gemini
warnings.filterwarnings("ignore", message=".*automatic function calling.*")
warnings.filterwarnings("ignore", category=UserWarning, module="google.generativeai")
logging.getLogger("google.generativeai").setLevel(logging.ERROR)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
DOCS_DIR = Path("data/docs")
REPORT_PATH = DOCS_DIR / "pipeline_health_report.md"

def audit_and_heal_local_docs() -> dict:
    """Audit local data/docs Markdown files, fix formatting issues, and purge empty/corrupt files."""
    stats = {"total_files": 0, "fixed_files": 0, "purged_files": 0, "corrupt_files": 0}
    
    if not DOCS_DIR.exists():
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        return stats
        
    for filepath in DOCS_DIR.glob("*.md"):
        if filepath.name == REPORT_PATH.name:
            continue
            
        stats["total_files"] += 1
        try:
            content = filepath.read_text(encoding="utf-8").strip()
            
            # Remove arquivos vazios ou extremamente curtos (< 50 caracteres)
            if len(content) < 50:
                logging.warning(f"Purging corrupt/empty file: {filepath.name}")
                filepath.unlink()
                stats["purged_files"] += 1
                continue
                
            # Autocorreção: Adiciona tag de cabeçalho [TEMA: ...] caso o arquivo não possua uma tag inicial
            fixed_content = content
            if not content.startswith("["):
                category = filepath.name.split("_")[0].upper()
                fixed_content = f"[CATEGORIA: {category}]\n" + content
                stats["fixed_files"] += 1
                
            # Autocorreção: Remove caracteres nulos ou sequências quebradas
            fixed_content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', fixed_content)
            
            if fixed_content != content:
                filepath.write_text(fixed_content, encoding="utf-8")
                
        except Exception as e:
            logging.error(f"Erro ao auditar {filepath.name}: {e}")
            stats["corrupt_files"] += 1
            
    return stats

def audit_pinecone_health() -> dict:
    """Verifica a contagem e sanidade do índice no Pinecone DB."""
    try:
        from pinecone import Pinecone
        api_key = os.environ.get("PINECONE_API_KEY")
        if not api_key:
            return {"status": "ERROR", "message": "PINECONE_API_KEY ausente"}
            
        pc = Pinecone(api_key=api_key)
        index_name = os.environ.get("PINECONE_INDEX_NAME", "rag-fundamentos")
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        
        vector_count = stats.get("namespaces", {}).get("", {}).get("vector_count", 0)
        return {
            "status": "OK" if vector_count > 0 else "WARNING",
            "total_vectors": vector_count,
            "dimension": stats.get("dimension", 384)
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def audit_github_workflows() -> list:
    """Consulta o status das últimas 5 execuções de CADA pipeline de ingestão via API REST do GitHub."""
    repo = os.environ.get("GITHUB_REPOSITORY", "steingui/chatbot-rag-fundamentos")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=100"
    grouped_runs = {}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            runs = res.json().get("workflow_runs", [])
            seen_ids = set()
            for r in runs:
                run_id = r.get("id")
                if run_id in seen_ids:
                    continue
                seen_ids.add(run_id)

                wf_name = r.get("name", "Outros Workflows")
                if wf_name not in grouped_runs:
                    grouped_runs[wf_name] = []
                
                # Mantém no máximo as 5 execuções mais recentes por pipeline
                if len(grouped_runs[wf_name]) < 5:
                    grouped_runs[wf_name].append({
                        "name": wf_name,
                        "status": r.get("status"),
                        "conclusion": r.get("conclusion"),
                        "created_at": r.get("created_at"),
                        "run_id": run_id
                    })
    except Exception as e:
        logging.error(f"Erro ao consultar execuções das GitHub Actions: {e}")
        
    return grouped_runs

def _clean_llm_response(content) -> str:
    """Extrai apenas o texto legível, removendo metadados, tokens de auth, assinaturas e dicionários brutos."""
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
            elif isinstance(item, str):
                text_parts.append(item)
        content = "\n".join(text_parts)
    elif not isinstance(content, str):
        content = str(content)

    # 1. Trata erros HTTP de autenticação ou chaves ausentes
    if "401" in content or "Missing Authentication" in content or "Unauthorized" in content:
        return "Diagnóstico suspenso: Nenhuma chave de API de LLM válida configurada no ambiente."

    # 2. Remove assinaturas e metadados brutos (como 'extras', 'signature', JWTs, hashes)
    content = re.sub(r"'extras':\s*\{.*?\}", "", content, flags=re.DOTALL)
    content = re.sub(r"\'signature\':\s*\'[^\']+\'", "", content)
    content = re.sub(r"eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*", "[TOKEN_OMITTED]", content)
    
    # 3. Desescapa quebras de linha e aspas brutas
    content = content.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')

    # 4. Remove blocos de dicionários brutos contendo 'type' ou 'extras'
    content = re.sub(r"\[\s*\{'type':.*?'extras':.*?\}\s*\]", "", content, flags=re.DOTALL)
    
    return content.strip()

def get_codebase_context() -> str:
    """Carrega o código fonte dos scripts de ingestão e workflows para fornecer contexto completo à LLM."""
    code_context = []
    base_dir = Path(__file__).resolve().parent.parent.parent
    
    # Scripts de Ingestão
    ingest_dir = base_dir / "pipelines" / "ingestion"
    if ingest_dir.exists():
        for file in ingest_dir.glob("*.py"):
            try:
                content = file.read_text(encoding="utf-8")
                lines = content.splitlines()[:250]
                code_context.append(f"--- FILE: {file.relative_to(base_dir)} ---\n" + "\n".join(lines))
            except Exception:
                pass

    # Workflows YAML
    wf_dir = base_dir / ".github" / "workflows"
    if wf_dir.exists():
        for file in wf_dir.glob("*.yml"):
            try:
                content = file.read_text(encoding="utf-8")
                code_context.append(f"--- WORKFLOW: {file.relative_to(base_dir)} ---\n" + content)
            except Exception:
                pass

    return "\n\n".join(code_context)

def get_failed_run_logs(run_id: int) -> str:
    """Busca os detalhes dos erros e etapas com falha do job via API REST do GitHub."""
    repo = os.environ.get("GITHUB_REPOSITORY", "steingui/chatbot-rag-fundamentos")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/jobs"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            jobs = res.json().get("jobs", [])
            failed_jobs_info = []
            for j in jobs:
                if j.get("conclusion") == "failure":
                    steps_failed = [
                        f"  - Step '{s['name']}' ({s.get('conclusion')})"
                        for s in j.get("steps", []) if s.get("conclusion") == "failure"
                    ]
                    failed_jobs_info.append(f"Job `{j.get('name')}` falhou nas etapas:\n" + "\n".join(steps_failed))
            return "\n".join(failed_jobs_info)
    except Exception as e:
        logging.warning(f"Não foi possível obter logs detalhados do run {run_id}: {e}")
    return "Logs detalhados indisponíveis."

def analyze_failures_with_llm(failed_runs: list) -> str:
    """Utiliza o modelo Google Gemini (plano Antigravity) para analisar falhas com contexto da codebase inteira."""
    google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not failed_runs:
        return "Nenhuma falha detectada nas últimas execuções."
        
    if not google_key and not openrouter_key:
        return "Nenhuma falha crítica ou chave de API (GOOGLE_API_KEY / GEMINI_API_KEY / OPENROUTER_API_KEY) ausente para diagnóstico via LLM."
        
    # Enriquece os runs com os logs de falha das etapas do job
    enriched_runs = []
    for r in failed_runs:
        run_copy = dict(r)
        run_copy["job_details"] = get_failed_run_logs(r["run_id"])
        enriched_runs.append(run_copy)

    codebase_context = get_codebase_context()

    prompt = (
        f"Você é um especialista sênior em engenharia de dados e CI/CD do repositório Antigravity.\n\n"
        f"### CONTEXTO DA CODEBASE (SCRIPTS DE INGESTÃO & WORKFLOWS):\n"
        f"{codebase_context}\n\n"
        f"### FALHAS DETECTADAS NAS ÚLTIMAS EXECUÇÕES DO GITHUB ACTIONS:\n"
        f"{json.dumps(enriched_runs, indent=2)}\n\n"
        f"INSTRUÇÕES DE RESPOSTA:\n"
        f"1. Responda apenas com o diagnóstico essencial (Causa Raiz) e o diff/snippet de correção em Python/YAML.\n"
        f"2. NUNCA inclua tokens, assinaturas criptográficas, hashes ou dumps de dicionários Python.\n"
        f"3. Seja conciso e vá direto ao ponto."
    )

    # Prioridade 1: Google Gemini (Plano Antigravity)
    if google_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-3.6-flash",
                google_api_key=google_key,
                temperature=0.1,
                max_retries=2
            )
            response = llm.invoke(prompt)
            clean_text = _clean_llm_response(response.content)
            return f"**[Diagnóstico Gemini 3.6 Flash (Google Antigravity com Contexto de Codebase)]**\n{clean_text}"
        except Exception as e:
            logging.warning(f"Falha ao invocar Google Gemini API: {e}. Tentando fallback OpenRouter...")

    # Fallback: OpenRouter API
    if openrouter_key:
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model="meta-llama/llama-3.3-70b-instruct:free",
                openai_api_key=openrouter_key,
                openai_api_base="https://openrouter.ai/api/v1",
                max_retries=2,
                temperature=0.1
            )
            response = llm.invoke(prompt)
            clean_text = _clean_llm_response(response.content)
            return f"**[Diagnóstico OpenRouter Fallback]**\n{clean_text}"
        except Exception as e:
            logging.error(f"Erro na análise autônoma via OpenRouter: {e}")
            return _clean_llm_response(str(e))

    return "Diagnóstico suspenso: Nenhuma chave de API de LLM válida configurada no ambiente."

def check_daily_commit_count(max_daily_commits: int = 10) -> bool:
    """Verifica se o número de commits [LLM-COMMIT-AND-HEAL] realizados no dia atual é menor que 10."""
    try:
        import subprocess
        cmd = 'git log --since="today 00:00:00" --grep="\\[LLM-COMMIT-AND-HEAL\\]" --oneline'
        res = subprocess.check_output(cmd, shell=True, text=True).strip()
        count = len([line for line in res.split('\n') if line]) if res else 0
        logging.info(f"Commits autônomos [LLM-COMMIT-AND-HEAL] hoje: {count}/{max_daily_commits}")
        return count < max_daily_commits
    except Exception as e:
        logging.error(f"Erro ao verificar limite de commits: {e}")
        return True

def should_trigger_commit(doc_stats: dict, pinecone_stats: dict, failed_runs: list) -> bool:
    """Determina se as alterações possuem alta importância e se o limite diário de 10 commits não foi atingido."""
    is_high_importance = (
        doc_stats.get("fixed_files", 0) > 0 or
        doc_stats.get("purged_files", 0) > 0 or
        pinecone_stats.get("status") != "OK" or
        len(failed_runs) > 0
    )
    
    if not is_high_importance:
        logging.info("Ignorando commit: Nenhuma alteração crítica ou falha de alta importância foi detectada.")
        return False
        
    under_limit = check_daily_commit_count(max_daily_commits=10)
    if not under_limit:
        logging.warning("Ignorando commit: Limite de 10 commits autônomos por dia foi atingido.")
        return False
        
    return True

def main():
    logging.info("Iniciando auditoria e autocorreção autônoma de dados e workflows...")
    
    doc_stats = audit_and_heal_local_docs()
    pinecone_stats = audit_pinecone_health()
    grouped_runs = audit_github_workflows()
    
    # Coleta todas as falhas das últimas 5 execuções de cada pipeline para análise via LLM
    all_failed_runs = []
    wf_sections = []
    
    for wf_name, runs in grouped_runs.items():
        run_bullets = []
        for r in runs:
            status_str = r.get("conclusion") or r.get("status")
            run_bullets.append(f"  - Execução ID `{r['run_id']}` ({r['created_at']}): `{status_str}`")
            if r.get("conclusion") in ["failure", "cancelled", "timed_out"]:
                all_failed_runs.append(r)
        
        wf_sections.append(f"### {wf_name}\n" + "\n".join(run_bullets))
        
    wf_text = "\n\n".join(wf_sections) if wf_sections else "Nenhuma execução recente rastreada via API."
    llm_diagnosis = analyze_failures_with_llm(all_failed_runs) if all_failed_runs else "Todos os workflows das últimas 5 execuções operaram com 100% de sucesso."
    
    report_content = (
        f"[PIPELINE_MONITOR: SAÚDE E QUALIDADE DOS DADOS]\n"
        f"# Relatório Autônomo de Monitoramento e Auto-Cura\n\n"
        f"**Status Pinecone:** `{pinecone_stats.get('status')}` | **Total Vetores:** {pinecone_stats.get('total_vectors', 0)}\n\n"
        f"## Auditoria e Auto-Cura de Documentos Local (`data/docs`)\n"
        f"- **Total de Arquivos:** {doc_stats['total_files']}\n"
        f"- **Arquivos Auto-Corrigidos:** {doc_stats['fixed_files']}\n"
        f"- **Arquivos Purgados (Inválidos/Vazios):** {doc_stats['purged_files']}\n\n"
        f"## Últimas 5 Execuções por Pipeline de Ingestão (GitHub Actions)\n"
        f"{wf_text}\n\n"
        f"## Diagnóstico Autônomo de LLM (`[LLM-COMMIT-AND-HEAL]`)\n"
        f"{llm_diagnosis}\n"
    )
    
    REPORT_PATH.write_text(report_content, encoding="utf-8")
    logging.info("Relatório autônomo gerado em data/docs/pipeline_health_report.md")
    
    # Avalia portão de commit por alta importância e limite diário (max 10 commits)
    can_commit = should_trigger_commit(doc_stats, pinecone_stats, all_failed_runs)
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"should_commit={'true' if can_commit else 'false'}\n")

if __name__ == "__main__":
    main()
