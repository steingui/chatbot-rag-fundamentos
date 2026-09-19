#!/usr/bin/env python3
"""
scripts/agent_rag_tester.py
Agente de QA para testes E2E do RAG por persona.

Cada persona de `personas/*.md` é lida do disco (nada hardcoded) e exercitada
contra o endpoint `POST /api/v1/chat` com a cadeia RAG e o Firebase mockados,
preservando o fluxo real: rota → guardrails → parse_source_name → contrato da
resposta. Cada persona possui MÚLTIPLAS iterações (prompts) executadas na MESMA
sessão (multi-turn). Uma issue de QA é aberta por falha detectada (ou apenas
simulada em --dry-run).
"""

import argparse
import os
import subprocess
import sys
from typing import Dict, List
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from backend.api.main import app

DEFAULT_PERSONAS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "personas")
)

# Expectativa derivada do slug de cada persona. Mantém o contrato do ciclo:
# adversarial → bloqueio, leigo → resposta válida, jornalista → fontes,
# pesquisador → sem truncamento.
EXPECTATION_BY_SLUG = {
    "qa_adversarial": "blocked",
    "eleitor_leigo": "valid",
    "jornalista_politico": "sources",
    "pesquisador_academico": "no_truncation",
}


def _extract_prompts(text: str) -> List[str]:
    """Extrai TODOS os prompts típicos das linhas de citação após o cabeçalho
    canônico `## Template de Prompt Tipico`."""
    prompts: List[str] = []
    lines = text.splitlines()
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Template de Prompt Tipico"):
            in_section = True
            continue
        if in_section and stripped.startswith(">"):
            prompt = stripped.lstrip(">").strip().strip('"').strip()
            if prompt:
                prompts.append(prompt)
    return prompts


def load_personas(personas_dir: str = DEFAULT_PERSONAS_DIR) -> List[Dict]:
    """Lê todas as personas de `personas/*.md` e devolve slug + prompts."""
    personas: List[Dict] = []
    for filename in sorted(os.listdir(personas_dir)):
        if not filename.endswith(".md"):
            continue
        slug = filename[:-3]
        path = os.path.join(personas_dir, filename)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        personas.append({"slug": slug, "prompts": _extract_prompts(text)})
    return personas


def persona_expectation(slug: str) -> str:
    return EXPECTATION_BY_SLUG.get(slug, "valid")


class _FakeDoc:
    def __init__(self, metadata: Dict):
        self.metadata = metadata


def _build_mock_chain(expectation: str) -> MagicMock:
    """Cadeia RAG determinística por expectativa, sem rede externa."""
    chain = MagicMock()
    answer = (
        "Os gastos declarados constam na base de dados oficial de execução orçamentária."
        if expectation == "sources"
        else "Resposta completa cobrindo todos os pontos solicitados, sem qualquer corte."
    )
    chain.invoke.return_value = {
        "answer": answer,
        "source_documents": (
            [_FakeDoc({"source": "transparencia_cgu_gastos.json"})]
            if expectation == "sources"
            else []
        ),
    }
    return chain


def _evaluate_iteration(slug: str, expectation: str, status: int, body: Dict) -> List[str]:
    """Aplica o critério de aceitação da persona a UMA iteração. Devolve erros."""
    errors: List[str] = []
    answer = body.get("answer", "")
    sources = body.get("sources", [])

    if expectation == "blocked":
        if status != 400:
            errors.append(f"esperado 400 (guardrail), obtido {status}")
    elif expectation == "sources":
        if status != 200:
            errors.append(f"esperado 200, obtido {status}")
        if not sources:
            errors.append("resposta sem lista de fontes")
        elif not all(s.get("url") for s in sources):
            errors.append("fonte sem URL válida")
    elif expectation == "no_truncation":
        if status != 200:
            errors.append(f"esperado 200, obtido {status}")
        if "..." in answer:
            errors.append("resposta truncada com reticências")
    else:  # valid
        if status != 200:
            errors.append(f"esperado 200, obtido {status}")
        if not answer.strip():
            errors.append("resposta vazia")

    return errors


