"""RAG-109: Janela de contexto dinâmica por contagem EXATA de tokens (evita perda de histórico recente)."""
from unittest.mock import MagicMock

import backend.rag.chat as chat
from backend.rag.context_window import (
    build_context_window,
    count_tokens,
    format_history,
    max_input_tokens_for_model,
)


def test_count_tokens_exato():
    # Contagem exata via tokenizer real: vazio = 0 e cresce com o texto.
    assert count_tokens("") == 0
    pequeno = count_tokens("Olá")
    grande = count_tokens("Olá " * 200)
    assert grande > pequeno > 0


def test_build_context_window_preserva_historico_recente():
    history = [
        {"role": "user", "content": "ANTIGA " * 200},
        {"role": "assistant", "content": "ANTIGA2 " * 200},
        {"role": "user", "content": "pergunta recente"},
        {"role": "assistant", "content": "resposta recente"},
    ]
    janela = build_context_window(history, max_tokens=30)
    conteudos = [m["content"] for m in janela]

    # Histórico recente sobrevive à poda
    assert "resposta recente" in conteudos
    assert "pergunta recente" in conteudos
    # Mensagens antigas que estouram o orçamento são descartadas
    assert all("ANTIGA" not in c for c in conteudos)
    # Ordem cronológica preservada
    assert conteudos.index("pergunta recente") < conteudos.index("resposta recente")
    # Orçamento respeitado pela contagem exata
    assert sum(count_tokens(m["content"]) for m in janela) <= 30


def test_janela_descarta_mais_antiga_primeiro_sem_perder_recente():
    history = [
        {"role": "user", "content": "a" * 200},
        {"role": "user", "content": "recente curta"},
    ]
    janela = build_context_window(history, max_tokens=10)
    assert [m["content"] for m in janela] == ["recente curta"]


def test_build_context_window_sem_historico():
    assert build_context_window([], max_tokens=100) == []


def test_max_input_tokens_for_model_dinamico():
    # A janela é dinâmica: modelos diferentes → orçamentos diferentes.
    grande = max_input_tokens_for_model("gemini-3.7-flash")
    pequeno = max_input_tokens_for_model("modelo-desconhecido")
    assert grande > pequeno > 0


def test_format_history_renderiza_papeis():
    texto = format_history([
        {"role": "user", "content": "Oi"},
        {"role": "assistant", "content": "Olá"},
    ])
    assert "Oi" in texto and "Olá" in texto


def test_chain_injeta_historico_recente_no_prompt(monkeypatch):
    monkeypatch.setattr(chat, "_retriever", None)
    monkeypatch.setattr(chat, "_buscar_noticias_web", lambda q, sid="default": ("WEB", []))
    # Este teste valida a janela de histórico, não o gate G2 de answerability.
    monkeypatch.setattr(chat, "_answerable", lambda *a, **k: True)

    llm = MagicMock()
    llm.invoke.return_value = MagicMock(content="ok")

    chain = chat.MultiSourceAgentChain(llm, "sess-h", model_name="gemini-3.7-flash")
    history = [
        {"role": "user", "content": "ANTIGA " * 500},
        {"role": "assistant", "content": "resposta anterior recente"},
    ]
    chain.invoke({"question": "Nova?", "history": history})

    prompt = llm.invoke.call_args[0][0]
    assert "resposta anterior recente" in prompt
    assert "Nova?" in prompt
