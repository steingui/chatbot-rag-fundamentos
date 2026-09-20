"""G6 — Analytics reativado: ``record_query`` canoniza o tema da query com Jev.

Contrato:
- ``analytics._classify_query_theme(query)`` devolve o tema canônico (uma das
  chaves de ``_QUERY_THEMES``) quando o ``jev_choice`` decide com confiança
  ``>= JEV_MIN_CONFIDENCE``.
- Abaixo do guardrail de 90% ou falha do Jev (``None``) ⇒ ``"desconhecido"``.
- ``record_query(query)`` nunca lança (roda em ``background_tasks``) e loga um
  evento estruturado ``query_recorded`` com ``theme`` + ``query_hash`` (nunca o
  texto cru da query — regra de segurança do AGENTS.md).
"""
import logging

import backend.api.analytics as analytics


def test_classify_theme_confiante(monkeypatch):
    monkeypatch.setattr(analytics, "jev_choice", lambda *a, **kw: ("camara", 0.95))
    assert analytics._classify_query_theme("como o deputado votou") == "camara"


def test_classify_theme_abaixo_do_guardrail(monkeypatch):
    monkeypatch.setattr(analytics, "jev_choice", lambda *a, **kw: ("camara", 0.5))
    assert analytics._classify_query_theme("qualquer pergunta") == "desconhecido"


def test_classify_theme_jev_falha(monkeypatch):
    monkeypatch.setattr(analytics, "jev_choice", lambda *a, **kw: None)
    assert analytics._classify_query_theme("qualquer pergunta") == "desconhecido"


def test_classify_theme_rotulo_invalido(monkeypatch):
    monkeypatch.setattr(analytics, "jev_choice", lambda *a, **kw: ("nao_existe", 0.99))
    assert analytics._classify_query_theme("qualquer pergunta") == "desconhecido"


def test_record_query_nao_quebra_e_loga_estruturado(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    monkeypatch.setattr(analytics, "jev_choice", lambda *a, **kw: None)
    analytics.record_query("pergunta de teste com conteúdo sensível")
    assert any("query_recorded" in r.getMessage() for r in caplog.records)
    # Nunca loga o texto cru da query.
    assert not any("pergunta de teste" in r.getMessage() for r in caplog.records)
