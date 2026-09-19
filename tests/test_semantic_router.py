"""RAG-101: Roteamento semântico — classifica a intenção do usuário antes de acionar ferramentas.

Valida, de forma offline e determinística, que o
[`SemanticRouter`](backend/rag/semantic_router.py) encaminha a consulta para a
rota correta (RAG vs Web vs Direct LLM) e que o
[`MultiSourceAgentChain`](backend/rag/chat.py) aciona apenas as ferramentas
pertinentes a cada rota.
"""
from unittest.mock import MagicMock

import backend.rag.chat as chat
from backend.rag.semantic_router import Route, SemanticRouter


def test_router_classifica_rag_para_dominio_legislativo():
    router = SemanticRouter()
    assert router.route("Como votou Alan Rick na PLP 192?") == Route.RAG
    assert router.route("Quais leis tratam do orçamento da saúde?") == Route.RAG
    assert router.route("Declaração de bens do candidato no TSE") == Route.RAG


def test_router_classifica_web_para_recencia_e_noticias():
    router = SemanticRouter()
    assert router.route("Quais as notícias de hoje sobre o congresso?") == Route.WEB
    assert router.route("O que aconteceu recentemente na política?") == Route.WEB


def test_router_classifica_direct_para_saudacoes_e_identidade():
    router = SemanticRouter()
    assert router.route("Olá, tudo bem?") == Route.DIRECT
    assert router.route("Quem é você?") == Route.DIRECT
    assert router.route("Obrigado!") == Route.DIRECT


def test_router_direct_nao_engole_dominio_legislativo():
    router = SemanticRouter()
    assert router.route("Olá, como votou o deputado na PLP?") == Route.RAG


def test_chain_route_rag_usa_retriever_e_web(monkeypatch):
    retriever = MagicMock()
    retriever.invoke.return_value = []
    monkeypatch.setattr(chat, "_retriever", retriever)

    web_calls = []
    monkeypatch.setattr(
        chat,
        "_buscar_noticias_web",
        lambda q, sid="default": web_calls.append(q) or ("WEB", []),
    )

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="resposta")
    chain = chat.MultiSourceAgentChain(llm, "sess")

    chain.invoke({"question": "Como votou Alan Rick na PLP 192?"})

    assert retriever.invoke.called
    assert web_calls


def test_chain_route_web_nao_usa_retriever(monkeypatch):
    retriever = MagicMock()
    monkeypatch.setattr(chat, "_retriever", retriever)
    monkeypatch.setattr(
        chat, "_buscar_noticias_web", lambda q, sid="default": ("WEB_CTX", [])
    )

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="resposta")
    chain = chat.MultiSourceAgentChain(llm, "sess")

    chain.invoke({"question": "Quais as notícias de hoje?"})

    assert not retriever.invoke.called
    prompt = llm.invoke.call_args[0][0]
    assert "FONTE SECUNDÁRIA" in prompt


def test_chain_route_direct_sem_ferramentas(monkeypatch):
    retriever = MagicMock()
    monkeypatch.setattr(chat, "_retriever", retriever)

    web = MagicMock(return_value=("WEB", []))
    monkeypatch.setattr(chat, "_buscar_noticias_web", web)

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="Olá! Como posso ajudar?")
    chain = chat.MultiSourceAgentChain(llm, "sess")

    result = chain.invoke({"question": "Olá, tudo bem?"})

    assert not retriever.invoke.called
    assert not web.called
    assert result["source_documents"] == []
    assert result["answer"] == "Olá! Como posso ajudar?"
