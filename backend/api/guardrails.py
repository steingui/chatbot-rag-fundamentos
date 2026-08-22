import re
import logging
from fastapi import HTTPException

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"forget\s+(all\s+)?(previous|prior)\s+commands",
    r"you\s+are\s+now\s+a",
    r"system\s*prompt\s*:",
    r"override\s+(the\s+)?system",
    r"disregard\s+(all\s+)?above",
    r"jailbreak",
    r"dan\s+mode",
    r"exec\s*\(",
    r"eval\s*\(",
    r"<script[\s>]",
]

COMPILED_INJECTION_REGEX = re.compile(
    "|".join(PROMPT_INJECTION_PATTERNS), re.IGNORECASE
)

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

    if COMPILED_INJECTION_REGEX.search(cleaned_query):
        logging.warning(f"Tentativa de Prompt Injection detectada e bloqueada: {cleaned_query[:60]}...")
        raise HTTPException(
            status_code=400,
            detail="Consulta bloqueada pelas diretrizes de segurança anti-prompt injection."
        )

    return cleaned_query
