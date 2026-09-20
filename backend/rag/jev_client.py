"""Cliente fino para o System One do TypeSafe Jev via OpenRouter.

Camada de decisão calibrada (não substitui a síntese). Toda chamada tem:

- timeout + 1 retry (5xx/timeout/rede);
- circuit breaker simples (3 falhas consecutivas → 60s aberto);
- fallback ``None`` em qualquer falha — o pipeline **nunca** quebra por
  indisponibilidade do Jev;
- log estruturado ``event="jev_call"`` (contrato de
  [`JEV_ALERTING.md`](../docs/JEV_ALERTING.md)).

Modelo fixo ``typesafe/jev-1.13``; nunca ``jev-latest`` (não resolve no
OpenRouter).
"""
import json
import logging
import os
import time

import httpx

JEV_ENDPOINT = "https://openrouter.ai/api/v1/systemone"
JEV_MODEL = "typesafe/jev-1.13"
JEV_TIMEOUT = 5.0
JEV_MAX_ATTEMPTS = 2  # tentativa inicial + 1 retry

# Guardrail de confiança: o Jev só decide sozinho com >= 90% de confiança.
# Abaixo disso a rotina chama o decider LLM; ausência do campo é tratada como 0.
JEV_MIN_CONFIDENCE = 0.9

logger = logging.getLogger("jev_client")


class _CircuitBreaker:
    """Abre após ``threshold`` falhas consecutivas e rearma após ``cooldown``s."""

    def __init__(self, threshold: int = 3, cooldown: float = 60.0):
        self.threshold = threshold
        self.cooldown = cooldown
        self.failures = 0
        self.opened_at: float | None = None

    def allow(self) -> bool:
        if self.opened_at is not None:
            if time.monotonic() - self.opened_at >= self.cooldown:
                self.opened_at = None
                self.failures = 0
            else:
                return False
        return True

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.threshold:
            self.opened_at = time.monotonic()

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = None


_breaker = _CircuitBreaker()


def _log(status: str, error: str | None, latency_ms: int) -> None:
    entry = {
        "event": "jev_call",
        "routine": "r1_semantic_route",
        "model": JEV_MODEL,
        "status": status,
        "latency_ms": latency_ms,
    }
    if error:
        entry["error"] = error
    line = json.dumps(entry, ensure_ascii=False)
    if status == "ok":
        logger.info(line)
    else:
        logger.error(line)


def _system_one(questions: dict, state: dict) -> dict | None:
    """POST ``/v1/systemone`` e devolve o JSON bruto, ou ``None`` em falha."""
    if not _breaker.allow():
        _log("error", "circuit breaker aberto", 0)
        return None

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        _log("error", "OPENROUTER_API_KEY ausente", 0)
        return None

    payload = {"state": state, "model": JEV_MODEL, "questions": questions}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    started = time.monotonic()
    response = None
    status = "error"
    last_error: str | None = None

    for _ in range(JEV_MAX_ATTEMPTS):
        try:
            response = httpx.post(JEV_ENDPOINT, headers=headers, json=payload, timeout=JEV_TIMEOUT)
        except httpx.TimeoutException:
            status = "timeout"
            last_error = "timeout"
            response = None
            continue
        except httpx.TransportError:
            status = "error"
            last_error = "falha de rede"
            response = None
            continue
        if response.status_code >= 500:
            status = "error"
            last_error = f"HTTP {response.status_code}"
            response = None
            continue
        break

    latency_ms = int((time.monotonic() - started) * 1000)

    if response is None:
        _breaker.record_failure()
        _log(status, last_error or "sem resposta", latency_ms)
        return None

    if response.status_code == 401:
        _breaker.record_failure()
        _log("error", "401 chave inválida", latency_ms)
        return None
    if response.status_code == 402:
        _breaker.record_failure()
        _log("no_credits", "402 sem crédito", latency_ms)
        return None
    if response.status_code == 429:
        _breaker.record_failure()
        _log("rate_limited", "429", latency_ms)
        return None
    if response.status_code != 200:
        _breaker.record_failure()
        _log("error", f"HTTP {response.status_code}", latency_ms)
        return None

    try:
        data = response.json()
    except ValueError:
        _breaker.record_failure()
        _log("error", "resposta JSON inválida", latency_ms)
        return None

    _breaker.record_success()
    _log("ok", None, latency_ms)
    return data


def jev_choice(instructions: str, criteria: dict[str, str], state: dict) -> tuple[str, float] | None:
    """Escolhe um rótulo entre ``criteria`` com a confiança calibrada.

    Devolve ``(choice, confidence)``. ``None`` em falha (fallback do chamador).
    A aplicação do limiar de 90% é responsabilidade da rotina, que decide se
    arbitra sozinha ou delega ao decider LLM.
    """
    data = _system_one(
        {"route": {"type": "choice", "instructions": instructions, "criteria": criteria}},
        state,
    )
    if not data:
        return None
    answer = data.get("answers", {}).get("route")
    if not (isinstance(answer, dict) and isinstance(answer.get("choice"), str)):
        _breaker.record_failure()
        _log("error", "resposta sem escolha válida", 0)
        return None

    confidence = answer.get("confidence")
    if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
        confidence = 0.0
    return answer["choice"], float(confidence)
