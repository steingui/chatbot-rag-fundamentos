"""RAG-108: Síntese hierárquica — isola contexto factual interno (primário) de web secundária."""
from unittest.mock import MagicMock

import backend.rag.chat as chat


def test_synthesis_prompt_isola_base_interna_como_fonte_primaria():
    prompt = chat._build_synthesis_prompt(
        pinecone_context="Votação da PEC 45 aprovada em 2023.",
        web_context="Notícia recente de 2024 sobre reforma tributária.",
        question="Como votou a PEC 45?",
    )

    # Contextos e pergunta presentes
    assert "Votação da PEC 45 aprovada em 2023." in prompt
    assert "Notícia recente de 2024 sobre reforma tributária." in prompt
    assert "Como votou a PEC 45?" in prompt

    # Hierarquia explícita: base interna = primária, web = secundária
    assert "FONTE PRIMÁRIA" in prompt
    assert "FONTE SECUNDÁRIA" in prompt

    # Base interna (factual) vem antes da web (hierarquia de confiança)
    assert prompt.index("Votação da PEC 45 aprovada em 2023.") < prompt.index(
        "Notícia recente de 2024 sobre reforma tributária."
    )

    # Regra anti-alucinação preservada
    assert "NUNCA invente" in prompt
    # Web não sobrescreve a base interna
    assert "prevaleça" in prompt


def test_invoke_e_stream_usam_prompt_hierarquico(monkeypatch):
    monkeypatch.setattr(chat, "_retriever", None)
    monkeypatch.setattr(
        chat, "_buscar_noticias_web", lambda q, sid="default": ("WEB_CTX", [])
    )

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="resposta")

    chain = chat.MultiSourceAgentChain(llm, "sess-1")

    result = chain.invoke({"question": "Pergunta X"})
    assert result["answer"] == "resposta"
    prompt_invoke = llm.invoke.call_args[0][0]
    assert "FONTE PRIMÁRIA" in prompt_invoke and "FONTE SECUNDÁRIA" in prompt_invoke
    assert "Pergunta X" in prompt_invoke

    llm.stream.return_value = [MagicMock(content="tok")]
    list(chain.stream({"question": "Pergunta Y"}))
    prompt_stream = llm.stream.call_args[0][0]
    assert "FONTE PRIMÁRIA" in prompt_stream and "FONTE SECUNDÁRIA" in prompt_stream
    assert "Pergunta Y" in prompt_stream
