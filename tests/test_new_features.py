import pytest
import asyncio
from langchain_core.documents import Document
from backend.rag.retriever import HybridRetriever
from backend.workers.ingestion_worker import AsyncIngestionWorker
from backend.rag.llm_fallback import DynamicFallbackLLMManager

class MockDenseRetriever:
    def invoke(self, query: str):
        return [Document(page_content="PEC 45 reforma tributaria aprovada em 2023", metadata={"source": "camara"})]

def test_hybrid_retriever_fusion():
    mock_dense = MockDenseRetriever()
    docs = [
        Document(page_content="PEC 45 reforma tributaria aprovada em 2023", metadata={"source": "camara"}),
        Document(page_content="Votacao do arcabouco fiscal pelo senado", metadata={"source": "senado"})
    ]
    retriever = HybridRetriever(dense_retriever=mock_dense, documents=docs, k_dense=2, k_bm25=2)
    results = retriever.get_relevant_documents("reforma tributaria")
    
    assert len(results) > 0
    assert "reforma tributaria" in results[0].page_content.lower()

@pytest.mark.asyncio
async def test_async_ingestion_worker():
    worker = AsyncIngestionWorker()
    worker.start()
    
    job_id = await worker.enqueue_job({"title": "Doc Teste", "content": "Conteudo legislativo"})
    assert job_id is not None
    
    # Aguarda processamento do worker
    await asyncio.sleep(0.7)
    
    status = worker.get_job_status(job_id)
    assert status is not None
    assert status["status"] == "completed"

def test_dynamic_fallback_llm_instantiation():
    manager = DynamicFallbackLLMManager()
    assert manager.primary_model is not None
    assert len(manager.fallback_models) > 0
