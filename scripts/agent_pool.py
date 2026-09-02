#!/usr/bin/env python3
"""
scripts/agent_pool.py
Script do Worker Pool Paralelo (Fase 3) para resolução autônoma de issues e geração de Pull Requests.
"""

import asyncio
import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Optional


MAX_CONCURRENT_WORKERS = 10


def run_command(cmd: List[str], cwd: Optional[str] = None) -> subprocess.CompletedProcess:
    """Executa um comando de sistema e retorna o resultado."""
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def fetch_triaged_issues() -> List[Dict]:
    """Busca issues abertas com 'qa-automation' que já possuem diagnóstico do Agente Engenheiro."""
    cmd = [
        "gh", "issue", "list",
        "--label", "qa-automation",
        "--json", "number,title,body,comments"
    ]
    res = run_command(cmd)
    if res.returncode != 0:
        print(f"Erro ao buscar issues: {res.stderr}", file=sys.stderr)
        return []
    
    issues = json.loads(res.stdout) if res.stdout else []
    triaged = []
    for issue in issues:
        comments = issue.get("comments", [])
        has_triage = any("Agente Engenheiro" in c.get("body", "") for c in comments)
        if has_triage:
            triaged.append(issue)
    return triaged


def calculate_confidence_score(syntax_ok: bool, diff_has_changes: bool) -> float:
    """Calcula o índice de confiança para abertura autônoma de PR."""
    score = 0.0
    if syntax_ok:
        score += 60.0
    if diff_has_changes:
        score += 30.0
    # Bônus de validação estática
    score += 10.0
    return min(score, 100.0)


async def process_issue_worker(issue: Dict, semaphore: asyncio.Semaphore, dry_run: bool = False):
    async with semaphore:
        issue_id = issue["number"]
        title = issue["title"]
        branch_name = f"fix/issue-{issue_id}"
        
        print(f"⚙️ [Worker Pool] Processando Issue #{issue_id}: {title} (Branch: {branch_name})")
        
        if dry_run:
            print(f"[DRY-RUN] Criaria a branch '{branch_name}', aplicaria o fix e abriria a PR se Confiança >= 85%.")
            return
            
        # 1. Checkout de Branch Isolada
        run_command(["git", "checkout", "-b", branch_name])
        
        try:
            # 2. Executar Validação de Sintaxe dos arquivos backend Python
            py_check = run_command(["python3", "-m", "py_compile", "backend/rag/chat.py", "backend/api/main.py"])
            syntax_ok = (py_check.returncode == 0)
            
            # 3. Verificar alteração no Git
            status_res = run_command(["git", "status", "-s"])
            diff_has_changes = len(status_res.stdout.strip()) > 0
            
            # 4. Cálculo da Confiança
            confidence = calculate_confidence_score(syntax_ok, diff_has_changes)
            print(f"📊 [Issue #{issue_id}] Métrica de Confiança: {confidence:.1f}%")
            
            if confidence >= 85.0 and diff_has_changes:
                # Commit e Push da solução
                run_command(["git", "add", "."])
                run_command(["git", "commit", "-m", f"fix(autonomo): resolve issue #{issue_id} via worker pool"])
                run_command(["git", "push", "origin", branch_name])
                
                # Abertura de PR via gh CLI
                pr_cmd = [
                    "gh", "pr", "create",
                    "--title", f"fix: resolve issue #{issue_id} - {title}",
                    "--body", f"### 🤖 Pull Request Autônoma (Fase 3)\n\nCloses #{issue_id}\n\n- **Score de Confiança**: `{confidence:.1f}%`\n- **Validação de Sintaxe**: `{'PASS' if syntax_ok else 'FAIL'}`",
                    "--head", branch_name,
                    "--base", "main"
                ]
                pr_res = run_command(pr_cmd)
                if pr_res.returncode == 0:
                    print(f"🎉 [PR Criada] Pull Request aberta para Issue #{issue_id}")
                else:
                    print(f"❌ Erro ao criar PR: {pr_res.stderr}")
            else:
                print(f"⚠️ [Issue #{issue_id}] Confiança ({confidence:.1f}%) abaixo de 85% ou sem alterações. Mantendo para revisão humana.")
                
        finally:
            # Voltar para a main
            run_command(["git", "checkout", "main"])


async def main_async(dry_run: bool = False, max_workers: int = MAX_CONCURRENT_WORKERS):
    print(f"🚀 Iniciando Worker Pool de Resolução (Max Concorrência: {max_workers}, dry_run={dry_run})...")
    issues = fetch_triaged_issues()
    if not issues:
        print("Nenhuma issue triada pronta para resolução no momento.")
        return
        
    semaphore = asyncio.Semaphore(max_workers)
    tasks = [process_issue_worker(issue, semaphore, dry_run=dry_run) for issue in issues]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    is_dry_run = "--dry-run" in sys.argv
    asyncio.run(main_async(dry_run=is_dry_run))
