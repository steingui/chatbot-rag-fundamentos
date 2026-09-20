"""G5 — Conflito interno vs web verificado mecanicamente (``jev_check``).

Contrato:
- ``chat._web_conflicts_with_base(pinecone_context, web_context, question)``
  devolve ``True`` somente quando ambas as fontes existem e o Jev julga
  ``supported`` a afirmação "a fonte web contradiz a base interna".
- Fallback: Jev indisponível (``None``) ⇒ ``False`` (resolução por instrução no
  prompt, comportamento atual). Fonte ausente ⇒ ``False``.
- ``_build_synthesis_prompt(..., web_conflict=True)`` injeta flag explícita
  para priorizar a base interna e citar a divergência.
- ``MultiSourceAgentChain.invoke()`` passa ``web_conflict`` para o prompt.
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


# --- _web_conflicts_with_base (unidade) ---

def test_conflict_quando_web_contradiz_base(monkeypatch):
    monkeypatch.setattr(chat, "jev_check", lambda **kw: "supported")
    assert chat._web_conflicts_with_base("BASE", "WEB", "pergunta") is True


def test_conflict_sem_base(monkeypatch):
    monkeypatch.setattr(chat, "jev_check", lambda **kw: "supported")
    assert chat._web_conflicts_with_base("", "WEB", "pergunta") is False


def test_conflict_sem_web(monkeypatch):
    monkeypatch.setattr(chat, "jev_check", lambda **kw: "supported")
    assert chat._web_conflicts_with_base("BASE", "", "pergunta") is False


def test_conflict_base_vazia_placeholder(monkeypatch):
    monkeypatch.setattr(chat, "jev_check", lambda **kw: "supported")
    assert chat._web_conflicts_with_base("Nenhum documento encontrado na base interna.", "WEB", "pergunta") is False


def test_conflict_verdict_nao_supported(monkeypatch):
    monkeypatch.setattr(chat, "jev_check", lambda **kw: "insufficient")
    assert chat._web_conflicts_with_base("BASE", "WEB", "pergunta") is False


def test_conflict_jev_falha_retorna_false(monkeypatch):
    monkeypatch.setattr(chat, "jev_check", lambda **kw: None)
    assert chat._web_conflicts_with_base("BASE", "WEB", "pergunta") is False


# --- flag no prompt ---

def test_prompt_com_flag_de_conflito():
    prompt = chat._build_synthesis_prompt("BASE", "WEB", "pergunta", "", web_conflict=True)
    assert "CONFLITO" in prompt
    assert "PRIORIZE" in prompt


def test_prompt_sem_flag_sem_conflito():
    prompt = chat._build_synthesis_prompt("BASE", "WEB", "pergunta")
    assert "CONFLITO" not in prompt


# --- integração: invoke injeta flag no prompt ---

def _stub_checks(monkeypatch):
    """Jev estubado: G3/G4 liberam; G2 answerable e G5 conflito = supported."""
    monkeypatch.setattr(
        chat, "jev_noul",
        lambda instructions, state: 0.9 if "trecho" in state else 0.9,
    )

    def jev_check(claim, evidence, state=None):
        return "supported"

    monkeypatch.setattr(chat, "jev_check", jev_check)


def test_invoke_injeta_flag_quando_conflito(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))
    monkeypatch.setattr(
        chat, "_retriever",
        _FakeRetriever([Document(page_content="Votação da PEC", metadata={"source": "camara"})]),
    )
    monkeypatch.setattr(chat, "_buscar_noticias_web", lambda q, sid="d": ("WEB_CTX", []))
    _stub_checks(monkeypatch)

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="resposta ok")
    chat.MultiSourceAgentChain(llm, "sess").invoke({"question": "Pergunta X"})

    prompt = llm.invoke.call_args.args[0]
    assert "CONFLITO" in prompt
    assert "PRIORIZE" in prompt


def test_invoke_nao_injeta_flag_sem_conflito(monkeypatch):
    monkeypatch.setattr(chat, "_router", _FakeRouter(Route.RAG))
    monkeypatch.setattr(
        chat, "_retriever",
        _FakeRetriever([Document(page_content="Votação da PEC", metadata={"source": "camara"})]),
    )
    monkeypatch.setattr(chat, "_buscar_noticias_web", lambda q, sid="d": ("WEB_CTX", []))
    _stub_checks(monkeypatch)
    monkeypatch.setattr(chat, "_web_conflicts_with_base", lambda a, b, q: False)

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="resposta ok")
    chat.MultiSourceAgentChain(llm, "sess").invoke({"question": "Pergunta X"})

    prompt = llm.invoke.call_args.args[0]
    assert "CONFLITO" not in prompt
