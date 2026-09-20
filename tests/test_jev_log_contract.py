"""Contrato de log estruturado ``event="jev_call"`` (docs/JEV_ALERTING.md §1).

Valida o contrato de observabilidade de toda chamada Jev:

- um único log JSON por chamada com ``event="jev_call"``;
- ``routine`` correto por rotina (não mais hardcoded em ``r1_semantic_route``);
- severidade do log por ``status`` conforme a tabela do contrato:

  | status            | nível   |
  |-------------------|---------|
  | ok                | INFO    |
  | low_confidence    | INFO    |
  | rate_limited      | WARNING |
  | no_credits        | ERROR   |
  | error             | ERROR   |
  | timeout           | ERROR   |
  | circuit breaker   | WARNING |
"""
import json
import logging
import time

import httpx

import backend.rag.jev_client as jev_client


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


CHOICE_PAYLOAD = {
    "answers": {
        "route": {"type": "choice", "choice": "DIRECT", "confidence": 0.9, "probabilities": {}}
    }
}

NOUL_PAYLOAD = {
    "answers": {"relevance": {"type": "noul", "noul": 0.87}}
}


def _check_payload(supports: float, contradicts: float, sufficient: float) -> dict:
    def noul(v: float) -> dict:
        return {"type": "noul", "noul": v}

    return {
        "answers": {
            "supports_claim": noul(supports),
            "contradicts_claim": noul(contradicts),
            "evidence_is_sufficient": noul(sufficient),
        }
    }


def _fresh_breaker(monkeypatch):
    breaker = jev_client._CircuitBreaker()
    monkeypatch.setattr(jev_client, "_breaker", breaker)
    return breaker


def _jev_events(caplog):
    """Devolve ``[(levelno, entry), ...]`` dos logs ``event="jev_call"``."""
    events = []
    for record in caplog.records:
        try:
            entry = json.loads(record.getMessage())
        except ValueError:
            continue
        if entry.get("event") == "jev_call":
            events.append((record.levelno, entry))
    return events


def test_ok_loga_info_com_routine(monkeypatch, caplog):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)
    monkeypatch.setattr(
        jev_client.httpx, "post",
        lambda *a, **kw: FakeResponse(200, CHOICE_PAYLOAD),
    )
    caplog.set_level(logging.INFO)

    jev_client.jev_choice("i", {"DIRECT": "d"}, {"x": 1}, routine="r6_analytics")

    events = _jev_events(caplog)
    assert len(events) == 1
    level, entry = events[0]
    assert level == logging.INFO
    assert entry["status"] == "ok"
    assert entry["routine"] == "r6_analytics"
    assert entry["model"] == "typesafe/jev-1.13"
    assert isinstance(entry["latency_ms"], int)
    assert "error" not in entry


def test_rate_limited_loga_warning(monkeypatch, caplog):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)
    monkeypatch.setattr(
        jev_client.httpx, "post",
        lambda *a, **kw: FakeResponse(429, {}),
    )
    caplog.set_level(logging.INFO)

    assert jev_client.jev_choice("i", {"DIRECT": "d"}, {"x": 1}) is None

    events = _jev_events(caplog)
    assert len(events) == 1
    level, entry = events[0]
    assert level == logging.WARNING
    assert entry["status"] == "rate_limited"


def test_no_credits_loga_error(monkeypatch, caplog):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)
    monkeypatch.setattr(
        jev_client.httpx, "post",
        lambda *a, **kw: FakeResponse(402, {}),
    )
    caplog.set_level(logging.INFO)

    assert jev_client.jev_choice("i", {"DIRECT": "d"}, {"x": 1}) is None

    events = _jev_events(caplog)
    assert len(events) == 1
    level, entry = events[0]
    assert level == logging.ERROR
    assert entry["status"] == "no_credits"


def test_timeout_loga_error(monkeypatch, caplog):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)

    def _timeout(*_a, **_kw):
        raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(jev_client.httpx, "post", _timeout)
    caplog.set_level(logging.INFO)

    assert jev_client.jev_choice("i", {"DIRECT": "d"}, {"x": 1}) is None

    events = _jev_events(caplog)
    assert len(events) == 1
    level, entry = events[0]
    assert level == logging.ERROR
    assert entry["status"] == "timeout"


def test_circuit_breaker_aberto_loga_warning(monkeypatch, caplog):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    breaker = _fresh_breaker(monkeypatch)
    breaker.failures = 3
    breaker.opened_at = time.monotonic()
    caplog.set_level(logging.INFO)

    assert jev_client.jev_choice("i", {"DIRECT": "d"}, {"x": 1}) is None

    events = _jev_events(caplog)
    assert len(events) == 1
    level, entry = events[0]
    assert level == logging.WARNING
    assert entry["status"] == "error"
    assert entry["error"] == "circuit breaker aberto"


def test_low_confidence_loga_info(monkeypatch, caplog):
    caplog.set_level(logging.INFO)

    jev_client.log_low_confidence("r1_semantic_route")

    events = _jev_events(caplog)
    assert len(events) == 1
    level, entry = events[0]
    assert level == logging.INFO
    assert entry["status"] == "low_confidence"
    assert entry["routine"] == "r1_semantic_route"
    assert "error" not in entry


def test_jev_noul_propaga_routine(monkeypatch, caplog):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)
    monkeypatch.setattr(
        jev_client.httpx, "post",
        lambda *a, **kw: FakeResponse(200, NOUL_PAYLOAD),
    )
    caplog.set_level(logging.INFO)

    assert jev_client.jev_noul("i", {"trecho": "x"}, routine="r4_rerank") == 0.87

    events = _jev_events(caplog)
    assert len(events) == 1
    _, entry = events[0]
    assert entry["routine"] == "r4_rerank"
    assert entry["status"] == "ok"


def test_jev_check_propaga_routine(monkeypatch, caplog):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)
    monkeypatch.setattr(
        jev_client.httpx, "post",
        lambda *a, **kw: FakeResponse(200, _check_payload(0.9, 0.1, 0.8)),
    )
    caplog.set_level(logging.INFO)

    assert jev_client.jev_check("claim", "evidence", routine="r3_answerability") == "supported"

    events = _jev_events(caplog)
    assert len(events) == 1
    _, entry = events[0]
    assert entry["routine"] == "r3_answerability"
    assert entry["status"] == "ok"
