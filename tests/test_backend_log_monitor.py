"""SDD: backend_log_monitor não eleva request outbound (INFO) com HTTP 5xx para ERROR.

O log `INFO: HTTP Request: POST ... "HTTP/1.1 503 Service Unavailable"` é o cliente
HTTP do Gemini reportando a resposta do provedor — não é um erro do backend.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.backend_log_monitor import error_severity, is_error  # noqa: E402


OUTBOUND_503 = {
    "severity": "INFO",
    "jsonPayload": {
        "message": (
            'INFO: HTTP Request: POST '
            'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.7-flash:'
            'streamGenerateContent?alt=sse "HTTP/1.1 503 Service Unavailable"'
        )
    },
    "timestamp": "2026-09-20T21:09:23Z",
}

SERVER_5XX_TEXT = {
    "severity": "INFO",
    "textPayload": 'GET /chat "HTTP/1.1 503 Service Unavailable"',
    "timestamp": "2026-09-20T21:09:23Z",
}

REAL_ERROR = {
    "severity": "ERROR",
    "jsonPayload": {"message": "boom"},
    "timestamp": "2026-09-20T21:09:23Z",
}


def test_outbound_info_503_is_not_an_error():
    assert not is_error(OUTBOUND_503)


def test_outbound_info_503_keeps_info_severity():
    assert error_severity(OUTBOUND_503) == "INFO"


def test_server_5xx_logged_as_info_is_still_elevated():
    assert is_error(SERVER_5XX_TEXT)
    assert error_severity(SERVER_5XX_TEXT) == "ERROR"


def test_real_error_still_detected():
    assert is_error(REAL_ERROR)
    assert error_severity(REAL_ERROR) == "ERROR"
