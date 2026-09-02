import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.api.auth import get_optional_user

client = TestClient(app)

def test_optional_user_without_header():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

from unittest.mock import patch, MagicMock

def test_chat_endpoint_allows_anonymous():
    mock_chain = MagicMock()
    mock_chain.invoke.return_value = {"answer": "Resposta de teste", "sources": []}
    with patch("backend.api.main.get_rag_chain", return_value=mock_chain):
        response = client.post("/chat", json={"query": "Qual o limite orçamentário?", "session_id": "test_anon"})
        assert response.status_code == 200
        assert "answer" in response.json()
