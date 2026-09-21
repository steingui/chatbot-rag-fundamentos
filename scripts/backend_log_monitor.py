#!/usr/bin/env python3
"""Monitora logs do Cloud Run (backend) e abre issue no GitHub se houver erros.

Uso:
    python scripts/backend_log_monitor.py [--since-minutes 185] [--dry-run]

Autenticação GCP: usa `gcloud` (ADC / Workload Identity Federation no runner).
Autenticação GitHub: usa GITHUB_TOKEN do ambiente (compatível com GitHub Actions).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

import requests

DEFAULT_PROJECT = os.environ.get("GCP_PROJECT_ID", "rag-eleicoes")
DEFAULT_SERVICE = "chatbot-rag-api"
ISSUE_LABEL = "backend-logs"
ERROR_SEVERITIES = {"ERROR", "CRITICAL", "ALERT", "EMERGENCY"}
HTTP_5XX_RE = re.compile(r"\bHTTP/\d\.\d\"?\s+5\d\d\b|\b5\d\d\b.*(?:Internal Server Error|Bad Gateway|Service Unavailable|Gateway Timeout)", re.IGNORECASE)
OUTBOUND_REQUEST_RE = re.compile(r"\bHTTP Request:\s+(?:GET|POST|PUT|PATCH|DELETE)\s+https?://", re.IGNORECASE)
MAX_ENTRIES_PER_GROUP = 5


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    """Executa um comando e retorna o processo concluído."""
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if check and proc.returncode != 0:
        raise RuntimeError(f"Comando falhou ({' '.join(cmd)}): {proc.stderr.strip()}")
    return proc


def fetch_logs(project: str, service: str, since_minutes: int) -> list[dict]:
    """Busca logs do Cloud Run dos últimos `since_minutes` via `gcloud logging read`."""
    since = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
    filter_expr = (
        f'resource.type="cloud_run_revision" AND '
        f'resource.labels.service_name="{service}" AND '
        f'timestamp >= "{since}"'
    )
    proc = run(
        [
            "gcloud", "logging", "read", filter_expr,
            "--project", project,
            "--format", "json",
            "--order", "asc",
            "--limit", "500",
        ],
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gcloud logging read falhou: {proc.stderr.strip()}")
    if not proc.stdout.strip():
        return []
    data = json.loads(proc.stdout)
    return data if isinstance(data, list) else []


def extract_message(entry: dict) -> str:
    """Extrai a mensagem mais útil de uma entrada de log do Cloud Run."""
    json_payload = entry.get("jsonPayload") or {}
    if isinstance(json_payload, dict):
        for key in ("message", "error", "exception", "traceback"):
            value = json_payload.get(key)
            if value:
                return str(value)
    for key in ("textPayload", "protoPayload"):
        value = entry.get(key)
        if isinstance(value, dict):
            value = value.get("line") or value.get("statusMessage") or json.dumps(value)
        if value:
            return str(value)
    return json.dumps(entry, ensure_ascii=False, default=str)


def severity_of(entry: dict) -> str:
    """Retorna a severidade normalizada da entrada."""
    sev = str(entry.get("severity", "DEFAULT")).upper()
    return sev if sev in ERROR_SEVERITIES | {"WARNING", "INFO", "NOTICE", "DEBUG", "DEFAULT"} else "DEFAULT"


_SEVERITY_RANK = {"EMERGENCY": 0, "ALERT": 1, "CRITICAL": 2, "ERROR": 3, "WARNING": 4, "NOTICE": 5, "INFO": 6, "DEBUG": 7, "DEFAULT": 8}


def max_severity(left: str, right: str) -> str:
    """Retorna a severidade mais crítica entre duas (menor rank vence)."""
    return left if _SEVERITY_RANK.get(left, 8) <= _SEVERITY_RANK.get(right, 8) else right


def is_error(entry: dict) -> bool:
    """Decide se a entrada representa um erro relevante."""
    sev = severity_of(entry)
    if sev in ERROR_SEVERITIES:
        return True
    message = extract_message(entry)
    # Request outbound do cliente HTTP (ex.: Gemini) logado como INFO não é erro do backend.
    if sev == "INFO" and OUTBOUND_REQUEST_RE.search(message):
        return False
    return bool(HTTP_5XX_RE.search(message)) or "Traceback (most recent call last)" in message


def signature(message: str) -> str:
    """Normaliza a mensagem para agrupar erros semelhantes (deduplicação)."""
    sig = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?", "<TS>", message)
    sig = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "<UUID>", sig, flags=re.IGNORECASE)
    sig = re.sub(r"\b\d{10,}\b", "<ID>", sig)
    sig = re.sub(r"0x[0-9a-fA-F]+", "<HEX>", sig)
    sig = re.sub(r"\s+", " ", sig).strip()
    return sig[:280]


def error_severity(entry: dict) -> str:
    """Severidade efetiva do erro: eleva HTTP 5xx/tracebacks logados como INFO/DEFAULT para ERROR."""
    sev = severity_of(entry)
    if sev in ERROR_SEVERITIES:
        return sev
    message = extract_message(entry)
    # Request outbound do cliente HTTP (ex.: Gemini) logado como INFO não é erro do backend.
    if sev == "INFO" and OUTBOUND_REQUEST_RE.search(message):
        return sev
    if HTTP_5XX_RE.search(message) or "Traceback (most recent call last)" in message:
        return "ERROR"
    return sev


def group_errors(entries: list[dict]) -> list[dict]:
    """Agrupa erros por assinatura, ordenados por severidade e contagem."""
    groups: dict[str, dict] = {}
    for entry in entries:
        if not is_error(entry):
            continue
        message = extract_message(entry)
        sig = signature(message)
        group = groups.setdefault(
            sig,
            {
                "signature": sig,
                "severity": "DEFAULT",
                "count": 0,
                "first_seen": entry.get("timestamp", "n/d"),
                "last_seen": entry.get("timestamp", "n/d"),
                "samples": [],
            },
        )
        group["count"] += 1
        group["severity"] = max_severity(group["severity"], error_severity(entry))
        if entry.get("timestamp", "") < group["first_seen"]:
            group["first_seen"] = entry["timestamp"]
        if entry.get("timestamp", "") > group["last_seen"]:
            group["last_seen"] = entry["timestamp"]
        if len(group["samples"]) < MAX_ENTRIES_PER_GROUP:
            group["samples"].append(message[:500])

    rank = {"EMERGENCY": 0, "ALERT": 1, "CRITICAL": 2, "ERROR": 3, "WARNING": 4, "DEFAULT": 9}
    return sorted(
        groups.values(),
        key=lambda g: (rank.get(g["severity"], 9), -g["count"], g["last_seen"]),
    )


def build_issue_body(project: str, service: str, since_minutes: int, groups: list[dict]) -> str:
    """Monta o corpo Markdown da issue."""
    total = sum(g["count"] for g in groups)
    lines = [
        f"## 🚨 Erros detectados no backend ({service})",
        "",
        f"- **Projeto GCP**: `{project}`",
        f"- **Janela analisada**: últimos {since_minutes} min",
        f"- **Ocorrências de erro**: {total}",
        f"- **Grupos distintos**: {len(groups)}",
        "",
        "### Resumo por assinatura",
        "",
        "| Severidade | Ocorrências | Primeira | Última | Assinatura |",
        "|------------|------------:|----------|--------|------------|",
    ]
    for g in groups:
        first = (g["first_seen"] or "n/d")[:19]
        last = (g["last_seen"] or "n/d")[:19]
        lines.append(
            f"| {g['severity']} | {g['count']} | {first} | {last} | `{g['signature'][:120]}` |"
        )
    lines += ["", "### Amostras", ""]
    for i, g in enumerate(groups, start=1):
        lines.append(f"**{i}. {g['severity']} ×{g['count']}** — `{g['signature'][:120]}`")
        for sample in g["samples"]:
            lines.append(f"```\n{sample}\n```")
        lines.append("")
    lines += [
        "---",
        "_Issue gerada automaticamente por `scripts/backend_log_monitor.py` via workflow "
        "`.github/workflows/backend-log-monitor.yml`._",
    ]
    return "\n".join(lines)


def github_session() -> tuple[requests.Session, str]:
    """Cria sessão autenticada contra a API do GitHub e retorna o repo `owner/name`."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token:
        raise RuntimeError("GITHUB_TOKEN não definido no ambiente.")
    if not repo:
        raise RuntimeError("GITHUB_REPOSITORY não definido no ambiente.")
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )
    return session, repo


