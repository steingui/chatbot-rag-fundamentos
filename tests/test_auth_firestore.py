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

def test_chat_endpoint_requires_authentication():
    response = client.post("/api/v1/chat", json={"query": "Qual o limite orçamentário?", "session_id": "test_anon"})
    assert response.status_code == 401

import asyncio
from backend.api.auth import get_optional_user, get_required_user

# --- SEC-502: middleware de validação id_token com injeção de privilégios ---

def test_optional_user_injects_uid_and_privileges():
    token = {
        "uid": "user-123",
        "email": "ana@example.com",
        "name": "Ana",
        "privileges": ["pro", "admin"],
    }
    with patch("backend.api.auth.auth.verify_id_token", return_value=token):
        user = asyncio.run(get_optional_user("Bearer valid-token"))
    assert user["uid"] == "user-123"
    assert user["email"] == "ana@example.com"
    assert user["privileges"] == ["pro", "admin"]

def test_optional_user_without_token_returns_none():
    assert asyncio.run(get_optional_user(None)) is None
    assert asyncio.run(get_optional_user("")) is None

def test_required_user_without_token_raises_401():
    with pytest.raises(Exception) as exc:
        asyncio.run(get_required_user(None))
    assert exc.value.status_code == 401

# --- SEC-503: Bearer Token substitui OriginCheckMiddleware ---

def test_chat_endpoint_rejects_untrusted_origin_without_token():
    response = client.post(
        "/api/v1/chat",
        json={"query": "Qual o limite orçamentário?", "session_id": "test_origin"},
        headers={"Origin": "https://evil.example.com"},
    )
    assert response.status_code == 401

def test_cors_preflight_allows_authorization_header():
    response = client.options(
        "/api/v1/chat",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert "authorization" in response.headers.get("access-control-allow-headers", "").lower()
