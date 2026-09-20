"""RAG-101: Roteamento semântico leve e determinístico.

Classifica a intenção da consulta antes de acionar ferramentas, evitando
custo desnecessário de LLM/retriever:

- ``RAG``: domínio legislativo/político → Pinecone (fonte primária) + Web.
- ``WEB``: intenção de recência/notícias → somente DuckDuckGo.
- ``DIRECT``: saudação/identidade → LLM direto, sem ferramentas.

Ordem de decisão (da mais barata para a mais cara):

1. **Regex soberano** (custo zero) decide os casos óbvios.
2. **Jev** arbitra o default ambíguo — mas só opera com **confiança ≥ 90%**
   (guardrail). Abaixo disso a decisão é delegada às nossas LLMs.
3. **Decider LLM** decide a rota quando o Jev está abaixo do limiar.
4. **Fallback final** ``Route.RAG`` (comportamento atual) se Jev e LLM
   estiverem indisponíveis — o pipeline nunca quebra.
"""
import os
import re
import unicodedata
from enum import Enum

import httpx

from backend.rag.jev_client import JEV_MIN_CONFIDENCE, jev_choice


class Route(str, Enum):
    RAG = "rag"
    WEB = "web"
    DIRECT = "direct"


OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DECIDER_MODEL = os.environ.get("JEV_DECIDER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

# Intenção de recência/notícias (avaliada primeiro: "notícias de hoje sobre
# o congresso" é WEB, não RAG).
_WEB_RE = re.compile(
    r"not[íi]cia|aconteceu|recentemente|hoje|[úu]ltimas|ao vivo|destaques|"
    r"atualiza[çc][ãa]o|em tempo real"
)

# Domínio legislativo/político — base factual interna.
_DOMAIN_RE = re.compile(
    r"votou|voto|vota[çc]|plp|pec\b|projeto|lei\b|leis\b|deputad|senador|"
    r"c[âa]mara|senado|\btse\b|cgu|or[çc]amento|bens\b|candidat|partido|"
    r"elei[çc]|legisl|transpar[êe]ncia|checagem|fato\b|governo|ministro|"
    r"presidente|pol[íi]tic|emenda|decreto|medida provis[óo]ria|stf|supremo|"
    r"plen[áa]rio|comiss[ãa]o|mandato|parlamentar|congresso"
)

# Conversa casual (identidade/saudação) — só é atingida quando não há sinal
# de domínio nem de web.
_DIRECT_RE = re.compile(
    r"^(ol[áa]|oi|eai|e a[íi]|hey|hello|hi|bom dia|boa tarde|boa noite|"
    r"tchau|at[ée] mais|valeu|obrigad[oa]?)\b|"
    r"tudo bem|como (voc[êe]|vc) (est[áa]|ta)|"
    r"quem ([ée]h? )?[ée] voc[êe]|quem [ée] voc[êe]|"
    r"o que (voc[êe]|vc) (faz|fazem)|qual ([ée]h? )?(o )?seu nome|"
    r"prazer em"
)

# Follow-ups conversacionais (G8): continuação do diálogo sobre a resposta
# anterior, sem palavra de domínio nem de recência. São DIRECT por regex (custo
# zero), nunca RAG/web — evita DDGS com query "fale mais" e lixo de fontes.
_FOLLOWUP_RE = re.compile(
    r"^(fale mais|fala mais|pode falar mais|falar mais|fale sobre|"
    r"continue|continua|continuar|"
    r"explique melhor|explica melhor|explique mais|explica mais|"
    r"mais detalhes|mais informa[çc][õo]es|detalhe mais|detalhes|"
    r"aprofunde)\b"
)

_DECIDER_PROMPT = (
    "Decida a rota de atendimento para a pergunta. Responda exatamente uma "
    "palavra:\n"
    "RAG — pergunta factual sobre política/legislação;\n"
    "WEB — pede notícias ou informação recente;\n"
    "DIRECT — conversa casual, identidade ou fora do domínio.\n\n"
    "Pergunta: "
)


def _parse_route_token(token: str) -> Route | None:
    """Mapeia o primeiro token da resposta do decider para uma rota válida."""
    first = token.strip().upper().split()[0].strip(".,;:\"")
    for route in (Route.RAG, Route.WEB, Route.DIRECT):
        if first.startswith(route.value.upper()):
            return route
    return None


def _llm_decide(query: str) -> Route | None:
    """Decider LLM via OpenRouter (chat completions). ``None`` em falha."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        response = httpx.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": DECIDER_MODEL,
                "messages": [
                    {"role": "user", "content": _DECIDER_PROMPT + query},
                ],
                "max_tokens": 5,
                "temperature": 0,
            },
            timeout=5.0,
        )
        if response.status_code != 200:
            return None
        content = response.json()["choices"][0]["message"]["content"]
        return _parse_route_token(content)
    except Exception:
        return None


def _jev_choice(instructions: str, criteria: dict[str, str], state: dict) -> tuple[str, float] | None:
    return jev_choice(instructions, criteria, state)


class SemanticRouter:
    """Roteador semântico de intenção do usuário (RAG vs Web vs Direct)."""

    def __init__(self, decider=None):
        self._decider = decider

    def _normalize(self, text: str) -> str:
        nfkd = unicodedata.normalize("NFKD", text.lower())
        ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
        return " ".join(ascii_only.split())

    def route(self, query: str) -> Route:
        q = self._normalize(query)
        if _WEB_RE.search(q):
            return Route.WEB
        if _DOMAIN_RE.search(q):
            return Route.RAG
        if _DIRECT_RE.search(q):
            return Route.DIRECT
        if _FOLLOWUP_RE.search(q):
            return Route.DIRECT

        # Default ambíguo: Jev arbitra, mas só opera com confiança >= 90%.
        result = _jev_choice(
            instructions="Classifique a intenção da pergunta.",
            criteria={
                "RAG": "pergunta factual sobre política/legislação",
                "WEB": "pede notícias ou informação recente",
                "DIRECT": "conversa casual, identidade ou fora do domínio",
            },
            state={"pergunta": query},
        )
        if result is not None:
            choice, confidence = result
            if confidence >= JEV_MIN_CONFIDENCE:
                route = _parse_route_token(choice)
                if route is not None:
                    return route

        # Jev abaixo de 90% (ou falhou): delega a decisão às nossas LLMs.
        decider = self._decider or _llm_decide
        try:
            decided = decider(query)
        except Exception:
            decided = None
        if decided is not None and decided in (Route.RAG, Route.WEB, Route.DIRECT):
            return decided

        # Fallback final: comportamento atual.
        return Route.RAG
