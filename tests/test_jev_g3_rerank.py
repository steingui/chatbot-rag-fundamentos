"""G3 — Rerank com limiar de relevância (noul por documento).

Contrato:
- ``jev_client.jev_noul(instructions, state)`` devolve o ``noul`` calibrado
  (0..1) ou ``None`` em falha (nunca lança).
- ``chat._filter_relevant_docs(question, docs)`` mantém apenas documentos com
  ``noul >= RERANK_NOUL_THRESHOLD`` (default 0.5).
- Fallback: Jev indisponível (``None``) ⇒ documento é mantido (comportamento
  atual, o pipeline nunca quebra por indisponibilidade do Jev).
- ``MultiSourceAgentChain.invoke()`` filtra os docs rerankeados **antes** de
  montar o prompt de síntese, e ``source_documents`` reflete só os mantidos.
"""
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


def _noul_payload(value: float) -> dict:
    return {"answers": {"relevance": {"type": "noul", "noul": value}}}


def _fresh_breaker(monkeypatch):
    breaker = jev_client._CircuitBreaker()
    monkeypatch.setattr(jev_client, "_breaker", breaker)
    return breaker


class _FakeRouter:
    def __init__(self, route: Route):
        self._route = route

    def route(self, query: str) -> Route:
        return self._route


# --- jev_noul (unidade) ---

def test_jev_noul_devolve_noul(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)
    monkeypatch.setattr(
        jev_client.httpx, "post",
        lambda *a, **kw: FakeResponse(200, _noul_payload(0.87)),
    )
    assert jev_client.jev_noul("instrução", {"trecho": "x"}) == 0.87


def test_jev_noul_sem_chave_retorna_none(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert jev_client.jev_noul("instrução", {"trecho": "x"}) is None


# --- _filter_relevant_docs (unidade) ---

def _docs(*contents: str) -> list[Document]:
    return [Document(page_content=c, metadata={"source": "camara"}) for c in contents]


def test_filter_remove_doc_abaixo_do_limiar(monkeypatch):
    monkeypatch.setattr(
        chat, "jev_noul",
        lambda instructions, state: 0.9 if state["trecho"] == "relevante" else 0.1,
    )
    docs = _docs("relevante", "ruído")
    assert [d.page_content for d in chat._filter_relevant_docs("pergunta", docs)] == ["relevante"]


def test_filter_mantem_doc_no_limiar(monkeypatch):
    monkeypatch.setattr(chat, "jev_noul", lambda instructions, state: 0.5)
    docs = _docs("no limiar")
    assert len(chat._filter_relevant_docs("pergunta", docs)) == 1


def test_filter_mantem_doc_quando_jev_falha(monkeypatch):
    monkeypatch.setattr(chat, "jev_noul", lambda instructions, state: None)
    docs = _docs("a", "b")
    assert len(chat._filter_relevant_docs("pergunta", docs)) == 2


def test_filter_ignora_doc_vazio(monkeypatch):
    monkeypatch.setattr(chat, "jev_noul", lambda instructions, state: 0.9)
    docs = _docs("   ", "ok")
    assert [d.page_content for d in chat._filter_relevant_docs("pergunta", docs)] == ["ok"]


# --- integração: invoke filtra antes do prompt ---

def test_invoke_prompt_contem_apenas_docs_relevantes(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))

    class _Retriever:
        def invoke(self, query: str) -> list[Document]:
            return _docs("trecho-relevante-xyz", "trecho-ruido-xyz")

    monkeypatch.setattr(chat, "_retriever", _Retriever())
    monkeypatch.setattr(chat, "_buscar_noticias_web", lambda q, sid="d": ("", []))
    monkeypatch.setattr(
        chat, "jev_noul",
        lambda instructions, state: 0.9 if state.get("trecho") == "trecho-relevante-xyz" else 0.1,
    )
    # Gate de answerability: Jev julga a base (pós-filtro) suficiente.
    monkeypatch.setattr(chat, "jev_check", lambda **kw: "supported")

    from unittest.mock import MagicMock
    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="resposta ok")
    chain = chat.MultiSourceAgentChain(llm, "sess")
    result = chain.invoke({"question": "Pergunta X"})

    prompt = llm.invoke.call_args.args[0]
    assert "trecho-relevante-xyz" in prompt
    assert "trecho-ruido-xyz" not in prompt
    assert [d.page_content for d in result["source_documents"]] == ["trecho-relevante-xyz"]
