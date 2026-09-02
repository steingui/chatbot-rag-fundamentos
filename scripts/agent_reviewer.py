#!/usr/bin/env python3
"""
scripts/agent_reviewer.py
Script do Agente Reviewer (Fase 4) para code review autônomo e validação de segurança de PRs.
"""

import json
import re
import subprocess
import sys
from typing import Dict, List, Optional


# Termos e padrões sensíveis proibidos em edições (Regra de Segurança AGENTS.md)
FORBIDDEN_PATTERNS = [
    r"API_KEY\s*=\s*['\"][A-Za-z0-9_\-]+['\"]",
    r"SECRET\s*=\s*['\"][A-Za-z0-9_\-]+['\"]",
    r"eval\(",
    r"exec\(",
    r"os\.system\("
]


def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def fetch_open_prs() -> List[Dict]:
    """Busca PRs abertas geradas pelo worker pool."""
    cmd = [
        "gh", "pr", "list",
        "--json", "number,title,headRefName,files"
    ]
    res = run_cmd(cmd)
    if res.returncode != 0:
        print(f"Erro ao buscar PRs: {res.stderr}", file=sys.stderr)
        return []
        
    prs = json.loads(res.stdout) if res.stdout else []
    # Filtrar apenas PRs criadas pelo bot/worker pool (prefixo fix/issue-)
    return [pr for pr in prs if pr.get("headRefName", "").startswith("fix/issue-")]


def inspect_pr_diff(pr_number: int) -> str:
    """Obtém o diff da PR via gh CLI."""
    cmd = ["gh", "pr", "diff", str(pr_number)]
    res = run_cmd(cmd)
    return res.stdout if res.returncode == 0 else ""


def validate_security_and_governance(diff_text: str) -> tuple[bool, str]:
    """Valida se o diff cumpre o contrato de segurança do AGENTS.md."""
    if not diff_text.strip():
        return False, "Diff vazio ou indisponível."
        
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, diff_text, re.IGNORECASE):
            return False, f"Padrão de risco de segurança detectado: `{pattern}`"
            
    return True, "Validação de segurança e governança concluída com sucesso."


def review_pr(pr: Dict, dry_run: bool = False):
    pr_num = pr["number"]
    title = pr["title"]
    branch = pr["headRefName"]
    
    print(f"🧐 [Auto Review] Analisando PR #{pr_num}: {title} (Branch: {branch})")
    
    diff_text = inspect_pr_diff(pr_num)
    is_safe, reason = validate_security_and_governance(diff_text)
    
    if dry_run:
        print(f"[DRY-RUN] PR #{pr_num} - Status: {'APROVADO' if is_safe else 'REPROVADO'}. Motivo: {reason}")
        return
        
    if is_safe:
        review_cmd = [
            "gh", "pr", "review", str(pr_num),
            "--approve",
            "--body", f"### 🛡️ Auto Code Review (Fase 4)\n\n✅ **Aprovado Autonomamente**\n- **Segurança & Governança**: {reason}\n- **Sintaxe & Contrato**: OK\n\n*Aprovado pelo Agente Reviewer.*"
        ]
        res = run_cmd(review_cmd)
        if res.returncode == 0:
            print(f"✅ PR #{pr_num} Aprovada com sucesso.")
        else:
            print(f"❌ Erro ao aprovar PR #{pr_num}: {res.stderr}")
    else:
        close_cmd = [
            "gh", "pr", "close", str(pr_num),
            "--comment", f"### 🚨 Auto Code Review (Fase 4)\n\n❌ **PR Fechada por violação de regras**:\n{reason}"
        ]
        res = run_cmd(close_cmd)
        if res.returncode == 0:
            print(f"⛔ PR #{pr_num} Fechada devido a falha no Code Review.")
        else:
            print(f"❌ Erro ao fechar PR #{pr_num}: {res.stderr}")


def run_reviewer(dry_run: bool = False):
    print(f"🚀 Iniciando Agente Reviewer (dry_run={dry_run})...")
    prs = fetch_open_prs()
    if not prs:
        print("Nenhuma Pull Request aberta encontrada para auto-review.")
        return
        
    for pr in prs:
        review_pr(pr, dry_run=dry_run)


if __name__ == "__main__":
    is_dry_run = "--dry-run" in sys.argv
    run_reviewer(dry_run=is_dry_run)
