"""G2 — Anti-alucinação mecânica: ``jev_check`` + gate de answerability (R3).

Contrato:
- ``jev_check(claim, evidence, state)`` devolve o veredito canônico
  (``supported`` | ``contradicted`` | ``conflicted`` | ``insufficient`` |
  ``unknown``) ou ``None`` em falha (nunca lança).
- Gate pré-geração em ``MultiSourceAgentChain.invoke()``/``stream()``: base
  interna vazia ou evidência insuficiente/contraditória ⇒ responde
  "não encontrei" sem gastar síntese Gemini.
- Pós-geração (``invoke()``): resposta contradita pelas fontes é substituída.
- Fallback: Jev indisponível ⇒ comportamento atual (gera normalmente).
"""
from unittest.mock import MagicMock

import httpx
from langchain_core.documents import Document

import backend.rag.chat as chat
import backend.rag.jev_client as jev_client
from backend.rag.semantic_router import Route


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


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


def _check_payload(supports: float, contradicts: float, sufficient: float) -> dict:
    def noul(v: float) -> dict:
        return {"type": "noul", "noul": v}

    return {
        "answers": {
            "supports_claim": noul(supports),
            "contradicts_claim": noul(contradicts),
            "evidence_is_sufficient": noul(sufficient),
        }
    }


def _fresh_breaker(monkeypatch):
    breaker = jev_client._CircuitBreaker()
    monkeypatch.setattr(jev_client, "_breaker", breaker)
    return breaker


def _stub_check(monkeypatch, verdict):
    calls = []
    monkeypatch.setattr(chat, "jev_check", lambda **kw: calls.append(kw) or verdict)
    # G3: rerank por noul fica neutro (mantém os docs) para isolar o contrato G2.
    monkeypatch.setattr(chat, "jev_noul", lambda **kw: None)
    return calls


# --- jev_check (unidade) ---

def test_jev_check_verdict_supported(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)
    monkeypatch.setattr(
        jev_client.httpx, "post",
        lambda *a, **kw: FakeResponse(200, _check_payload(0.9, 0.1, 0.8)),
    )
    assert jev_client.jev_check("claim", "evidence") == "supported"


def test_jev_check_verdict_insufficient(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)
    monkeypatch.setattr(
        jev_client.httpx, "post",
        lambda *a, **kw: FakeResponse(200, _check_payload(0.9, 0.1, 0.1)),
    )
    assert jev_client.jev_check("claim", "evidence") == "insufficient"


def test_jev_check_verdict_contradicted(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)
    monkeypatch.setattr(
        jev_client.httpx, "post",
        lambda *a, **kw: FakeResponse(200, _check_payload(0.1, 0.9, 0.8)),
    )
    assert jev_client.jev_check("claim", "evidence") == "contradicted"


def test_jev_check_sem_chave_retorna_none(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert jev_client.jev_check("claim", "evidence") is None


# --- gate pré-geração (invoke) ---

def test_invoke_base_vazia_nao_chama_llm(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))
    monkeypatch.setattr(chat, "_retriever", _FakeRetriever([]))
    monkeypatch.setattr(chat, "_buscar_noticias_web", lambda q, sid="d": ("WEB", []))

    llm = MagicMock()
    chain = chat.MultiSourceAgentChain(llm, "sess")
    result = chain.invoke({"question": "Como votou o deputado X?"})

    assert result["answer"] == chat.NOT_FOUND_ANSWER
    llm.invoke.assert_not_called()


def test_invoke_evidencia_insuficiente_bloqueia(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))
    monkeypatch.setattr(
        chat, "_retriever",
        _FakeRetriever([Document(page_content="Votação da PEC", metadata={"source": "camara"})]),
    )
    monkeypatch.setattr(chat, "_buscar_noticias_web", lambda q, sid="d": ("WEB", []))
    _stub_check(monkeypatch, "insufficient")

    llm = MagicMock()
    chain = chat.MultiSourceAgentChain(llm, "sess")
    result = chain.invoke({"question": "Pergunta X"})

    assert result["answer"] == chat.NOT_FOUND_ANSWER
    llm.invoke.assert_not_called()


def test_invoke_evidencia_suficiente_gera(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))
    monkeypatch.setattr(
        chat, "_retriever",
        _FakeRetriever([Document(page_content="Votação da PEC", metadata={"source": "camara"})]),
    )
    monkeypatch.setattr(chat, "_buscar_noticias_web", lambda q, sid="d": ("WEB", []))
    _stub_check(monkeypatch, "supported")

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="resposta ok")
    chain = chat.MultiSourceAgentChain(llm, "sess")
    result = chain.invoke({"question": "Pergunta X"})

    assert result["answer"] == "resposta ok"


def test_invoke_jev_fora_nao_bloqueia(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))
    monkeypatch.setattr(
        chat, "_retriever",
        _FakeRetriever([Document(page_content="Votação da PEC", metadata={"source": "camara"})]),
    )
    monkeypatch.setattr(chat, "_buscar_noticias_web", lambda q, sid="d": ("WEB", []))
    _stub_check(monkeypatch, None)

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="resposta ok")
    chain = chat.MultiSourceAgentChain(llm, "sess")
    result = chain.invoke({"question": "Pergunta X"})

    assert result["answer"] == "resposta ok"


def test_invoke_pos_check_verifica_base_e_web_combinadas(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))
    monkeypatch.setattr(
        chat, "_retriever",
        _FakeRetriever([Document(page_content="Votação da PEC", metadata={"source": "camara"})]),
    )
    monkeypatch.setattr(chat, "_buscar_noticias_web", lambda q, sid="d": ("WEB_CTX", []))

    calls = []
    monkeypatch.setattr(chat, "jev_check", lambda **kw: calls.append(kw) or "supported")
    monkeypatch.setattr(chat, "jev_noul", lambda **kw: None)

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="resposta ok")
    chain = chat.MultiSourceAgentChain(llm, "sess")
    chain.invoke({"question": "Pergunta X"})

    # 1ª chamada = gate pré-geração (base); 2ª = pós-geração (base + web).
    post_evidence = calls[1]["evidence"]
    assert "Votação da PEC" in post_evidence
    assert "WEB_CTX" in post_evidence


def test_invoke_pos_check_contradito_substitui(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))
    monkeypatch.setattr(
        chat, "_retriever",
        _FakeRetriever([Document(page_content="Votação da PEC", metadata={"source": "camara"})]),
    )
    monkeypatch.setattr(chat, "_buscar_noticias_web", lambda q, sid="d": ("WEB", []))

    verdicts = iter(["supported", "contradicted"])
    monkeypatch.setattr(chat, "jev_check", lambda **kw: next(verdicts))
    monkeypatch.setattr(chat, "jev_noul", lambda **kw: None)

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="resposta inventada")
    chain = chat.MultiSourceAgentChain(llm, "sess")
    result = chain.invoke({"question": "Pergunta X"})

    assert result["answer"] == chat.NOT_FOUND_ANSWER


# --- gate pré-geração (stream) ---

def test_stream_base_vazia_emite_nao_encontrado(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))
    monkeypatch.setattr(chat, "_retriever", _FakeRetriever([]))
    monkeypatch.setattr(chat, "_buscar_noticias_web", lambda q, sid="d": ("WEB", []))

    llm = MagicMock()
    chain = chat.MultiSourceAgentChain(llm, "sess")
    events = list(chain.stream({"question": "Pergunta X"}))

    tokens = [e.get("token") for e in events if e.get("type") == "token"]
    assert tokens == [chat.NOT_FOUND_ANSWER]
    llm.stream.assert_not_called()
