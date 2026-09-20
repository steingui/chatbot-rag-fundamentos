import pytest
import asyncio
from backend.workers.ingestion_worker import AsyncIngestionWorker


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
