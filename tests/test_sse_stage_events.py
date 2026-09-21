"""RAG-110: SSE emite eventos de progresso por etapa (retrieving → generating → done).

Finding 2 da issue #13: expor no stream eventos que distinguem a etapa de
busca (retrieval) da etapa de geração, dando feedback granular ao usuário.
"""
from unittest.mock import MagicMock

import backend.rag.chat as chat


def _chain(monkeypatch):
    monkeypatch.setattr(chat, "_retriever", None)
    monkeypatch.setattr(chat._router, "route", lambda q: chat.Route.DIRECT)
    monkeypatch.setattr(chat, "_needs_web_search", lambda q: False)
    llm = MagicMock()
    llm.stream.return_value = [MagicMock(content="tok")]
    return chat.MultiSourceAgentChain(llm, "sess-1")


def test_stream_emite_etapas_retrieving_generating_done(monkeypatch):
    events = list(_chain(monkeypatch).stream({"question": "Olá"}))

    stages = [e.get("stage") for e in events if e.get("type") == "stage"]
    assert stages == ["retrieving", "generating", "done"]


def test_stream_emite_token_apos_etapa_generating(monkeypatch):
    events = list(_chain(monkeypatch).stream({"question": "Olá"}))

    generating_idx = next(
        i for i, e in enumerate(events) if e.get("type") == "stage" and e.get("stage") == "generating"
    )
    token_idx = next(
        i for i, e in enumerate(events) if e.get("type") == "token"
    )
    assert generating_idx < token_idx
    assert events[token_idx]["token"] == "tok"
