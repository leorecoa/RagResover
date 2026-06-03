import logging
from uuid import UUID

import anyio

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.repositories.documents import DocumentRepository
from app.repositories.ingestion_jobs import IngestionJobRepository
from app.services.embeddings import embedding_service
from app.services.ingestion import ingestion_service
from app.services.ingestion_queue import IngestionQueue
from app.services.storage import storage_service

logger = logging.getLogger("rag_resover")


async def process_queued_upload_job(*, job_id: UUID, queue: IngestionQueue | None = None) -> None:
    async with AsyncSessionLocal() as session:
        jobs = IngestionJobRepository(session)
        job = await jobs.start_attempt(job_id=job_id)
        if job is None:
            logger.warning("Ingestion job %s not found or not retryable.", job_id)
            return

        try:
            if not job.raw_storage_path:
                raise RuntimeError("Arquivo bruto do upload nao esta disponivel para o worker.")

            file_bytes = await storage_service.download_file(job.raw_storage_path)
            ingestion_result = await ingestion_service.ingest_stored_file(
                file_name=job.file_name,
                file_bytes=file_bytes,
                content_type=job.content_type,
                storage_path=job.raw_storage_path,
            )
            embeddings = await embedding_service.embed_texts(
                [chunk.page_content for chunk in ingestion_result.chunks]
            )
            persisted = await DocumentRepository(session).persist_ingestion(
                file_name=job.file_name,
                content_type=job.content_type,
                file_size=ingestion_result.file_size,
                storage_path=ingestion_result.storage_path,
                chunks=ingestion_result.chunks,
                embeddings=embeddings,
                tenant_id=job.tenant_id,
            )
            await jobs.complete_job(
                job_id=job_id,
                document_id=persisted.document_id,
            )
        except Exception as exc:
            logger.exception("Erro ao processar ingestion job %s", job_id)
            await handle_upload_job_error(
                jobs=jobs,
                queue=queue,
                job_id=job_id,
                attempts=job.attempts,
                max_attempts=job.max_attempts,
                error_message=str(exc),
            )


async def handle_upload_job_error(
    *,
    jobs: IngestionJobRepository,
    queue: IngestionQueue | None,
    job_id: UUID,
    attempts: int,
    max_attempts: int,
    error_message: str,
) -> None:
    if attempts >= max_attempts:
        await jobs.fail_job(job_id=job_id, error_message=error_message)
        return

    retry_job = await jobs.mark_retry_pending(job_id=job_id, error_message=error_message)
    if retry_job is None:
        return

    if settings.INGESTION_RETRY_DELAY_SECONDS:
        await anyio.sleep(settings.INGESTION_RETRY_DELAY_SECONDS)

    if queue is not None:
        await queue.enqueue(job_id)
