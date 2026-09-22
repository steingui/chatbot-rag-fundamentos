"""RAG-113: Finding 1 da issue #16 — fallback quando o stream falha NO MEIO.

A 2ª pergunta (follow-up contextual) tinha a resposta truncada após ~10 tokens
com a mensagem genérica de instabilidade. O `gemini-3.7-flash` falhou no meio do
`streamGenerateContent`. Antes deste fix, qualquer erro no meio do stream virava
apenas o aviso "[Resposta interrompida...]".

Contrato:
- Stream que já emitiu tokens e falha no meio tenta `llm.invoke()` como
  continuação (o `_llm` usa `with_fallbacks`, então o fallback troca de modelo).
- O texto já emitido é descontado do início da resposta do invoke (sem
  duplicar tokens) e o restante é emitido como continuação.
- Só emite a mensagem de instabilidade quando o fallback também falha.
"""
from unittest.mock import MagicMock

import backend.rag.chat as chat
from backend.rag.semantic_router import Route


def _chain(monkeypatch, llm):
    monkeypatch.setattr(chat, "_retriever", None)
    monkeypatch.setattr(chat._router, "route", lambda q: Route.DIRECT)
    monkeypatch.setattr(chat, "_needs_web_search", lambda q: False)
    return chat.MultiSourceAgentChain(llm, "sess")


def test_stream_falha_no_meio_completa_via_invoke_sem_duplicar(monkeypatch):
    llm = MagicMock()

    def _boom(prompt):
        yield MagicMock(content="Deputados do PL")
        raise RuntimeError("503 Service Unavailable")

    llm.stream = _boom
    llm.invoke.return_value = MagicMock(content="Deputados do PL e do MDB são: ...")

    chain = _chain(monkeypatch, llm)
    events = list(chain.stream({"question": "quais nomes são do PL e do MDB?"}))
    full = "".join(e["token"] for e in events if e.get("type") == "token")

    llm.invoke.assert_called_once()
    # Continuação emitida sem duplicar o prefixo já transmitido.
    assert full.startswith("Deputados do PL")
    assert full.count("Deputados do PL") == 1
    assert " e do MDB são: ..." in full
    assert "Resposta interrompida" not in full


def test_stream_falha_no_meio_invoke_sem_prefixo_emite_resposta_inteira(monkeypatch):
    llm = MagicMock()

    def _boom(prompt):
        yield MagicMock(content="texto parcial...")
        raise RuntimeError("503 Service Unavailable")

    llm.stream = _boom
    # Modelo de fallback regenerou com redação diferente (prefixo não casa).
    llm.invoke.return_value = MagicMock(content="Resposta completa regenerada.")

    chain = _chain(monkeypatch, llm)
    full = "".join(
        e["token"] for e in chain.stream({"question": "fale mais"}) if e.get("type") == "token"
    )

    assert "Resposta completa regenerada." in full
    assert "Resposta interrompida" not in full


def test_stream_falha_no_meio_e_invoke_falha_emite_aviso(monkeypatch):
    llm = MagicMock()

    def _boom(prompt):
        yield MagicMock(content="texto parcial...")
        raise RuntimeError("503 Service Unavailable")

    llm.stream = _boom
    llm.invoke.side_effect = RuntimeError("fallback também falhou")

    chain = _chain(monkeypatch, llm)
    full = "".join(
        e["token"] for e in chain.stream({"question": "fale mais"}) if e.get("type") == "token"
    )

    assert "texto parcial..." in full
    assert "Resposta interrompida" in full
