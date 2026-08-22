import os
import re
import json
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

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
            for r in runs:
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
                        "run_id": r.get("id")
                    })
    except Exception as e:
        logging.error(f"Erro ao consultar execuções das GitHub Actions: {e}")
        
    return grouped_runs

def analyze_failures_with_llm(failed_runs: list) -> str:
    """Utiliza o modelo Google Gemini (plano Antigravity) para analisar falhas detectadas e sugerir correções autônomas."""
    google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not failed_runs:
        return "Nenhuma falha detectada nas últimas execuções."
        
    if not google_key and not openrouter_key:
        return "Nenhuma falha crítica ou chave de API (GOOGLE_API_KEY / GEMINI_API_KEY / OPENROUTER_API_KEY) ausente para diagnóstico via LLM."
        
    prompt = (
        f"Você é um engenheiro de dados sênior e especialista em CI/CD do Antigravity. "
        f"As seguintes GitHub Actions falharam no pipeline de dados do RAG político:\n"
        f"{json.dumps(failed_runs, indent=2)}\n\n"
        f"Forneça uma análise técnica concisa da provável causa raiz e a correção exata em Python/YAML com o prefixo [LLM-COMMIT-AND-HEAL]."
    )

    # Prioridade 1: Google Gemini (Plano Antigravity)
    if google_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=google_key,
                temperature=0.1,
                max_retries=2
            )
            response = llm.invoke(prompt)
            return f"**[Diagnóstico Gemini (Google Antigravity)]**\n{response.content}"
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
            return f"**[Diagnóstico OpenRouter Fallback]**\n{response.content}"
        except Exception as e:
            logging.error(f"Erro na análise autônoma via OpenRouter: {e}")
            return f"Falha ao consultar LLM para diagnóstico: {e}"

    return "Falha ao executar diagnóstico por ausência de chaves de API válidas."

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

if __name__ == "__main__":
    main()
