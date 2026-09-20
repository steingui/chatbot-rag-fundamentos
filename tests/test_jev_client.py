"""G1 — jev_client: System One via OpenRouter com timeout/retry e circuit breaker.

Contrato de robustez: toda chamada tem timeout + 1 retry (5xx/timeout/rede),
circuit breaker após 3 falhas consecutivas e **sempre** devolve ``None`` em
falha (nunca lança para o chamador).
"""
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


def _fresh_breaker(monkeypatch):
    breaker = jev_client._CircuitBreaker()
    monkeypatch.setattr(jev_client, "_breaker", breaker)
    return breaker


def _raise_connect(*_args, **_kwargs):
    raise httpx.ConnectError("down")


def test_jev_choice_sem_chave_retorna_none(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert jev_client.jev_choice("i", {"A": "a"}, {"x": 1}) is None


def test_jev_choice_parseia_escolha(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)

    calls = []
    monkeypatch.setattr(
        jev_client.httpx,
        "post",
        lambda *a, **kw: calls.append(kw) or FakeResponse(200, CHOICE_PAYLOAD),
    )

    assert jev_client.jev_choice("i", {"DIRECT": "d"}, {"x": 1}) == ("DIRECT", 0.9)
    assert len(calls) == 1


def test_jev_choice_retry_em_timeout(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)

    attempts = {"n": 0}

    def fake_post(*_a, **_kw):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise httpx.TimeoutException("timeout")
        return FakeResponse(200, CHOICE_PAYLOAD)

    monkeypatch.setattr(jev_client.httpx, "post", fake_post)

    assert jev_client.jev_choice("i", {"DIRECT": "d"}, {"x": 1}) == ("DIRECT", 0.9)
    assert attempts["n"] == 2


def test_jev_choice_retry_em_5xx(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)

    attempts = {"n": 0}

    def fake_post(*_a, **_kw):
        attempts["n"] += 1
        if attempts["n"] == 1:
            return FakeResponse(500, {})
        return FakeResponse(200, CHOICE_PAYLOAD)

    monkeypatch.setattr(jev_client.httpx, "post", fake_post)

    assert jev_client.jev_choice("i", {"DIRECT": "d"}, {"x": 1}) == ("DIRECT", 0.9)
    assert attempts["n"] == 2


def test_jev_choice_nao_retry_em_401(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    _fresh_breaker(monkeypatch)

    attempts = {"n": 0}

    def fake_post(*_a, **_kw):
        attempts["n"] += 1
        return FakeResponse(401, {})

    monkeypatch.setattr(jev_client.httpx, "post", fake_post)

    assert jev_client.jev_choice("i", {"DIRECT": "d"}, {"x": 1}) is None
    assert attempts["n"] == 1


def test_circuit_breaker_abre_apos_3_falhas(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    breaker = _fresh_breaker(monkeypatch)
    monkeypatch.setattr(jev_client.httpx, "post", _raise_connect)

    for _ in range(3):
        assert jev_client.jev_choice("i", {"DIRECT": "d"}, {"x": 1}) is None
    assert breaker.allow() is False

    calls = {"n": 0}
    monkeypatch.setattr(
        jev_client.httpx,
        "post",
        lambda *a, **kw: calls.__setitem__("n", calls["n"] + 1),
    )
    assert jev_client.jev_choice("i", {"DIRECT": "d"}, {"x": 1}) is None
    assert calls["n"] == 0


def test_circuit_breaker_reabre_apos_janela(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-teste")
    breaker = _fresh_breaker(monkeypatch)
    breaker.failures = 3
    breaker.opened_at = time.monotonic() - 61

    assert breaker.allow() is True
