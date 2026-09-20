"""Invariantes do harness de contexto da LLM.

Garante que a codebase expõe à LLM apenas o contexto necessário e sem fatos
obsoletos, conforme o diagnóstico de otimização do harness:

- P0-1: fonte única de verdade (bootstrap enxuto na raiz).
- P0-2: sem referências obsoletas (`render.yaml`, endpoint/modelo hardcoded).
- P0-3: artefatos pesados fora da raiz.
- P0-4: `.llm/MANIFEST.md` como índice de carga sob demanda.
- P1-1: skills de provider reduzidas a stubs (sem duplicação de governança).
- P1-4: roteamento declarativo único via MANIFEST.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LLM_DIR = ROOT / ".llm"

# Artefatos de resultado/roadmap que não são contrato de trabalho.
HEAVY_ROOT_ARTIFACTS = {
    "BUSINESS_TEST_RESULTS.md",
    "ROADMAP_MOBILE.md",
    "TEST_RESULTS.md",
    "ROADMAP.md",
}

# Bootstrap mínimo permitido na raiz (restante vive em .llm/).
ALLOWED_ROOT_MD = {"AGENTS.md", "README.md", "CLAUDE.md"}

PROVIDER_SKILLS = [
    ROOT / ".agents/skills/chatbot-rag-fundamentos/SKILL.md",
    ROOT / ".claude/skills/chatbot-rag-fundamentos/SKILL.md",
]

LLM_DOCS = {
    "API_CONTRACT.md",
    "ARCHITECTURE.md",
    "BUSINESS_RULES.md",
    "COMPONENT_MAP.md",
    "CONVENTIONS.md",
    "DATA_MODEL.md",
    "DEPENDENCY_GRAPH.md",
    "DESIGN_SYSTEM.md",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _root_md_files() -> set[str]:
    return {p.name for p in ROOT.glob("*.md")}


def test_heavy_artifacts_not_in_root() -> None:
    for name in HEAVY_ROOT_ARTIFACTS:
        assert not (ROOT / name).exists(), (
            f"{name} está na raiz e polui o contexto da LLM. "
            f"Mova para docs_projeto/ ou backlog/."
        )


def test_root_md_are_only_bootstrap() -> None:
    unexpected = _root_md_files() - ALLOWED_ROOT_MD
    assert not unexpected, (
        f"Arquivos markdown fora do bootstrap mínimo na raiz: {sorted(unexpected)}. "
        f"Permitidos: {sorted(ALLOWED_ROOT_MD)}."
    )


def test_no_stale_render_reference() -> None:
    paths = (
        [ROOT / "AGENTS.md", ROOT / "README.md"]
        + list(LLM_DIR.glob("*.md"))
        + list((ROOT / ".agents").rglob("*.md"))
        + list((ROOT / ".claude").rglob("*.md"))
        + list((ROOT / "skills").glob("*.md"))
    )
    offenders = [str(p.relative_to(ROOT)) for p in paths if "render.yaml" in _read(p)]
    assert not offenders, (
        f"Referência obsoleta a 'render.yaml' (deploy real é cloudbuild.yaml): {offenders}"
    )


def test_e2e_skill_has_no_hardcoded_endpoint_or_model() -> None:
    skill = ROOT / "skills/e2e_test_skill.md"
    content = _read(skill)
    assert "run.app" not in content, (
        "skills/e2e_test_skill.md contém endpoint de produção hardcoded. "
        "Use variável de ambiente."
    )
    assert "gemini-1.5-flash" not in content, (
        "skills/e2e_test_skill.md contém modelo hardcoded. Use variável de ambiente."
    )


def test_manifest_exists_and_indexes_all_llm_docs() -> None:
    manifest = LLM_DIR / "MANIFEST.md"
    assert manifest.exists(), ".llm/MANIFEST.md não existe."
    content = _read(manifest)
    for doc in LLM_DOCS:
        assert doc in content, f".llm/MANIFEST.md não indexa {doc}."


def test_provider_skills_are_stubs() -> None:
    for skill in PROVIDER_SKILLS:
        assert skill.exists(), f"Skill de provider ausente: {skill}"
        content = _read(skill)
        lines = content.count("\n") + 1
        assert "AGENTS.md" in content, (
            f"{skill.relative_to(ROOT)} deve referenciar AGENTS.md como fonte única."
        )
        assert ".llm/MANIFEST.md" in content, (
            f"{skill.relative_to(ROOT)} deve rotear a carga via .llm/MANIFEST.md."
        )
        assert lines <= 20, (
            f"{skill.relative_to(ROOT)} tem {lines} linhas; deve ser um stub "
            f"(governança completa vive em AGENTS.md)."
        )


def test_agents_md_routes_via_manifest() -> None:
    content = _read(ROOT / "AGENTS.md")
    assert ".llm/MANIFEST.md" in content, (
        "AGENTS.md deve rotear a carga de documentação via .llm/MANIFEST.md."
    )


def test_validate_commits_has_semantic_drift_audit() -> None:
    """H1: o harness ganha uma camada de drift semântico doc ↔ código.

    O skill validate-commits deve auditar regras/contratos de `.llm/` com
    `jev_check`, interpretando `contradicted`/`insufficient`/`supported`.
    """
    skill = ROOT / ".roo/skills/validate-commits/SKILL.md"
    content = _read(skill).lower()
    for token in ("drift", "jev_check", "contradicted", "insufficient", "supported"):
        assert token in content, (
            f".roo/skills/validate-commits/SKILL.md não implementa a auditoria "
            f"de drift semântico H1 (token ausente: '{token}')."
        )


def test_provider_adapters_are_pointer_only() -> None:
    """Adapter de provider não pode duplicar governança.

    O contrato vive apenas em AGENTS.md; cada provider (Claude, Codex, Roo,
    DeepSeek, etc.) deve ter um arquivo ponteiro curto, sem regras copiadas.
    """
    adapters = [
        ROOT / "CLAUDE.md",
        ROOT / ".agents/skills/chatbot-rag-fundamentos/agents/openai.yaml",
    ]
    duplicated_governance = ("cloudbuild.yaml", "pytest", "sanitize", "guardrails")
    for adapter in adapters:
        assert adapter.exists(), f"Adapter de provider ausente: {adapter}"
        content = _read(adapter)
        assert "AGENTS.md" in content, (
            f"{adapter.relative_to(ROOT)} deve apontar para AGENTS.md."
        )
        for token in duplicated_governance:
            assert token not in content, (
                f"{adapter.relative_to(ROOT)} duplica governança ('{token}'). "
                f"Mantenha apenas o ponteiro para AGENTS.md."
            )
