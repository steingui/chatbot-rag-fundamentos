"""RAG-114: Finding 2 da issue #16 — instrumentação de latência do stream SSE.

O follow-up levou ~21 s do request ao fim do stream. Para isolar geração vs.
recuperação, o `stream()` deve logar (JSON estruturado) as métricas:
``retrieval_ms`` (busca), ``ttfb_ms`` (1º token) e ``total_ms`` (stream inteiro).

Contrato:
- Ao final do stream, um log com ``chat_stream_latency`` é emitido contendo
  ``retrieval_ms``, ``ttfb_ms`` e ``total_ms``.
"""
from unittest.mock import MagicMock

import backend.rag.chat as chat
from backend.rag.semantic_router import Route


def test_stream_loga_metricas_de_latencia(monkeypatch, caplog):
    monkeypatch.setattr(chat, "_retriever", None)
    monkeypatch.setattr(chat._router, "route", lambda q: Route.DIRECT)
    monkeypatch.setattr(chat, "_needs_web_search", lambda q: False)

    llm = MagicMock()
    llm.stream.return_value = [MagicMock(content="tok")]

    chain = chat.MultiSourceAgentChain(llm, "sess")
    with caplog.at_level("INFO", logger="backend.rag.chat"):
        list(chain.stream({"question": "Olá"}))

    latency_logs = [r.message for r in caplog.records if "chat_stream_latency" in r.getMessage()]
    assert latency_logs, "esperado log de chat_stream_latency"
    assert "ttfb_ms=" in latency_logs[0]
    assert "retrieval_ms=" in latency_logs[0]
    assert "total_ms=" in latency_logs[0]
