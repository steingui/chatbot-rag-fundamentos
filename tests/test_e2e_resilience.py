import unittest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from backend.rag.cache import RAGQueryCache
from backend.rag.llm_fallback import DynamicFallbackLLMManager
from backend.rag.retriever import HybridRetriever
from pipelines.scrapers.scraper_camara import fetch_data, fetch_proposicao_ementa


class TestE2EResilienceAndIntegrity(unittest.TestCase):
    """Testes E2E de resiliência, integração e retrocompatibilidade do pipeline RAG-AI."""

    def test_rag_query_cache_cachetools(self):
        """Valida que o RAGQueryCache utilizando cachetools.TTLCache funciona corretamente."""
        cache = RAGQueryCache(ttl_seconds=10, max_size=2)
        
        # Set & Get
        cache.set("Quem é o presidente?", "Resposta A", model_name="gemini")
        val = cache.get("Quem é o presidente?", model_name="gemini")
        self.assertEqual(val, "Resposta A")

        # Key Normalization Check (ignora maiúsculas e espaços)
        val_normalized = cache.get("  quem É o presidente?  ", model_name="gemini")
        self.assertEqual(val_normalized, "Resposta A")

        # Eviction (Max size = 2)
        cache.set("Pergunta 2", "Resposta B", model_name="gemini")
        cache.set("Pergunta 3", "Resposta C", model_name="gemini")
        
        # Primeira pergunta deve ter sido removida por LRU
        self.assertIsNone(cache.get("Quem é o presidente?", model_name="gemini"))
        self.assertEqual(cache.get("Pergunta 3", model_name="gemini"), "Resposta C")

        # Clear
        cache.clear()
        self.assertIsNone(cache.get("Pergunta 3", model_name="gemini"))

    def test_dynamic_fallback_llm_manager_with_fallbacks(self):
        """Valida se o DynamicFallbackLLMManager instancia resiliência via with_fallbacks do LangChain."""
        manager = DynamicFallbackLLMManager(primary_model="model-1")
        chain = manager.get_resilient_chain()
        self.assertIsNotNone(chain)

    def test_hybrid_retriever_tokenization_and_weighted_rrf(self):
        """Valida tokenização acentuada e fusão de relevância RRF no HybridRetriever."""
        doc1 = Document(page_content="Votação sobre orçamento da educação pública federal")
        doc2 = Document(page_content="Emenda constitucional sobre transporte escolar")
        doc3 = Document(page_content="Lei de diretrizes tributárias estaduais")

        mock_dense = MagicMock()
        mock_dense.invoke.return_value = [doc1, doc2]

        retriever = HybridRetriever(dense_retriever=mock_dense, documents=[doc1, doc2, doc3])
        
        # Testar tokenização com acento "educação" -> "educacao"
        results = retriever.invoke("educação pública")
        self.assertTrue(len(results) > 0)
        self.assertEqual(results[0].page_content, doc1.page_content)

    @patch("pipelines.scrapers.scraper_camara._session.get")
    def test_scraper_tenacity_retry(self, mock_get):
        """Valida se os decoradores do tenacity executam com sucesso no scraper_camara."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"dados": [{"id": 1, "nome": "Votação Teste"}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        dados = fetch_data("votacoes")
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]["nome"], "Votação Teste")


if __name__ == "__main__":
    unittest.main()
