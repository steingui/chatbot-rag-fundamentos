"""G7 — Dedup semântico de cache com ``jev_noul``.

Contrato:
- Hit por chave exata continua custo zero (nenhuma chamada Jev).
- Em miss exato, ``RAGQueryCache.get`` varre as chaves recentes do **mesmo
  modelo** e reusa a resposta quando o ``jev_noul`` julga equivalência
  semântica ``>= SEMANTIC_DEDUP_THRESHOLD``.
- Jev indisponível (``None``) ou abaixo do limiar ⇒ miss (comportamento atual).
- O dedup nunca cruza modelos diferentes (chave = ``{model}:{query}``).
"""
import backend.rag.cache as cache_mod
from backend.rag.cache import RAGQueryCache


def test_get_hit_exato_nao_chama_jev(monkeypatch):
    calls = []
    monkeypatch.setattr(cache_mod, "jev_noul", lambda *a, **kw: calls.append(1) or 1.0)
    c = RAGQueryCache(ttl_seconds=300, max_size=10)
    c.set("Como votou o deputado?", {"answer": "x"}, model_name="m")
    assert c.get("como votou o deputado?", model_name="m")["answer"] == "x"
    assert calls == []


def test_get_hit_semantico(monkeypatch):
    monkeypatch.setattr(cache_mod, "jev_noul", lambda instructions, state, routine=None: 1.0)
    c = RAGQueryCache(ttl_seconds=300, max_size=10)
    c.set("voto do deputado X na PEC Y", {"answer": "A"}, model_name="m")
    assert c.get("como o deputado X votou na PEC Y", model_name="m")["answer"] == "A"


def test_get_semantico_abaixo_do_limiar(monkeypatch):
    monkeypatch.setattr(cache_mod, "jev_noul", lambda instructions, state, routine=None: 0.1)
    c = RAGQueryCache(ttl_seconds=300, max_size=10)
    c.set("voto do deputado X na PEC Y", {"answer": "A"}, model_name="m")
    assert c.get("como o deputado X votou na PEC Y", model_name="m") is None


def test_get_semantico_jev_falha(monkeypatch):
    monkeypatch.setattr(cache_mod, "jev_noul", lambda instructions, state, routine=None: None)
    c = RAGQueryCache(ttl_seconds=300, max_size=10)
    c.set("voto do deputado X", {"answer": "A"}, model_name="m")
    assert c.get("outra pergunta", model_name="m") is None


def test_semantico_respeita_modelo(monkeypatch):
    monkeypatch.setattr(cache_mod, "jev_noul", lambda instructions, state, routine=None: 1.0)
    c = RAGQueryCache(ttl_seconds=300, max_size=10)
    c.set("voto do deputado X", {"answer": "A"}, model_name="gemini")
    assert c.get("como votou o deputado X", model_name="llama") is None