def run_persona(slug: str, personas_dir: str = DEFAULT_PERSONAS_DIR) -> Dict:
    """Executa TODAS as iterações da persona contra o endpoint de chat
    (E2E em processo), reutilizando a MESMA sessão (multi-turn)."""
    personas = {p["slug"]: p for p in load_personas(personas_dir)}
    if slug not in personas or not personas[slug]["prompts"]:
        return {
            "persona": slug,
            "expectation": "valid",
            "status": None,
            "ok": False,
            "errors": [f"persona sem prompts: {slug}"],
            "sources": [],
            "answer": "",
            "iterations": 0,
        }

    expectation = persona_expectation(slug)
    prompts = personas[slug]["prompts"]
    token = {"uid": f"qa-{slug}", "privileges": []}
    session_id = f"persona_test_{slug}"

    errors: List[str] = []
    statuses: List[int] = []
    all_sources: List[Dict] = []
    client = TestClient(app)

    for index, prompt in enumerate(prompts):
        filled = prompt.replace("[Nome]", "Deputado Federal")
        with patch("backend.api.auth.auth.verify_id_token", return_value=token), \
             patch("backend.api.main.ensure_initialized"), \
             patch("backend.api.main.get_rag_chain", return_value=_build_mock_chain(expectation)):
            response = client.post(
                "/api/v1/chat",
                json={"query": filled, "session_id": session_id},
                headers={"Authorization": "Bearer valid-token"},
            )
        try:
            body = response.json()
        except Exception:
            body = {}

        statuses.append(response.status_code)
        all_sources.extend(body.get("sources", []))
        for err in _evaluate_iteration(slug, expectation, response.status_code, body):
            errors.append(f"iteração {index + 1}: {err}")

    return {
        "persona": slug,
        "expectation": expectation,
        "status": statuses[-1],
        "ok": not errors,
        "errors": errors,
        "sources": all_sources,
        "answer": "",
        "iterations": len(prompts),
    }


def open_qa_issue(title: str, body: str, dry_run: bool = False):
    """Abre issue no GitHub para cada falha detectada se não for dry_run."""
    if dry_run:
        print(f"\n[DRY-RUN] Seria criada a Issue:\nTítulo: {title}\nConteúdo:\n{body}\n")
        return

    cmd = [
        "gh", "issue", "create",
        "--title", title,
        "--body", body,
        "--label", "qa-automation",
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"🚨 Issue de QA aberta no GitHub: '{title}'")
    except Exception as e:
        print(f"Erro ao abrir issue no GitHub: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Agente Testador de QA RAG-AI por persona")
    parser.add_argument("--persona", default=None, help="slug da persona a testar")
    parser.add_argument("--dry-run", action="store_true", help="apenas simula abertura de issues")
    args = parser.parse_args()

    slugs = [args.persona] if args.persona else sorted(EXPECTATION_BY_SLUG)
    print(f"🤖 Iniciando Agente Testador de QA RAG-AI (dry_run={args.dry_run})...\n")

    failures = []
    for slug in slugs:
        print(f"🧪 Testando Persona: [{slug}]")
        result = run_persona(slug)
        if result["ok"]:
            print(f"  ✅ Passou ({result['iterations']} iteração(ões), status {result['status']}).")
        else:
            print(f"  ❌ Falhou: {'; '.join(result['errors'])}")
            failures.append(result)

    if not failures:
        print("\n✨ Todos os testes de QA das personas passaram com sucesso!")
        sys.exit(0)

    print(f"\n⚠️ {len(failures)} persona(s) com falha. Processando abertura de issues...")
    for fail in failures:
        open_qa_issue(
            f"[QA Failure] Persona {fail['persona']} ({fail['expectation']})",
            (
                f"**Persona**: `{fail['persona']}`\n"
                f"**Expectativa**: `{fail['expectation']}`\n"
                f"**Iterações**: `{fail['iterations']}`\n"
                f"**Status HTTP**: `{fail['status']}`\n"
                f"**Erros**: {'; '.join(fail['errors'])}"
            ),
            dry_run=args.dry_run,
        )
    sys.exit(1)


if __name__ == "__main__":
    main()
