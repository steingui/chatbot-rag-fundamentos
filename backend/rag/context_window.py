"""RAG-109: Janela de contexto dinâmica baseada em contagem EXATA de tokens.

Preserva o histórico RECENTE da conversa, descartando as mensagens mais
antigas que estouram o orçamento de entrada do modelo. Contagem exata via
tokenizer cl100k_base (tiktoken), que é a base do OpenRouter/Gemini/DeepSeek.
"""
import logging
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Orçamento de entrada do modelo (total - reserva para resposta).
# 1.0M de janela total para os Gemini 3.x / DeepSeek V4; a conta não muda
# o orçamento de SAÍDA: reservamos 8k tokens para a resposta gerada.
MODEL_INPUT_BUDGETS: Dict[str, int] = {
    "gemini-3.7-flash": 1_000_000 - 8192,
    "gemini-3.6-flash": 1_000_000 - 8192,
    "gemini-flash-latest": 1_000_000 - 8192,
    "gemini-3.5-flash": 1_000_000 - 8192,
    "gemini-pro-latest": 2_000_000 - 8192,
    "gemini-2.5-flash": 1_000_000 - 8192,
    "deepseek/deepseek-r1-distill-llama-70b:free": 128_000 - 4096,
    "meta-llama/llama-3.3-70b-instruct:free": 128_000 - 4096,
    "qwen/qwen-2.5-coder-32b-instruct:free": 128_000 - 4096,
}

DEFAULT_INPUT_BUDGET = 128_000 - 4096

# Encodings tolerantes: na ausência do cl100k, usa tiktoken default e por
# último um proxy de contagem determinístico (sem dependência externa).
_TOKENIZER_ENCODINGS = ("cl100k_base", "o200k_base")


@lru_cache(maxsize=1)
def _get_encoder():
    try:
        import tiktoken
    except Exception:
        return None
    for enc_name in _TOKENIZER_ENCODINGS:
        try:
            return tiktoken.get_encoding(enc_name)
        except Exception:
            continue
    return None


def count_tokens(text: str) -> int:
    """Contagem EXATA de tokens do texto (0 para vazio)."""
    if not text:
        return 0
    encoder = _get_encoder()
    if encoder is not None:
        try:
            return len(encoder.encode(text))
        except Exception:
            pass
    # Proxy determinístico (fallback de último recurso, sem dependência):
    # ~4 caracteres/token é a heurística média clássica para PT/EN.
    return max(1, len(text) // 4)


def max_input_tokens_for_model(model_name: Optional[str]) -> int:
    """Retorna o orçamento máximo de tokens de ENTRADA para o modelo."""
    if not model_name:
        return DEFAULT_INPUT_BUDGET
    return MODEL_INPUT_BUDGETS.get(model_name, DEFAULT_INPUT_BUDGET)


def format_history(history: List[Dict[str, str]]) -> str:
    """Renderiza o histórico como bloco textual para o prompt."""
    if not history:
        return ""
    linhas = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        linhas.append(f"{role.capitalize()}: {content}")
    return "\n".join(linhas)


def build_context_window(
    history: List[Dict[str, Any]],
    max_tokens: int,
) -> List[Dict[str, Any]]:
    """Poda o histórico mantendo APENAS as mensagens mais recentes cuja
    contagem exata de tokens caiba em ``max_tokens``.

    KISS: itera do fim para o início (recentes primeiro), descartando as
    mensagens mais antigas. Nunca corta uma mensagem no meio — só descarta
    mensagens inteiras para preservar a integridade do diálogo.
    """
    if not history or max_tokens <= 0:
        return []

    kept: List[Dict[str, Any]] = []
    used = 0

    # Recentes primeiro: garantimos que a mensagem mais recente sempre entra,
    # e as antigas são descartadas à medida que o orçamento estoura.
    for msg in reversed(history):
        content = str(msg.get("content", ""))
        cost = count_tokens(content)
        if used + cost <= max_tokens:
            kept.append(msg)
            used += cost
        else:
            # Estourou o orçamento: tudo mais antigo também estoura.
            break

    kept.reverse()
    return kept
