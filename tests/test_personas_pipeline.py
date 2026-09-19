"""Testes do ciclo de QA por personas (SDD).

Garante que o `scripts/agent_rag_tester.py`:
  - lê as personas de `personas/*.md` (sem suítes hardcoded);
  - mapeia cada slug para a expectativa correta;
  - exercita o endpoint `POST /api/v1/chat` de ponta a ponta
    (rota → guardrails → cadeia RAG);
  - e que o workflow executa 1 job por persona.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PERSONA_SLUGS = [
    "qa_adversarial",
    "eleitor_leigo",
    "jornalista_politico",
    "pesquisador_academico",
]


def test_personas_directory_has_four_personas():
    from scripts.agent_rag_tester import load_personas

    personas = load_personas(str(ROOT / "personas"))
    slugs = {p["slug"] for p in personas}
    assert slugs == set(PERSONA_SLUGS)


def test_load_personas_extracts_prompt_from_markdown():
    from scripts.agent_rag_tester import load_personas

    personas = {p["slug"]: p for p in load_personas(str(ROOT / "personas"))}
    for slug in PERSONA_SLUGS:
        assert personas[slug]["prompt"].strip(), f"prompt vazio para {slug}"


def test_persona_expectation_mapping():
    from scripts.agent_rag_tester import persona_expectation

    expected = {
        "qa_adversarial": "blocked",
        "eleitor_leigo": "valid",
        "jornalista_politico": "sources",
        "pesquisador_academico": "no_truncation",
    }
    for slug, expectation in expected.items():
        assert persona_expectation(slug) == expectation


def test_adversarial_persona_blocked_via_endpoint():
    from scripts.agent_rag_tester import run_persona

    result = run_persona("qa_adversarial")
    assert result["ok"] is True
    assert result["status"] == 400


def test_jornalista_persona_returns_sources_via_endpoint():
    from scripts.agent_rag_tester import run_persona

    result = run_persona("jornalista_politico")
    assert result["ok"] is True
    assert result["status"] == 200
    assert result["sources"]


def test_workflow_has_one_job_per_persona():
    content = (
        ROOT / ".github" / "workflows" / "autonomous_qa_pipeline.yml"
    ).read_text(encoding="utf-8")
    assert "matrix" in content, "workflow deve usar strategy.matrix"
    for slug in PERSONA_SLUGS:
        assert slug in content, f"workflow não cobre a persona {slug}"
