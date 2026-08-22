import re
import logging
import unicodedata
from fastapi import HTTPException

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
    r"ignore\s+(todas?\s+)?(as\s+)?instru[çc][õo]es\s+anteriores",
    r"esque[çc]a\s+(tudo|todas?\s+regras?)",
    r"agora\s+voc[êe]\s+[ée]\s+um",
    r"finja\s+que\s+(voc[êe]|n[ãa]o\s+tem\s+restri)",
    r"novas?\s+instru[çc][õo]es?\s*:",
    r"desconsidere\s+(tudo|as?\s+regras?)",
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

    if COMPILED_INJECTION_REGEX.search(normalized_query):
        import hashlib
        # SEC-011: Loga apenas o hash (SHA-256 truncado) da query maliciosa para não expor PII nos logs (LGPD)
        query_hash = hashlib.sha256(cleaned_query.encode('utf-8')).hexdigest()[:16]
        logging.warning(f"SEC-011: Prompt Injection bloqueado (hash: {query_hash})")
        raise HTTPException(
            status_code=400,
            detail="Consulta bloqueada pelas diretrizes de segurança anti-prompt injection."
        )

    return cleaned_query
