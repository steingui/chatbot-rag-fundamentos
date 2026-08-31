import pytest
from backend.api.main import parse_source_name
from backend.rag.cache import RAGQueryCache
from backend.rag.retriever import HybridRetriever
from backend.api.analytics import record_query, get_top_suggestions
from langchain_core.documents import Document

def test_source_classification_business_rules():
    """Valida regra 3: Classificacao e Rastreabilidade de Fontes por metadados."""
    # Votacao Camara
    f1 = parse_source_name("votacao_pln_12_2026.txt")
    assert f1.type == "Câmara dos Deputados"
    assert f1.label == "Histórico de Votação"

    # TSE Bens
    f2 = parse_source_name("tse_bens_declaracao_2026.pdf")
    assert f2.type == "TSE - DivulgaCand"
    assert f2.label == "Declaração de Bens"

    # Noticia Web
    f3 = parse_source_name("https://g1.globo.com/politica/noticia/2026/orcamento.ghtml")
    assert f3.type == "Notícia Web (DuckDuckGo)"
    assert "Web: g1.globo.com" in f3.label

    # CGU Transparencia
    f4 = parse_source_name("transparencia_cgu_gastos.json")
    assert f4.type == "Portal da Transparência (CGU)"
    assert f4.label == "Execução Orçamentária"

    # Fact-checking
    f5 = parse_source_name("lupa_checagem_fatos_eleicoes.html")
    assert f5.type == "Agência de Fact-Checking"
    assert f5.label == "Checagem de Fatos"

def test_cache_business_rules():
    """Valida regra de cache RAGQueryCache: normalizacao de chaves e eviction."""
    cache = RAGQueryCache(ttl_seconds=300, max_size=2)

    # Chaves normalizadas (espacos e caixa alta) devem bater no mesmo registro
    cache.set("   QUAIS AS LEIS DA  SAUDE?  ", {"answer": "Lei 8080", "sources": []}, model_name="gemini-2.0-flash")
    cached = cache.get("quais as leis da saude?", model_name="gemini-2.0-flash")

    assert cached is not None
    assert cached["answer"] == "Lei 8080"

    # Eviction FIFO quando atinge max_size=2
    cache.set("query 2", {"answer": "ans 2", "sources": []})
    cache.set("query 3", {"answer": "ans 3", "sources": []})

    # "quais as leis da saude?" deve ter sido removido por ser o mais antigo
    assert cache.get("quais as leis da saude?", model_name="gemini-2.0-flash") is None
    assert cache.get("query 3") is not None

def test_hybrid_retriever_rrf_scoring():
    """Valida fusao RRF (Reciprocal Rank Fusion) no Retriever Hibrido."""
    doc1 = Document(page_content="Votação da PEC do orçamento da saúde", metadata={"source": "camara_pec.txt"})
    doc2 = Document(page_content="Declaração de bens do candidato no TSE", metadata={"source": "tse_bens.pdf"})

    class MockDenseRetriever:
        def invoke(self, query):
            return [doc1, doc2]

    retriever = HybridRetriever(dense_retriever=MockDenseRetriever(), documents=[doc1, doc2], k_dense=2, k_bm25=2)
    docs = retriever.invoke("orçamento da saúde")

    assert len(docs) > 0
    assert docs[0].page_content == doc1.page_content

def test_analytics_business_rules():
    """Valida regras de negocio do Analytics: carregamento de sugestoes curiosas."""
    record_query("query teste")
    suggestions = get_top_suggestions(limit=4)
    assert len(suggestions) <= 4
    assert "prompt" in suggestions[0]
