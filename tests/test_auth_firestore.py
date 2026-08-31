import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.api.auth import get_optional_user

client = TestClient(app)

def test_optional_user_without_header():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_chat_endpoint_allows_anonymous():
    response = client.post("/chat", json={"query": "Qual o limite orçamentário?", "session_id": "test_anon"})
    # Retorna 200 com resposta ou cache
    assert response.status_code == 200
    assert "answer" in response.json()
