"""G1 — Roteamento Jev apenas no default ambíguo.

Valida que o [`SemanticRouter.route()`](backend/rag/semantic_router.py) mantém o
regex soberano (custo zero) e só consulta o Jev quando nenhum padrão decide.
Contrato do guardrail de 90%:

- ``_jev_choice`` devolve ``(choice, confidence)``;
- confiança >= ``JEV_MIN_CONFIDENCE`` (0.9) → usa a escolha do Jev;
- confiança < 0.9 → delega a decisão às nossas LLMs (decider);
- Jev ou decider indisponíveis/indecisos → fallback ``Route.RAG``.
"""
import backend.rag.semantic_router as sr
from backend.rag.semantic_router import Route, SemanticRouter


def _stub_jev(monkeypatch, result):
    calls = []
    monkeypatch.setattr(sr, "_jev_choice", lambda **kw: calls.append(kw) or result)
    return calls


def _stub_decider(monkeypatch, result):
    calls = []
    monkeypatch.setattr(sr, "_llm_decide", lambda query: calls.append(query) or result)
    return calls


def test_regex_soberano_nao_chama_jev(monkeypatch):
    calls = _stub_jev(monkeypatch, ("DIRECT", 1.0))
    router = SemanticRouter()

    assert router.route("Como votou Alan Rick na PLP 192?") == Route.RAG
    assert router.route("Quais as notícias de hoje?") == Route.WEB
    assert router.route("Olá, tudo bem?") == Route.DIRECT

    assert calls == []


def test_ambiguo_direct_via_jev_confianca_alta(monkeypatch):
    _stub_jev(monkeypatch, ("DIRECT", 0.95))
    assert SemanticRouter().route("o que é inflação?") == Route.DIRECT


def test_ambiguo_web_via_jev_confianca_alta(monkeypatch):
    _stub_jev(monkeypatch, ("WEB", 0.9))
    assert SemanticRouter().route("o que é inflação?") == Route.WEB


def test_ambiguo_rag_via_jev_confianca_alta(monkeypatch):
    _stub_jev(monkeypatch, ("RAG", 1.0))
    assert SemanticRouter().route("o que é inflação?") == Route.RAG


def test_abaixo_de_90_porcento_usa_decider(monkeypatch):
    _stub_jev(monkeypatch, ("DIRECT", 0.5))
    decider_calls = _stub_decider(monkeypatch, Route.WEB)

    assert SemanticRouter().route("o que é inflação?") == Route.WEB
    assert decider_calls == ["o que é inflação?"]


def test_abaixo_de_90_porcento_decider_indeciso_fallback_rag(monkeypatch):
    _stub_jev(monkeypatch, ("DIRECT", 0.5))
    _stub_decider(monkeypatch, None)

    assert SemanticRouter().route("o que é inflação?") == Route.RAG


def test_abaixo_de_90_porcento_decider_quebra_fallback_rag(monkeypatch):
    _stub_jev(monkeypatch, ("DIRECT", 0.5))

    def _boom(_query):
        raise RuntimeError("decider down")

    monkeypatch.setattr(sr, "_llm_decide", _boom)

    assert SemanticRouter().route("o que é inflação?") == Route.RAG


def test_jev_falha_usa_decider(monkeypatch):
    _stub_jev(monkeypatch, None)
    _stub_decider(monkeypatch, Route.DIRECT)

    assert SemanticRouter().route("o que é inflação?") == Route.DIRECT


def test_jev_falha_e_decider_indisponivel_fallback_rag(monkeypatch):
    _stub_jev(monkeypatch, None)
    _stub_decider(monkeypatch, None)

    assert SemanticRouter().route("o que é inflação?") == Route.RAG


def test_jev_escolha_invalida_fallback_rag(monkeypatch):
    _stub_jev(monkeypatch, ("qualquer", 1.0))
    _stub_decider(monkeypatch, None)

    assert SemanticRouter().route("o que é inflação?") == Route.RAG
