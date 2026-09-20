import hashlib
import logging
from typing import Any, Optional
from cachetools import TTLCache

from backend.rag.jev_client import jev_noul

logger = logging.getLogger(__name__)

# G7 — Limiar de equivalência semântica: reusa cache quando o Jev julga que a
# nova query é a mesma pergunta de uma chave recente do mesmo modelo.
SEMANTIC_DEDUP_THRESHOLD = 0.9


def _hash(query: str) -> str:
    """Hash curto da query para log sem expor PII (regra de segurança do AGENTS.md)."""
    return hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]


class RAGQueryCache:
    """Cache em memória com TTL (Time-To-Live) e LRU de alta performance alimentado por cachetools."""

    def __init__(self, ttl_seconds: int = 300, max_size: int = 200):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache = TTLCache(maxsize=max_size, ttl=ttl_seconds)

    def _normalize_key(self, query: str, model_name: Optional[str] = None) -> str:
        clean = " ".join(query.strip().lower().split())
        model = model_name or "default"
        return f"{model}:{clean}"

    def _semantic_hit(self, query: str, model: str) -> Optional[Any]:
        """Dedup semântico (G7): compara a query com chaves recentes do mesmo modelo.

        ``None``/falha do Jev ou ``noul`` abaixo do limiar ⇒ sem hit (comportamento
        atual). Nunca cruza modelos diferentes.
        """
        clean = " ".join(query.strip().lower().split())
        prefix = f"{model}:"
        for key, data in list(self._cache.items()):
            if not key.startswith(prefix):
                continue
            cached_query = key[len(prefix):]
            noul = jev_noul(
                instructions="Does this question mean the same as the cached question?",
                state={"pergunta": clean, "cache": cached_query},
                routine="r7_cache",
            )
            if noul is not None and noul >= SEMANTIC_DEDUP_THRESHOLD:
                logger.info("Cache HIT semântico query_hash=%s", _hash(query))
                return data
        return None

    def get(self, query: str, model_name: Optional[str] = None) -> Optional[Any]:
        key = self._normalize_key(query, model_name)
        data = self._cache.get(key)
        if data is not None:
            logger.info("Cache HIT query_hash=%s", _hash(query))
            return data
        return self._semantic_hit(query, model_name or "default")

    def set(self, query: str, data: Any, model_name: Optional[str] = None) -> None:
        key = self._normalize_key(query, model_name)
        self._cache[key] = data
        logger.info("Cache SET query_hash=%s", _hash(query))

    def clear(self) -> None:
        self._cache.clear()


global_rag_cache = RAGQueryCache(ttl_seconds=300, max_size=200)
