"""RAG-111: Finding 1 da issue #14 — paraleliza Pinecone e DDGS no stream.

A 1ª resposta do chat levava ~58s porque a recuperação híbrida (Pinecone) e a
busca web (DDGS) rodavam em série. Este teste prova que a web começa ENQUANTO o
Pinecone ainda executa (sobreposição de I/O), e não depois.
"""
import threading
from unittest.mock import MagicMock

import backend.rag.chat as chat


def test_stream_paraleliza_pinecone_e_web(monkeypatch):
    retrieval_started = threading.Event()
    retrieval_done = threading.Event()
    web_overlapped_retrieval = threading.Event()

    def fake_retrieve(query):
        retrieval_started.set()
        # Só destrava quando a web já tiver começado (prova de sobreposição).
        web_overlapped_retrieval.wait(timeout=2)
        retrieval_done.set()
        return []

    def fake_web(query, sid="default"):
        if retrieval_started.is_set() and not retrieval_done.is_set():
            web_overlapped_retrieval.set()
        return ("", [])

    retriever = MagicMock()
    retriever.invoke.side_effect = fake_retrieve
    monkeypatch.setattr(chat, "_retriever", retriever)
    monkeypatch.setattr(chat, "_buscar_noticias_web", fake_web)
    monkeypatch.setattr(chat._router, "route", lambda q: chat.Route.RAG)
    monkeypatch.setattr(chat, "_needs_web_search", lambda q: True)

    llm = MagicMock()
    llm.stream.return_value = [MagicMock(content="tok")]
    chain = chat.MultiSourceAgentChain(llm, "sess-1")

    list(chain.stream({"question": "Como votaram os senadores na PEC 45?"}))

    assert web_overlapped_retrieval.is_set(), (
        "a busca web deveria iniciar enquanto o Pinecone ainda executa "
        "(paralelismo), não após o término da recuperação"
    )