def find_open_issue(session: requests.Session, repo: str) -> dict | None:
    """Retorna a issue aberta mais recente com o label do monitor, se existir."""
    resp = session.get(
        f"https://api.github.com/repos/{repo}/issues",
        params={"state": "open", "labels": ISSUE_LABEL, "per_page": 1},
        timeout=30,
    )
    resp.raise_for_status()
    issues = resp.json()
    return issues[0] if issues else None


def create_issue(session: requests.Session, repo: str, title: str, body: str) -> dict:
    """Cria a issue e retorna o JSON da resposta."""
    resp = session.post(
        f"https://api.github.com/repos/{repo}/issues",
        json={"title": title, "body": body, "labels": [ISSUE_LABEL]},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def comment_issue(session: requests.Session, repo: str, number: int, body: str) -> None:
    """Adiciona um comentário a uma issue existente."""
    resp = session.post(
        f"https://api.github.com/repos/{repo}/issues/{number}/comments",
        json={"body": body},
        timeout=30,
    )
    resp.raise_for_status()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-minutes", type=int, default=180, help="Janela de análise em minutos (default: 180)")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="Projeto GCP (default: rag-eleicoes)")
    parser.add_argument("--service", default=DEFAULT_SERVICE, help="Serviço Cloud Run (default: chatbot-rag-api)")
    parser.add_argument("--dry-run", action="store_true", help="Não cria/atualiza issue; apenas imprime o relatório")
    args = parser.parse_args()

    entries = fetch_logs(args.project, args.service, args.since_minutes)
    groups = group_errors(entries)

    if not groups:
        print(f"✅ Nenhum erro detectado em {args.service} nos últimos {args.since_minutes} min.")
        return 0

    total = sum(g["count"] for g in groups)
    print(f"⚠️ {total} ocorrências de erro agrupadas em {len(groups)} assinaturas.")
    body = build_issue_body(args.project, args.service, args.since_minutes, groups)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    title = f"🚨 Erros no backend ({args.service}) — {now}"

    if args.dry_run:
        print("\n" + title + "\n" + body)
        return 0

    session, repo = github_session()
    existing = find_open_issue(session, repo)
    if existing:
        comment_issue(
            session,
            repo,
            existing["number"],
            f"Novo ciclo de monitoramento ({now}) detectou {total} ocorrências:\n\n{body}",
        )
        print(f"💬 Issue #{existing['number']} já aberta — comentário adicionado.")
    else:
        created = create_issue(session, repo, title, body)
        print(f"📝 Issue criada: {created['html_url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
