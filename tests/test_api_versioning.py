from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def _api_paths():
    return {route.path for route in app.routes}


def test_routes_under_api_v1_prefix():
    paths = _api_paths()
    assert "/api/v1/chat" in paths
    assert "/api/v1/chat/stream" in paths
    assert "/api/v1/suggestions" in paths


def test_legacy_routes_removed():
    paths = _api_paths()
    assert "/chat" not in paths
    assert "/chat/stream" not in paths
    assert "/suggestions" not in paths


def test_healthcheck_stays_at_root():
    assert "/" in _api_paths()


def test_chat_v1_requires_authentication():
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"answer": "Resposta de teste", "sources": []}
    with patch("backend.api.main.ensure_initialized"), patch("backend.api.main.get_rag_chain", return_value=mock_chain):
        response = client.post("/api/v1/chat", json={"query": "Qual o limite orçamentário?", "session_id": "test_anon"})
        assert response.status_code == 401
