import asyncio
import logging
import uuid
from typing import Dict, Any, Optional

class AsyncIngestionWorker:
    """Worker assíncrono para processar lote de ingestão de documentos sem bloquear a API principal."""

    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._worker_task: Optional[asyncio.Task] = None

    def start(self):
        if not self._worker_task or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._process_queue())
            logging.info("Worker assíncrono de ingestão iniciado.")

    async def enqueue_job(self, doc_data: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        job_info = {
            "job_id": job_id,
            "status": "pending",
            "data": doc_data,
            "error": None
        }
        self.jobs[job_id] = job_info
        await self.queue.put(job_id)
        logging.info(f"Job {job_id} enfileirado para ingestão assíncrona.")
        return job_id

    async def _process_queue(self):
        while True:
            job_id = await self.queue.get()
            job = self.jobs.get(job_id)
            if not job:
                self.queue.task_done()
                continue

            try:
                job["status"] = "processing"
                logging.info(f"Processando job de ingestão {job_id}...")
                
                # Simula etapa de extração, chunking e vetorização assíncrona
                await asyncio.sleep(0.5)
                
                job["status"] = "completed"
                logging.info(f"Job de ingestão {job_id} concluído com sucesso.")
            except Exception as e:
                logging.error(f"Erro ao processar job {job_id}: {e}")
                job["status"] = "failed"
                job["error"] = str(e)
            finally:
                self.queue.task_done()

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)

global_ingestion_worker = AsyncIngestionWorker()
