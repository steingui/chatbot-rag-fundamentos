"""E2E de integração contra o ambiente produtivo (Cloud Run).

Valida, de forma assertiva e com apontamento real para produção, a integridade
E2E do pipeline após os commits: healthcheck, roteamento semântico
(RAG/WEB/DIRECT), contrato de fontes, sugestões e streaming SSE.

Execução opt-in — NÃO roda no CI/pytest por padrão (evita chamadas externas):

    RUN_E2E_PROD=1 .venv/bin/python -m pytest tests/test_e2e_production.py -v

Variáveis de ambiente:
- ``RUN_E2E_PROD``: define como ``1`` para habilitar a execução real.
- ``E2E_PROD_API_URL``: URL base da API em produção (default Cloud Run).
"""
import os

import pytest
import requests

API_URL = os.environ.get(
    "E2E_PROD_API_URL",
    "https://chatbot-rag-api-1043919586992.southamerica-east1.run.app",
).rstrip("/")

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_E2E_PROD") != "1",
    reason="E2E de produção desativado por padrão. Defina RUN_E2E_PROD=1 para executar.",
)

TIMEOUT = 60
MODEL = "gemini-3.7-flash"


def _post_chat(query: str) -> requests.Response:
    """POST /api/v1/chat com sessão isolada por processo (evita colisão de cache)."""
    return requests.post(
        f"{API_URL}/api/v1/chat",
        json={"session_id": f"e2e_prod_{os.getpid()}", "query": query, "model": MODEL},
        timeout=TIMEOUT,
    )


def test_healthcheck_prod():
    """GET / deve responder 200 com status ok (liveness do Cloud Run)."""
    res = requests.get(f"{API_URL}/", timeout=TIMEOUT)
    assert res.status_code == 200, res.text
    assert res.json().get("status") == "ok"


def test_chat_rota_rag_retorna_resposta_e_fontes():
    """Rota RAG (domínio legislativo): deve acionar retriever + web e devolver answer + sources."""
    res = _post_chat("Como votou Alan Rick na PLP 192?")
    assert res.status_code == 200, res.text
    body = res.json()
    assert isinstance(body.get("answer"), str) and body["answer"].strip()
    assert isinstance(body.get("sources"), list)


def test_chat_rota_web_retorna_resposta():
    """Rota WEB (intenção de recência): deve devolver resposta ancorada em fonte web."""
    res = _post_chat("Quais as notícias de hoje sobre o congresso?")
    assert res.status_code == 200, res.text
    assert res.json()["answer"].strip()


def test_chat_rota_direct_sem_fontes():
    """Rota DIRECT (saudação/identidade): LLM direto, sources obrigatoriamente vazias."""
    res = _post_chat("Olá, tudo bem?")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["answer"].strip()
    assert body.get("sources") == []


def test_suggestions_prod():
    """GET /api/v1/suggestions deve devolver lista de sugestões."""
    res = requests.get(f"{API_URL}/api/v1/suggestions", timeout=TIMEOUT)
    assert res.status_code == 200, res.text
    assert isinstance(res.json().get("suggestions"), list)


def test_chat_stream_prod_emite_sse():
    """POST /api/v1/chat/stream deve emitir evento sources, tokens e [DONE]."""
    res = requests.post(
        f"{API_URL}/api/v1/chat/stream",
        json={"session_id": f"e2e_prod_{os.getpid()}", "query": "Olá", "model": MODEL},
        timeout=TIMEOUT,
        stream=True,
    )
    assert res.status_code == 200, res.text
    raw = "".join(
        chunk.decode("utf-8", errors="replace")
        for chunk in res.iter_content(chunk_size=1024)
    )
    assert '"type": "sources"' in raw
    assert "data: [DONE]" in raw
