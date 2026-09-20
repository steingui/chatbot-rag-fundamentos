import os
import random
import hashlib
import logging
from typing import List, Dict, Optional

from backend.rag.jev_client import JEV_MIN_CONFIDENCE, jev_choice

# Fase 1/2: Prompts provocativos elaborados manualmente ou gerados por LLM
PROMPTS_PATH = os.path.join(os.path.dirname(__file__), "curated_prompts.json")

# Temas canônicos de produto (rótulos estáveis para métricas de uso). O Jev
# escolhe um deles; a confiança abaixo do guardrail vira "desconhecido".
QUERY_THEMES: Dict[str, str] = {
    "camara": "Câmara dos Deputados",
    "senado": "Senado Federal",
    "tse": "TSE / eleições",
    "cgu": "Portal da Transparência (CGU)",
    "checagem": "Fact-checking",
    "web": "Notícias / atualidade",
    "direto": "Conversa casual / identidade",
}

UNKNOWN_THEME = "desconhecido"


def load_prompts() -> List[str]:
    try:
        import json
        with open(PROMPTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Erro ao carregar curated_prompts.json: {e}")
        return ["Qual é a correlação entre as empresas que mais doaram no TSE e os maiores contratos no Portal da Transparência?"]


def get_top_suggestions(limit: int = 4) -> List[Dict]:
    """Fase 1/2: Retorna N iscas curiosas aleatórias (sem contadores)."""
    prompts = load_prompts()
    limit = max(1, min(int(limit), len(prompts)))
    selected = random.sample(prompts, limit)
    # A estrutura atual do frontend esperava Dict com "prompt" e opcional "count" (agora obsoleto)
    return [{"prompt": p} for p in selected]


def _classify_query_theme(query: str) -> str:
    """Canoniza o tema da query com ``jev_choice`` (G6).

    Só aceita o rótulo quando o Jev decide com confiança >= 90%
    (``JEV_MIN_CONFIDENCE``). Abaixo do guardrail, rótulo inválido ou falha do
    Jev (``None``) ⇒ ``"desconhecido"``. Nunca lança.
    """
    try:
        result = jev_choice(
            instructions="Classifique o tema da pergunta do usuário.",
            criteria=QUERY_THEMES,
            state={"pergunta": query},
        )
    except Exception:
        return UNKNOWN_THEME
    if result is None:
        return UNKNOWN_THEME
    choice, confidence = result
    if choice in QUERY_THEMES and confidence >= JEV_MIN_CONFIDENCE:
        return choice
    return UNKNOWN_THEME


def record_query(query: str) -> Optional[str]:
    """Registra o tema da query para métricas de produto (G6).

    Roda em ``background_tasks`` — nunca lança. Loga um evento estruturado com
    ``theme`` e ``query_hash`` (nunca o texto cru da query, regra de segurança
    do AGENTS.md).
    """
    try:
        theme = _classify_query_theme(query)
    except Exception:
        theme = UNKNOWN_THEME
    logging.info(
        "query_recorded theme=%s query_hash=%s",
        theme,
        hashlib.sha256(query.encode("utf-8")).hexdigest()[:16],
    )
    return theme
