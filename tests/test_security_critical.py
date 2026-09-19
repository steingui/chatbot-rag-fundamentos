"""Testes de regressão para as oportunidades críticas do SECURITY_SCAN.

Cada bloco cobre um achado do relatório em docs_projeto/SECURITY_SCAN.md:
  - C-01: venv/ rastreado no Git
  - C-02: API Cloud Run pública sem autenticação
  - C-03: pipeline de prompts com push direto na main
  - C-04: métrica de confiança inócua do worker pool
"""
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from backend.api.main import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


# ---------------------------------------------------------------------------
# C-01 — Higiene de repositório: venv/ não pode ser rastreado pelo Git.
# ---------------------------------------------------------------------------
def test_gitignore_ignores_venv():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "venv/" in gitignore


def test_no_venv_file_tracked_by_git():
    res = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert res.returncode == 0, f"git ls-files falhou: {res.stderr}"
    tracked = res.stdout.splitlines()
    offenders = [p for p in tracked if p.startswith("venv/")]
    assert not offenders, (
        f"venv/ ainda está rastreado no Git ({len(offenders)} arquivos). "
        f"Execute: git rm -r --cached venv/"
    )


# ---------------------------------------------------------------------------
# C-02 — API Cloud Run pública sem autenticação.
# ---------------------------------------------------------------------------
def test_chat_endpoint_requires_authentication():
    """Sem Bearer token, o chat deve responder 401 (não 200 anônimo)."""
    response = client.post(
        "/api/v1/chat",
        json={"query": "Qual o limite orçamentário?", "session_id": "test_auth"},
    )
    assert response.status_code == 401


def test_chat_stream_endpoint_requires_authentication():
    """Sem Bearer token, o stream deve responder 401."""
    response = client.post(
        "/api/v1/chat/stream",
        json={"query": "Qual o limite orçamentário?", "session_id": "test_auth"},
    )
    assert response.status_code == 401


def test_chat_endpoint_accepts_valid_bearer_token():
    """Com token válido, o chat segue o fluxo normal (200)."""
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"answer": "Resposta de teste", "sources": []}
    token = {"uid": "user-123", "email": "ana@example.com", "privileges": []}
    with patch("backend.api.auth.auth.verify_id_token", return_value=token), \
         patch("backend.api.main.ensure_initialized"), \
         patch("backend.api.main.get_rag_chain", return_value=mock_chain):
        response = client.post(
            "/api/v1/chat",
            json={"query": "Qual o limite orçamentário?", "session_id": "test_auth"},
            headers={"Authorization": "Bearer valid-token"},
        )
    assert response.status_code == 200
    assert "answer" in response.json()


def test_cloudbuild_allows_unauthenticated_invocation():
    """Cloud Run precisa aceitar chamadas sem credencial IAM, pois o frontend
    autentica via Firebase Auth (ID token) — incompatível com o IAM do Cloud Run.
    A autenticação real é aplicada na camada de aplicação via get_required_user
    (coberta pelos testes de 401 acima)."""
    content = (ROOT / "cloudbuild.yaml").read_text(encoding="utf-8")
    assert "--allow-unauthenticated" in content, (
        "cloudbuild.yaml deve permitir invocação sem credencial IAM no Cloud Run; "
        "a autenticação Firebase é feita na aplicação (get_required_user)."
    )


def test_setup_gcp_allows_unauthenticated_invocation():
    content = (ROOT / "scripts" / "setup-gcp.sh").read_text(encoding="utf-8")
    assert "--allow-unauthenticated" in content, (
        "scripts/setup-gcp.sh deve permitir invocação sem credencial IAM no Cloud Run; "
        "a autenticação Firebase é feita na aplicação (get_required_user)."
    )


# ---------------------------------------------------------------------------
# C-03 — Pipeline de prompts não pode empurrar direto na main.
# ---------------------------------------------------------------------------
def test_prompts_workflow_does_not_push_to_main():
    content = (ROOT / ".github" / "workflows" / "generate_dynamic_prompts.yml").read_text(encoding="utf-8")
    assert "git push" not in content, (
        "generate_dynamic_prompts.yml ainda faz push direto no repositório. Use PR."
    )


def test_prompts_workflow_creates_pull_request():
    content = (ROOT / ".github" / "workflows" / "generate_dynamic_prompts.yml").read_text(encoding="utf-8")
    assert "create-pull-request" in content, (
        "generate_dynamic_prompts.yml deve abrir PR em vez de commitar direto na main."
    )
    assert "pull-requests: write" in content, (
        "generate_dynamic_prompts.yml precisa da permissão pull-requests: write."
    )


# ---------------------------------------------------------------------------
# C-04 — Métrica de confiança do worker pool deve refletir testes reais.
# ---------------------------------------------------------------------------
def test_confidence_score_without_tests_below_threshold():
    from scripts.agent_pool import calculate_confidence_score
    # sintaxe ok + diff, mas sem suíte de testes verde: abaixo de 85%
    assert calculate_confidence_score(True, False, True) < 85.0


def test_confidence_score_full_pass_reaches_threshold():
    from scripts.agent_pool import calculate_confidence_score
    assert calculate_confidence_score(True, True, True) >= 85.0


def test_confidence_score_no_checks_never_reaches_threshold():
    from scripts.agent_pool import calculate_confidence_score
    assert calculate_confidence_score(False, False, False) < 85.0


def test_worker_runs_tests_before_confidence():
    content = (ROOT / "scripts" / "agent_pool.py").read_text(encoding="utf-8")
    assert "pytest" in content, (
        "agent_pool.py deve executar a suíte de testes antes de calcular confiança."
    )
    assert "calculate_confidence_score(syntax_ok, tests_ok, diff_has_changes)" in content, (
        "agent_pool.py deve repassar o resultado dos testes à métrica de confiança."
    )
