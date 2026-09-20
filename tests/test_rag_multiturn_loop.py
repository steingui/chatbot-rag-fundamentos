"""RAG-LOOP: Ciclo automatizado de conversa fluida (multiturn >= 5 turnos).

Valida, de forma offline e determinística (mocks), que o pipeline
[`MultiSourceAgentChain`](backend/rag/chat.py) mantém coerência contextual,
recupera fontes em todos os turnos e injeta o histórico recente sem alucinação.

Cada turno é registrado com status (PASS/FAIL) e o relatório final é impresso.
"""
from unittest.mock import MagicMock

import pytest

import backend.rag.chat as chat
import backend.rag.semantic_router as semantic_router
from langchain_core.documents import Document


def _fake_retriever(query: str):
    return [Document(page_content=f"FATO_TURNO: {query}", metadata={"source": "votacao_192"})]


def _fake_web(query: str, session_id: str = "default"):
    return "WEB_CTX", [Document(page_content=f"web:{query}", metadata={"source": "https://example.com/x"})]


def _make_chain():
    llm = MagicMock()

    def _answer(prompt_text):
        # Resposta ancorada na pergunta presente no prompt (simula síntese fiel)
        question = prompt_text.split("--- PERGUNTA DO USUÁRIO: ---")[1].strip().splitlines()[0].strip()
        return MagicMock(content=f"Resposta ancorada para: {question}")

    llm.invoke.side_effect = _answer
    return chat.MultiSourceAgentChain(llm, "sess-loop", model_name="gemini-3.7-flash"), llm


def test_loop_multiturn_coerencia_e_fontes(monkeypatch):
    # Isola o gate Jev (G1): este teste é offline e determinístico; o roteador
    # continua exercitando o regex e o fallback ambiguo vira RAG (comportamento
    # atual), sem chamada de rede.
    monkeypatch.setattr(semantic_router, "_jev_choice", lambda **kw: ("RAG", 1.0))
    monkeypatch.setattr(chat, "_retriever", MagicMock(invoke=_fake_retriever))
    monkeypatch.setattr(chat, "_buscar_noticias_web", _fake_web)
    # Gate G2 (answerability) fora do escopo deste loop: mantém determinístico/offline.
    monkeypatch.setattr(chat, "jev_check", lambda **kw: "supported")
    # G3: rerank por noul fica neutro (mantém os docs) para isolar o loop de contexto.
    monkeypatch.setattr(chat, "jev_noul", lambda **kw: None)

    chain, llm = _make_chain()
    history = []
    report = []
    all_passed = True

    perguntas = [
        "Como votou Alan Rick na PLP 192?",
        "E qual foi o partido dele nessa votação?",
        "Repita o voto e confirme a data da sessão.",
        "Houve alguma divergência entre a base interna e a web?",
        "Resuma tudo que apuramos nesta conversa.",
    ]

    for i, pergunta in enumerate(perguntas, start=1):
        result = chain.invoke({"question": pergunta, "history": list(history)})

        prompt = llm.invoke.call_args_list[-1][0][0]
        answer = result["answer"]
        sources = result.get("source_documents", [])

        # 1. Fontes injetadas em todos os turnos (base interna + web)
        has_base = any(d.metadata.get("source", "").startswith("votacao") for d in sources)
        has_web = any(d.metadata.get("source", "").startswith("http") for d in sources)

        # 2. Coerência contextual: pergunta corrente e histórico recente no prompt
        has_question = pergunta in prompt
        has_history = f"--- HISTÓRICO RECENTE" in prompt if history else True

        # 3. Anti-alucinação: hierarquia de fontes e regra "NUNCA invente"
        has_hierarchy = "FONTE PRIMÁRIA" in prompt and "FONTE SECUNDÁRIA" in prompt
        has_antihalluc = "NUNCA invente" in prompt

        # 4. Resposta não-vazia e ancorada na pergunta
        has_answer = bool(answer) and pergunta in answer

        ok = all([has_base, has_web, has_question, has_history, has_hierarchy, has_antihalluc, has_answer])
        all_passed = all_passed and ok
        report.append(
            {
                "turno": i,
                "pergunta": pergunta,
                "fontes_base": has_base,
                "fonte_web": has_web,
                "coerencia_questao": has_question,
                "historico_injetado": has_history,
                "hierarquia_anti_alucinacao": has_hierarchy and has_antihalluc,
                "resposta_ancorada": has_answer,
                "status": "PASS" if ok else "FAIL",
            }
        )

        # Propaga o turno para o histórico da conversa
        history.append({"role": "user", "content": pergunta})
        history.append({"role": "assistant", "content": answer})

    print("\n=== RELATÓRIO RAG-LOOP (multiturn) ===")
    for r in report:
        print(
            f"[{r['status']}] Turno {r['turno']}: base={r['fontes_base']} "
            f"web={r['fonte_web']} questao={r['coerencia_questao']} "
            f"historico={r['historico_injetado']} anti_aluc={r['hierarquia_anti_alucinacao']} "
            f"ancorada={r['resposta_ancorada']} | {r['pergunta'][:40]}..."
        )
    print(f"Total de turnos: {len(report)} — {'TODOS PASS' if all_passed else 'HÁ FALHAS'}")

    # Garante no mínimo 5 turnos avaliados
    assert len(report) >= 5
    assert all_passed


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
