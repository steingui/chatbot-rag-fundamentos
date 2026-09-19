"""RAG-101: Roteamento semântico leve e determinístico.

Classifica a intenção da consulta antes de acionar ferramentas, evitando
custo desnecessário de LLM/retriever:

- ``RAG``: domínio legislativo/político → Pinecone (fonte primária) + Web.
- ``WEB``: intenção de recência/notícias → somente DuckDuckGo.
- ``DIRECT``: saudação/identidade → LLM direto, sem ferramentas.

Sem dependências externas: heurística por regex sobre texto normalizado
(NFKD, lowercase, sem acentos). A ordem importa — sinais de web vencem o
domínio, e o domínio vence a conversa casual.
"""
import re
import unicodedata
from enum import Enum


class Route(str, Enum):
    RAG = "rag"
    WEB = "web"
    DIRECT = "direct"


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


class SemanticRouter:
    """Roteador semântico de intenção do usuário (RAG vs Web vs Direct)."""

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
        return Route.RAG
