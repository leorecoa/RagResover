import logging
from uuid import UUID

from app.db.session import AsyncSessionLocal
from app.repositories.documents import DocumentRepository
from app.repositories.ingestion_jobs import IngestionJobRepository
from app.services.embeddings import embedding_service
from app.services.ingestion import ingestion_service

logger = logging.getLogger("rag_resover")


async def process_upload_job(
    *,
    job_id: UUID,
    tenant_id: str,
    file_name: str,
    file_bytes: bytes,
    content_type: str,
) -> None:
    async with AsyncSessionLocal() as session:
        jobs = IngestionJobRepository(session)
        started = await jobs.update_status(job_id=job_id, status="processing")
        if started is None:
            logger.warning("Ingestion job %s not found before processing.", job_id)
            return

        try:
            ingestion_result = await ingestion_service.ingest_raw_file(
                file_name=file_name,
                file_bytes=file_bytes,
                content_type=content_type,
            )
            embeddings = await embedding_service.embed_texts(
                [chunk.page_content for chunk in ingestion_result.chunks]
            )
            persisted = await DocumentRepository(session).persist_ingestion(
                file_name=file_name,
                content_type=content_type,
                file_size=ingestion_result.file_size,
                storage_path=ingestion_result.storage_path,
                chunks=ingestion_result.chunks,
                embeddings=embeddings,
                tenant_id=tenant_id,
            )
            await jobs.update_status(
                job_id=job_id,
                status="completed",
                document_id=persisted.document_id,
                error_message=None,
            )
        except Exception as exc:
            logger.exception("Erro ao processar ingestion job %s", job_id)
            await jobs.update_status(
                job_id=job_id,
                status="failed",
                error_message=str(exc),
            )
