"""G8 — Follow-ups conversacionais ("fale mais") não devem cair em RAG/web.

Caso de uso real: após uma resposta, o usuário digita "fale mais". O roteador
não reconhecia o follow-up como conversa direta, caía no default ambíguo
(virava RAG) e disparava DDGS com a query "fale mais" — recuperando lixo
(wikipedia/instagram/facebook) e queimando latência/tokens.

Contrato:
- "fale mais", "continue", "explique melhor" e similares ⇒ ``Route.DIRECT``
  (resposta continua a partir do histórico da conversa, sem Pinecone nem web),
  decidido por regex (custo zero, sem chamada Jev).
- Follow-up que cita domínio legislativo continua ``Route.RAG`` (regex soberano).
- Em falha de streaming, a mensagem de erro é separada da resposta parcial
  (nunca concatenada no meio de uma palavra).
"""
from unittest.mock import MagicMock

import backend.rag.chat as chat
import backend.rag.semantic_router as sr
from backend.rag.semantic_router import Route, SemanticRouter


def test_fale_mais_e_direct_sem_jev(monkeypatch):
    calls = []
    monkeypatch.setattr(sr, "_jev_choice", lambda **kw: calls.append(kw) or None)
    router = SemanticRouter()

    assert router.route("fale mais") == Route.DIRECT
    assert router.route("pode falar mais") == Route.DIRECT
    assert router.route("continue") == Route.DIRECT
    assert router.route("explique melhor") == Route.DIRECT
    assert router.route("mais detalhes") == Route.DIRECT

    # Regex decide: nenhuma chamada Jev para follow-ups puros.
    assert calls == []


def test_followup_com_dominio_continua_rag(monkeypatch):
    calls = []
    monkeypatch.setattr(sr, "_jev_choice", lambda **kw: calls.append(kw) or None)
    router = SemanticRouter()

    assert router.route("fale mais sobre a PEC 192") == Route.RAG
    assert router.route("explique melhor a emenda") == Route.RAG
    assert calls == []


def test_stream_erro_separa_mensagem_de_erro(monkeypatch):
    class _FakeRouter:
        def route(self, query: str) -> Route:
            return Route.DIRECT

    monkeypatch.setattr(chat, "_router", _FakeRouter())

    llm = MagicMock()

    def _boom(prompt):
        yield MagicMock(content="texto parcial...")
        raise RuntimeError("boom")

    llm.stream = _boom
    chain = chat.MultiSourceAgentChain(llm, "sess")

    tokens = [e["token"] for e in chain.stream({"question": "fale mais"}) if e.get("type") == "token"]
    full = "".join(tokens)

    assert "texto parcial..." in full
    assert "Resposta interrompida" in full
    # O erro não pode colar no meio da palavra ("parcial...Resposta").
    assert "parcial...Resposta" not in full
    # A separação garante quebra de linha entre o parcial e o aviso.
    assert "parcial...\n\n" in full
