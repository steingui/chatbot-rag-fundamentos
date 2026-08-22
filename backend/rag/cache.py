import time
import logging
from typing import Dict, Any, Optional, Tuple

class RAGQueryCache:
    """Cache em memória com TTL (Time-To-Live) para armazenar respostas de consultas frequentes do RAG."""

    def __init__(self, ttl_seconds: int = 300, max_size: int = 200):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: Dict[str, Tuple[float, Any]] = {}

    def _normalize_key(self, query: str, model_name: Optional[str] = None) -> str:
        clean = " ".join(query.strip().lower().split())
        model = model_name or "default"
        return f"{model}:{clean}"

    def get(self, query: str, model_name: Optional[str] = None) -> Optional[Any]:
        key = self._normalize_key(query, model_name)
        if key in self._cache:
            timestamp, data = self._cache[key]
            if time.time() - timestamp <= self.ttl_seconds:
                logging.info(f"Cache HIT para consulta: '{query[:40]}...'")
                return data
            else:
                logging.info(f"Cache EXPIRED para consulta: '{query[:40]}...'")
                del self._cache[key]
        return None

    def set(self, query: str, data: Any, model_name: Optional[str] = None) -> None:
        if len(self._cache) >= self.max_size:
            # Remove o item mais antigo
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        
        key = self._normalize_key(query, model_name)
        self._cache[key] = (time.time(), data)
        logging.info(f"Cache SET para consulta: '{query[:40]}...'")

    def clear(self) -> None:
        self._cache.clear()

global_rag_cache = RAGQueryCache(ttl_seconds=300, max_size=200)
