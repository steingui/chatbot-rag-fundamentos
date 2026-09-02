import logging
from typing import Any, Optional
from cachetools import TTLCache

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

    def get(self, query: str, model_name: Optional[str] = None) -> Optional[Any]:
        key = self._normalize_key(query, model_name)
        data = self._cache.get(key)
        if data is not None:
            logging.info(f"Cache HIT para consulta: '{query[:40]}...'")
            return data
        return None

    def set(self, query: str, data: Any, model_name: Optional[str] = None) -> None:
        key = self._normalize_key(query, model_name)
        self._cache[key] = data
        logging.info(f"Cache SET para consulta: '{query[:40]}...'")

    def clear(self) -> None:
        self._cache.clear()

global_rag_cache = RAGQueryCache(ttl_seconds=300, max_size=200)
