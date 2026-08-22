import pytest
import time
from backend.rag.cache import RAGQueryCache, global_rag_cache

def test_cache_hit_and_ttl():
    cache = RAGQueryCache(ttl_seconds=1, max_size=10)
    query = "Resuma a PEC 45/2019"
    data = {"answer": "Resumo da PEC...", "sources": []}
    
    cache.set(query, data)
    hit = cache.get(query)
    assert hit is not None
    assert hit["answer"] == "Resumo da PEC..."

    time.sleep(1.1)
    expired = cache.get(query)
    assert expired is None

def test_cache_max_size_eviction():
    cache = RAGQueryCache(ttl_seconds=10, max_size=2)
    cache.set("q1", "ans1")
    cache.set("q2", "ans2")
    cache.set("q3", "ans3")
    
    # q1 should be evicted because max_size is 2
    assert cache.get("q1") is None
    assert cache.get("q2") == "ans2"
    assert cache.get("q3") == "ans3"

def test_global_rag_cache_isolation():
    global_rag_cache.clear()
    global_rag_cache.set("teste", {"answer": "ok", "sources": []}, model_name="nemotron")
    assert global_rag_cache.get("teste", model_name="nemotron") is not None
    assert global_rag_cache.get("teste", model_name="gpt4") is None
