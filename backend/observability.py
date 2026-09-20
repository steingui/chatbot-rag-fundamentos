"""Observabilidade mínima: correlation id (``session_id``) e log JSON estruturado.

Uso no entrypoint da API::

    from backend.observability import setup_logging
    setup_logging()

Uso por requisição::

    from backend.observability import set_session_id, reset_session_id
    token = set_session_id(body.session_id)
    try:
        ...
    finally:
        reset_session_id(token)

Todos os logs emitidos abaixo do escopo carregam ``session_id`` via
:class:`SessionContextFilter`. O logger ``"jev_client"`` fica isolado com
handler cru porque já emite JSON estruturado (contrato ``event="jev_call"``).
"""
import contextvars
import json
import logging

_SESSION_ID: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "session_id", default=None
)


class SessionContextFilter(logging.Filter):
    """Injeta ``session_id`` (do contextvar) em todo record de log."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.session_id = _SESSION_ID.get() or "-"
        return True


class JsonFormatter(logging.Formatter):
    """Formata o record como JSON de linha única, com exceção quando houver."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "event": record.getMessage(),
            "level": record.levelname,
            "logger": record.name,
            "session_id": getattr(record, "session_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def set_session_id(session_id: str | None) -> contextvars.Token:
    return _SESSION_ID.set(session_id or "-")


def reset_session_id(token: contextvars.Token) -> None:
    _SESSION_ID.reset(token)


def setup_logging() -> None:
    """Configura o logger raiz com JSON + session_id e isola o ``jev_client``.

    Idempotente: limpa handlers existentes antes de reconfigurar.
    """
    root = logging.getLogger()
    root.handlers[:] = []
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(SessionContextFilter())
    root.addHandler(handler)

    # O cliente Jev já emite JSON estruturado; handler cru, sem re-wrap.
    jev = logging.getLogger("jev_client")
    jev.handlers[:] = []
    jev.propagate = False
    jev.setLevel(logging.INFO)
    jev.addHandler(logging.StreamHandler())
