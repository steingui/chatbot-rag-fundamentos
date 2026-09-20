"""G4 — Gate de web search com ``noul`` (só aciona DDGS quando necessário).

Contrato:
- ``chat._needs_web_search(question)`` devolve ``True`` quando o Jev julga
  ``noul >= WEB_GATE_NOUL_THRESHOLD`` (pergunta exige informação recente/web) e
  ``False`` quando ``noul < limiar``.
- Fallback: Jev indisponível (``None``) ⇒ ``True`` (comportamento atual: web
  dispara sempre) — o pipeline nunca perde recência por indisponibilidade do Jev.
- ``MultiSourceAgentChain.invoke()``/``stream()`` só chamam
  ``_buscar_noticias_web`` quando ``_needs_web_search`` é ``True``.
"""
from unittest.mock import MagicMock

from langchain_core.documents import Document

import backend.rag.chat as chat
from backend.rag.semantic_router import Route


class _FakeRouter:
    def __init__(self, route: Route):
        self._route = route

    def route(self, query: str) -> Route:
        return self._route


class _FakeRetriever:
    def __init__(self, docs: list[Document]):
        self._docs = docs

    def invoke(self, query: str) -> list[Document]:
        return self._docs


# --- _needs_web_search (unidade) ---

def test_needs_web_quando_noul_alto(monkeypatch):
    monkeypatch.setattr(chat, "jev_noul", lambda instructions, state, routine=None: 0.9)
    assert chat._needs_web_search("últimas notícias da Câmara") is True


def test_needs_web_quando_noul_no_limiar(monkeypatch):
    monkeypatch.setattr(chat, "jev_noul", lambda instructions, state, routine=None: 0.5)
    assert chat._needs_web_search("notícias de hoje") is True


def test_pula_web_quando_noul_baixo(monkeypatch):
    monkeypatch.setattr(chat, "jev_noul", lambda instructions, state, routine=None: 0.1)
    assert chat._needs_web_search("como o deputado X votou na PEC Y") is False


def test_jev_falha_mantem_web(monkeypatch):
    monkeypatch.setattr(chat, "jev_noul", lambda instructions, state, routine=None: None)
    assert chat._needs_web_search("pergunta qualquer") is True


# --- integração: invoke não aciona DDGS quando o gate corta ---

def test_invoke_pula_web_quando_gate_corta(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))
    monkeypatch.setattr(
        chat, "_retriever",
        _FakeRetriever([Document(page_content="Votação da PEC", metadata={"source": "camara"})]),
    )
    monkeypatch.setattr(
        chat, "jev_noul",
        lambda instructions, state, routine=None: 0.9 if "trecho" in state else 0.1,
    )
    monkeypatch.setattr(chat, "jev_check", lambda **kw: "supported")

    web_calls: list[str] = []
    monkeypatch.setattr(
        chat, "_buscar_noticias_web",
        lambda q, sid="d": web_calls.append(q) or ("", []),
    )

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="resposta ok")
    result = chat.MultiSourceAgentChain(llm, "sess").invoke({"question": "Como votou o deputado X?"})

    assert web_calls == []
    assert result["answer"] == "resposta ok"


def test_invoke_chama_web_quando_gate_libera(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))
    monkeypatch.setattr(
        chat, "_retriever",
        _FakeRetriever([Document(page_content="Votação da PEC", metadata={"source": "camara"})]),
    )
    monkeypatch.setattr(
        chat, "jev_noul",
        lambda instructions, state, routine=None: 0.9 if "trecho" in state else 0.9,
    )
    monkeypatch.setattr(chat, "jev_check", lambda **kw: "supported")

    web_calls: list[str] = []
    monkeypatch.setattr(
        chat, "_buscar_noticias_web",
        lambda q, sid="d": web_calls.append(q) or ("WEB_CTX", []),
    )

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="resposta ok")
    chat.MultiSourceAgentChain(llm, "sess").invoke({"question": "Notícias de hoje"})

    assert web_calls == ["Notícias de hoje"]


def test_stream_pula_web_quando_gate_corta(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))
    monkeypatch.setattr(
        chat, "_retriever",
        _FakeRetriever([Document(page_content="Votação da PEC", metadata={"source": "camara"})]),
    )
    monkeypatch.setattr(chat, "jev_noul", lambda instructions, state, routine=None: 0.1)
    monkeypatch.setattr(chat, "jev_check", lambda **kw: "supported")

    web_calls: list[str] = []
    monkeypatch.setattr(
        chat, "_buscar_noticias_web",
        lambda q, sid="d": web_calls.append(q) or ("", []),
    )

    llm = MagicMock()
    llm.stream.return_value = iter([])
    chain = chat.MultiSourceAgentChain(llm, "sess")
    list(chain.stream({"question": "Como votou o deputado X?"}))

    assert web_calls == []
