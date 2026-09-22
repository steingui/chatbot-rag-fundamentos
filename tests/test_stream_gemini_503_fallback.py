"""RAG-112: stream sem tokens (ex.: Gemini 503 no streamGenerateContent) cai no fallback invoke.

Cenário real da issue #15: o `gemini-3.7-flash` respondeu `503 Service Unavailable`
no `streamGenerateContent` (stream abortou sem emitir token). Antes deste fix, o
stream terminava apenas com o aviso de instabilidade e o usuário ficava sem resposta.

Contrato:
- Se o `llm.stream()` não emitir NENHUM token, o chain tenta `llm.invoke()` como
  fallback (mesmo prompt) e emite a resposta completa como token.
- O fallback nunca duplica a mensagem de instabilidade quando consegue responder.
"""
from unittest.mock import MagicMock

import backend.rag.chat as chat
from backend.rag.semantic_router import Route


def _chain_with_stream(monkeypatch, stream_effect):
    class _FakeRouter:
        def route(self, query: str) -> Route:
            return Route.DIRECT

    monkeypatch.setattr(chat, "_router", _FakeRouter())
    monkeypatch.setattr(chat, "_needs_web_search", lambda q: False)

    llm = MagicMock()
    llm.stream = stream_effect
    return chat.MultiSourceAgentChain(llm, "sess")


def test_stream_sem_token_cai_no_fallback_invoke(monkeypatch):
    llm = MagicMock()
    llm.stream.return_value = iter([])  # stream vazio: 503 antes do 1º token
    llm.invoke.return_value = MagicMock(content="resposta via invoke")

    class _FakeRouter:
        def route(self, query: str) -> Route:
            return Route.DIRECT

    monkeypatch.setattr(chat, "_router", _FakeRouter())
    monkeypatch.setattr(chat, "_needs_web_search", lambda q: False)
    chain = chat.MultiSourceAgentChain(llm, "sess")

    tokens = [e["token"] for e in chain.stream({"question": "qual a PEC 45?"}) if e.get("type") == "token"]

    assert "resposta via invoke" in "".join(tokens)
    llm.invoke.assert_called_once()
    assert "Resposta interrompida" not in "".join(tokens)


def test_stream_que_emite_token_nao_chama_invoke(monkeypatch):
    llm = MagicMock()
    llm.stream.return_value = [MagicMock(content="tok")]
    llm.invoke.return_value = MagicMock(content="nao-deve-aparecer")

    class _FakeRouter:
        def route(self, query: str) -> Route:
            return Route.DIRECT

    monkeypatch.setattr(chat, "_router", _FakeRouter())
    monkeypatch.setattr(chat, "_needs_web_search", lambda q: False)
    chain = chat.MultiSourceAgentChain(llm, "sess")

    list(chain.stream({"question": "olá"}))

    llm.invoke.assert_not_called()


def test_stream_falha_apos_token_mantem_aviso_e_nao_invoca(monkeypatch):
    llm = MagicMock()

    def _boom(prompt):
        yield MagicMock(content="texto parcial...")
        raise RuntimeError("503 Service Unavailable")

    llm.stream = _boom
    llm.invoke.return_value = MagicMock(content="nao-deve-aparecer")

    class _FakeRouter:
        def route(self, query: str) -> Route:
            return Route.DIRECT

    monkeypatch.setattr(chat, "_router", _FakeRouter())
    monkeypatch.setattr(chat, "_needs_web_search", lambda q: False)
    chain = chat.MultiSourceAgentChain(llm, "sess")

    tokens = [e["token"] for e in chain.stream({"question": "fale mais"}) if e.get("type") == "token"]
    full = "".join(tokens)

    assert "texto parcial..." in full
    assert "Resposta interrompida" in full
    llm.invoke.assert_not_called()
