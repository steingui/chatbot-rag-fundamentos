import re
import logging
import unicodedata
import warnings
from functools import lru_cache

from fastapi import HTTPException

try:
    from sklearn.exceptions import InconsistentVersionWarning
except Exception:  # pragma: no cover - scikit-learn opcional
    InconsistentVersionWarning = Warning

# SEC-008: Patterns expandidos com variantes em português, Unicode e técnicas avançadas
PROMPT_INJECTION_PATTERNS = [
    # Inglês
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"forget\s+(all\s+)?(previous|prior)\s+commands",
    r"you\s+are\s+now\s+a",
    r"system\s*prompt\s*:",
    r"override\s+(the\s+)?system",
    r"disregard\s+(all\s+)?above",
    r"jailbreak",
    r"dan\s+mode",
    r"do\s+anything\s+now",
    r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
    r"pretend\s+you\s+(are|can)",
    r"new\s+instructions?\s*:",
    r"ignore\s+safety",
    # Português
    r"ignore\s+.*instru[çc][õo]es",
    r"esque[çc]a\s+(tudo|todas?\s+regras?|instru[çc][õo]es)",
    r"agora\s+voc[êe]\s+[ée]\s+um",
    r"finja\s+que\s+(voc[êe]|n[ãa]o\s+tem\s+restri)",
    r"novas?\s+instru[çc][õo]es?\s*:",
    r"desconsidere\s+(tudo|as?\s+regras?|instru[çc][õo]es)",
    # Out of Scope / Conversas fora de escopo
    r"receita\s+de\s+",
    r"bolo\s+de\s+",
    # Code injection
    r"exec\s*\(",
    r"eval\s*\(",
    r"<script[\s>]",
    r"javascript\s*:",
    r"on(error|load|click)\s*=",
    r"\{\{.*\}\}",  # Template injection
]

COMPILED_INJECTION_REGEX = re.compile(
    "|".join(PROMPT_INJECTION_PATTERNS), re.IGNORECASE
)

# Tenta carregar biblioteca especializada de detecção de injeção.
# O pacote `prompt-injection-detector` empacota model.pkl/vectorizer.pkl
# serializados com scikit-learn 1.8.0; ao desserializar com 1.9.0, o sklearn
# emite InconsistentVersionWarning (artefato de terceiros, não retreinável aqui).
try:
    import prompt_injection_detector as pid
except Exception:  # pragma: no cover - dependência opcional
    pid = None


@lru_cache(maxsize=1)
def _get_pid_scanner():
    """Carrega o Scanner PID uma única vez (lazy), suprimindo o warning de
    versão dos artefatos pickle de terceiros. Retorna None se indisponível."""
    if pid is None:
        return None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", InconsistentVersionWarning)
            return pid.Scanner()
    except Exception:  # pragma: no cover - depende de artefatos do pacote
        return None


def validate_and_sanitize_query(query: str) -> str:
    """Higieniza e valida a consulta do usuário contra injeção de prompt e exploits."""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="A consulta não pode estar vazia.")

    cleaned_query = query.strip()

    if len(cleaned_query) > 1000:
        raise HTTPException(
            status_code=400,
            detail="A consulta excede o limite máximo permitido de 1000 caracteres."
        )

    # SEC-008: Normalização Unicode (NFKC) para evitar bypass via homoglyphs
    normalized_query = unicodedata.normalize("NFKC", cleaned_query)

    import hashlib
    query_hash = hashlib.sha256(cleaned_query.encode('utf-8')).hexdigest()[:16]

    # Camada 1: Regex e heurísticas locais
    if COMPILED_INJECTION_REGEX.search(normalized_query):
        logging.warning(f"SEC-011: Prompt Injection bloqueado por Regex (hash: {query_hash})")
        raise HTTPException(
            status_code=400,
            detail="Consulta bloqueada pelas diretrizes de segurança anti-prompt injection."
        )

    # Camada 2: Scanner especializado via biblioteca prompt-injection-detector
    _pid_scanner = _get_pid_scanner()
    if _pid_scanner is not None:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", InconsistentVersionWarning)
                scan_res = _pid_scanner.scan(normalized_query)
            if scan_res.decision == "reject" or scan_res.risk_score >= 0.85:
                logging.warning(f"SEC-011: Prompt Injection bloqueado por PID Scanner (score: {scan_res.risk_score:.2f}, hash: {query_hash})")
                raise HTTPException(
                    status_code=400,
                    detail="Consulta bloqueada pelas diretrizes de segurança anti-prompt injection."
                )
        except HTTPException:
            raise
        except Exception as e:
            logging.debug(f"Falha ao rodar PID scanner: {e}")

    return cleaned_query

