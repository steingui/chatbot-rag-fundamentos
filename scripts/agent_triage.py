#!/usr/bin/env python3
"""
scripts/agent_triage.py
Script do Agente Engenheiro para triagem autônoma de issues de QA e diagnóstico de causa raiz.
"""

import json
import re
import subprocess
import sys
from typing import Dict, List, Optional


# Mapeamento heurístico de componentes por domínio de palavras-chave
CODEBASE_MAP = {
    "fontes": {
        "files": ["backend/rag/chat.py", "backend/api/main.py"],
        "symbols": ["_buscar_noticias_web", "parse_source_name", "_clean_url"],
        "cause": "Falha na extração de metadados das fontes do RAG ou limpeza inadequadas de URLs (UTM/parâmetros).",
        "fix": "Revisar a normalização de URLs e garantir que a lista de `SourceObject` inclua as propriedades `url` e `label` tratadas."
    },
    "truncado": {
        "files": ["backend/rag/chat.py"],
        "symbols": ["get_rag_chain", "init_components"],
        "cause": "Limite de max_tokens na resposta do LLM ou instrução de sistema não enfatizando completude.",
        "fix": "Ajustar o prompt do sistema para proibir o uso de reticências (...) e ampliar a contagem máxima de tokens de resposta."
    },
    "guardrail": {
        "files": ["backend/api/guardrails.py", "backend/api/main.py"],
        "symbols": ["validate_and_sanitize_query", "sanitize_input"],
        "cause": "Padrões de Regex de jailbreak/injection insuficientes ou falta de regras de bloqueio para domínios fora de escopo.",
        "fix": "Atualizar a lista de termos proibidos em `guardrails.py` e garantir retorno HTTP 400 tratável."
    },
    "stream": {
        "files": ["frontend/src/store/useChatStore.ts", "frontend/src/components/MessageList.tsx"],
        "symbols": ["abortController", "useChatStore"],
        "cause": "Falta de manipulador AbortController na requisição Fetch/SSE ou ausência de sinal no estado global do Zustand.",
        "fix": "Adicionar AbortController na chamada de streaming do frontend e expor a ação `cancelCurrentStream()` na UI."
    }
}


def fetch_qa_issues() -> List[Dict]:
    """Busca issues abertas com a label 'qa-automation' via GitHub CLI."""
    cmd = [
        "gh", "issue", "list",
        "--label", "qa-automation",
        "--json", "number,title,body,comments"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Erro ao buscar issues no GitHub: {e.stderr}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Erro inesperado: {e}", file=sys.stderr)
        return []


def analyze_issue(title: str, body: str) -> Dict:
    """Cruza o conteúdo da issue com o mapa da codebase para gerar diagnóstico."""
    text_content = f"{title} {body}".lower()
    
    matched_component = None
    for keyword, info in CODEBASE_MAP.items():
        if keyword in text_content or any(term in text_content for term in keyword.split()):
            matched_component = info
            break
            
    if not matched_component:
        # Fallback genérico caso não combine diretamente com as palavras-chave padrão
        matched_component = {
            "files": ["backend/rag/chat.py", "backend/api/main.py"],
            "symbols": ["get_rag_chain"],
            "cause": "Comportamento inesperado na camada RAG ou na rota de API de chat.",
            "fix": "Realizar depuração estática dos parâmetros da requisição e validar os logs de execução do Cloud Run."
        }
        
    return matched_component


def format_triage_comment(analysis: Dict) -> str:
    """Formata o comentário de diagnóstico do Agente Engenheiro."""
    files_str = "\n".join([f"- `{f}`" for f in analysis["files"]])
    symbols_str = ", ".join([f"`{s}`" for s in analysis["symbols"]])
    
    comment = f"""### 🔍 Análise de Causa Raiz pelo Agente Engenheiro

**Diagnóstico Provável**:
{analysis['cause']}

**Arquivos & Módulos Afetados**:
{files_str}
- **Símbolos / Funções**: {symbols_str}

**💡 Plano de Solução Recomendado**:
{analysis['fix']}

---
*Diagnóstico gerado automaticamente pelo Agente Engenheiro (Fase 2).*"""
    return comment


def post_triage_comment(issue_number: int, comment: str, dry_run: bool = False):
    """Publica o comentário na issue no GitHub ou simula se dry_run=True."""
    if dry_run:
        print(f"[DRY-RUN] Comentário para Issue #{issue_number}:\n{comment}\n")
        return
        
    cmd = ["gh", "issue", "comment", str(issue_number), "--body", comment]
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Diagnóstico publicado na Issue #{issue_number}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao comentar na Issue #{issue_number}: {e.stderr}", file=sys.stderr)


def run_triage(dry_run: bool = False):
    print(f"🚀 Iniciando triagem do Agente Engenheiro (dry_run={dry_run})...")
    issues = fetch_qa_issues()
    if not issues:
        print("Nenhuma issue com a label 'qa-automation' encontrada para triagem.")
        return
        
    for issue in issues:
        num = issue["number"]
        title = issue["title"]
        body = issue.get("body", "")
        comments = issue.get("comments", [])
        
        # Evita publicar duplicado se o Agente já comentou
        already_triaged = any("Agente Engenheiro" in c.get("body", "") for c in comments)
        if already_triaged:
            print(f"Skipping Issue #{num}: Já possui diagnóstico do Agente Engenheiro.")
            continue
            
        print(f"Analisando Issue #{num}: {title}...")
        analysis = analyze_issue(title, body)
        comment = format_triage_comment(analysis)
        post_triage_comment(num, comment, dry_run=dry_run)


if __name__ == "__main__":
    is_dry_run = "--dry-run" in sys.argv
    run_triage(dry_run=is_dry_run)
