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
    """Consulta o status das últimas execuções das GitHub Actions via API REST."""
    repo = os.environ.get("GITHUB_REPOSITORY", "steingui/chatbot-rag-fundamentos")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=10"
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            runs = res.json().get("workflow_runs", [])
            return [
                {
                    "name": r.get("name"),
                    "status": r.get("status"),
                    "conclusion": r.get("conclusion"),
                    "created_at": r.get("created_at")
                }
                for r in runs
            ]
    except Exception as e:
        logging.error(f"Erro ao consultar execuções das GitHub Actions: {e}")
        
    return []

def main():
    logging.info("Iniciando auditoria e autocorreção autônoma de dados e workflows...")
    
    doc_stats = audit_and_heal_local_docs()
    pinecone_stats = audit_pinecone_health()
    workflow_runs = audit_github_workflows()
    
    # Gera relatório Markdown consolidado
    wf_text = "\n".join([
        f"- **{wf['name']}**: `{wf['conclusion'] or wf['status']}` ({wf['created_at']})"
        for wf in workflow_runs[:5]
    ]) or "Nenhuma execução registrada recentemente via API."
    
    report_content = (
        f"[PIPELINE_MONITOR: SAÚDE E QUALIDADE DOS DADOS]\n"
        f"# Relatório Autônomo de Monitoramento e Auto-Cura\n\n"
        f"**Status Pinecone:** `{pinecone_stats.get('status')}` | **Total Vetores:** {pinecone_stats.get('total_vectors', 0)}\n\n"
        f"## Auditoria e Auto-Cura de Documentos Local (`data/docs`)\n"
        f"- **Total de Arquivos:** {doc_stats['total_files']}\n"
        f"- **Arquivos Auto-Corrigidos:** {doc_stats['fixed_files']}\n"
        f"- **Arquivos Purgados (Inválidos/Vazios):** {doc_stats['purged_files']}\n\n"
        f"## Status das Últimas Execuções de Workflows (GitHub Actions)\n"
        f"{wf_text}\n"
    )
    
    REPORT_PATH.write_text(report_content, encoding="utf-8")
    logging.info("Relatório autônomo gerado em data/docs/pipeline_health_report.md")

if __name__ == "__main__":
    main()
