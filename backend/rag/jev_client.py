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

# Severidade de log por ``status`` (contrato JEV_ALERTING.md §1). O circuit
# breaker aberto usa ``status="error"`` com severidade WARNING — tratado à parte.
_SEVERITY: dict[str, int] = {
    "ok": logging.INFO,
    "low_confidence": logging.INFO,
    "rate_limited": logging.WARNING,
    "no_credits": logging.ERROR,
    "error": logging.ERROR,
    "timeout": logging.ERROR,
}


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


def _log(status: str, error: str | None, latency_ms: int, routine: str = "r1_semantic_route") -> None:
    entry = {
        "event": "jev_call",
        "routine": routine,
        "model": JEV_MODEL,
        "status": status,
        "latency_ms": latency_ms,
    }
    if error:
        entry["error"] = error
    line = json.dumps(entry, ensure_ascii=False)
    # Circuit breaker aberto é WARNING (status="error" mas não é falha de rede).
    if status == "error" and error == "circuit breaker aberto":
        logger.warning(line)
    else:
        logger.log(_SEVERITY.get(status, logging.ERROR), line)


def log_low_confidence(routine: str) -> None:
    """Registra a delegação por guardrail de 90% (não é falha — é o guardrail)."""
    _log("low_confidence", None, 0, routine)


def _system_one(questions: dict, state: dict, routine: str) -> dict | None:
    """POST ``/v1/systemone`` e devolve o JSON bruto, ou ``None`` em falha."""
    if not _breaker.allow():
        _log("error", "circuit breaker aberto", 0, routine)
        return None

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        _log("error", "OPENROUTER_API_KEY ausente", 0, routine)
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
        _log(status, last_error or "sem resposta", latency_ms, routine)
        return None

    if response.status_code == 401:
        _breaker.record_failure()
        _log("error", "401 chave inválida", latency_ms, routine)
        return None
    if response.status_code == 402:
        _breaker.record_failure()
        _log("no_credits", "402 sem crédito", latency_ms, routine)
        return None
    if response.status_code == 429:
        _breaker.record_failure()
        _log("rate_limited", "429", latency_ms, routine)
        return None
    if response.status_code != 200:
        _breaker.record_failure()
        _log("error", f"HTTP {response.status_code}", latency_ms, routine)
        return None

    try:
        data = response.json()
    except ValueError:
        _breaker.record_failure()
        _log("error", "resposta JSON inválida", latency_ms, routine)
        return None

    _breaker.record_success()
    _log("ok", None, latency_ms, routine)
    return data


def jev_choice(
    instructions: str,
    criteria: dict[str, str],
    state: dict,
    routine: str = "r1_semantic_route",
) -> tuple[str, float] | None:
    """Escolhe um rótulo entre ``criteria`` com a confiança calibrada.

    Devolve ``(choice, confidence)``. ``None`` em falha (fallback do chamador).
    A aplicação do limiar de 90% é responsabilidade da rotina, que decide se
    arbitra sozinha ou delega ao decider LLM.
    """
    data = _system_one(
        {"route": {"type": "choice", "instructions": instructions, "criteria": criteria}},
        state,
        routine,
    )
    if not data:
        return None
    answer = data.get("answers", {}).get("route")
    if not (isinstance(answer, dict) and isinstance(answer.get("choice"), str)):
        _breaker.record_failure()
        _log("error", "resposta sem escolha válida", 0, routine)
        return None

    confidence = answer.get("confidence")
    if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
        confidence = 0.0
    return answer["choice"], float(confidence)


# Vereditos canônicos do ``jev_check`` (contrato do jevcore/TypeSafe).
CHECK_SUPPORTED = "supported"
CHECK_CONTRADICTED = "contradicted"
CHECK_CONFLICTED = "conflicted"
CHECK_INSUFFICIENT = "insufficient"
CHECK_UNKNOWN = "unknown"

# Limiares do jevcore ``resolveCheck`` (contrato de precedência: contradição
# vence suporte; suporte sem suficiência = ``insufficient``).
_CHECK_SUPPORT_THRESHOLD = 0.7
_CHECK_CONTRADICTION_THRESHOLD = 0.7
_CHECK_SUFFICIENCY_THRESHOLD = 0.5

# Ids canônicos do jevcore (``VERDICT_QUESTION``): as chaves das perguntas são
# também as chaves das respostas no payload System One.
_CHECK_QUESTIONS = {
    "supports_claim": {"type": "noul", "instructions": "Does this evidence support the claim?"},
    "contradicts_claim": {"type": "noul", "instructions": "Does this evidence contradict the claim?"},
    "evidence_is_sufficient": {"type": "noul", "instructions": "Is this evidence sufficient to settle whether the claim is true?"},
}


def _read_noul(answers: dict, key: str) -> float | None:
    answer = answers.get(key)
    if isinstance(answer, dict) and answer.get("type") == "noul":
        noul = answer.get("noul")
        if isinstance(noul, (int, float)) and 0 <= noul <= 1:
            return float(noul)
    return None


def jev_noul(
    instructions: str,
    state: dict,
    routine: str = "r4_rerank",
) -> float | None:
    """Devolve o ``noul`` calibrado (0..1) para uma única pergunta.

    Usado no rerank (G3) para julgar, documento a documento, se o trecho
    responde à pergunta. ``None`` em falha (fallback do chamador: mantém o
    documento — o pipeline nunca quebra por indisponibilidade do Jev).
    """
    data = _system_one(
        {"relevance": {"type": "noul", "instructions": instructions}},
        state,
        routine,
    )
    if not data:
        return None
    noul = _read_noul(data.get("answers", {}), "relevance")
    if noul is None:
        _breaker.record_failure()
        _log("error", "resposta sem noul válido", 0, routine)
    return noul


def jev_check(
    claim: str,
    evidence: str,
    state: dict | None = None,
    routine: str = "r3_answerability",
) -> str | None:
    """Verifica se ``evidence`` sustenta ``claim`` (veredito calibrado).

    Espelha o ``jev_check`` do jevcore: três perguntas ``noul`` independentes
    (suporta / contradiz / suficiente) resolvidas com precedência em código —
    contradição vence suporte; suporte sem suficiência é ``insufficient``.

    Devolve o veredito canônico ou ``None`` em falha (fallback do chamador:
    o pipeline nunca quebra por indisponibilidade do Jev).
    """
    questions = {k: dict(v) for k, v in _CHECK_QUESTIONS.items()}
    data = _system_one(
        questions,
        {"claim": claim, "evidence": evidence, **(state or {})},
        routine,
    )
    if not data:
        return None

    answers = data.get("answers", {})
    supports = _read_noul(answers, "supports_claim")
    contradicts = _read_noul(answers, "contradicts_claim")
    sufficient = _read_noul(answers, "evidence_is_sufficient")

    if supports is None and contradicts is None:
        _breaker.record_failure()
        _log("error", "resposta sem veredito válido", 0, routine)
        return None

    if (supports or 0) >= _CHECK_SUPPORT_THRESHOLD and (contradicts or 0) >= _CHECK_CONTRADICTION_THRESHOLD:
        return CHECK_CONFLICTED
    if (contradicts or 0) >= _CHECK_CONTRADICTION_THRESHOLD:
        return CHECK_CONTRADICTED
    if (supports or 0) >= _CHECK_SUPPORT_THRESHOLD:
        if sufficient is not None and sufficient < _CHECK_SUFFICIENCY_THRESHOLD:
            return CHECK_INSUFFICIENT
        return CHECK_SUPPORTED
    return CHECK_INSUFFICIENT
