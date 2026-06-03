import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import TenantContext, get_tenant_context
from app.api.schemas.ingestion import UploadJobListResponse, UploadJobResponse, UploadResponse
from app.core.config import settings
from app.db.session import get_db_session
from app.repositories.ingestion_jobs import IngestionJobRecord, IngestionJobRepository
from app.services.ingestion_queue import get_ingestion_queue
from app.services.storage import storage_service

logger = logging.getLogger("rag_resover")
router = APIRouter(tags=["Ingestion"])


def normalize_content_type(content_type: str | None) -> str:
    return (content_type or "application/octet-stream").split(";", 1)[0].strip().lower()


def validate_upload(file: UploadFile) -> tuple[str, str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome do arquivo nao fornecido.")

    content_type = normalize_content_type(file.content_type)
    if content_type not in settings.allowed_upload_content_types:
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de arquivo nao suportado: {content_type}",
        )

    return file.filename, content_type


def upload_job_payload(job: IngestionJobRecord, message: str | None = None) -> dict:
    return {
        "job_id": str(job.id),
        "filename": job.file_name,
        "content_type": job.content_type,
        "file_size": job.file_size,
        "status": job.status,
        "tenant_id": job.tenant_id,
        "error_message": job.error_message,
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
        "last_error": job.last_error,
        "document_id": str(job.document_id) if job.document_id else None,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "message": message or "Upload recebido para processamento.",
    }


def parse_job_id(job_id: str) -> UUID:
    try:
        return UUID(job_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload job nao encontrado.",
        ) from exc


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    file_name, content_type = validate_upload(file)
    logger.info("Recebendo arquivo: %s (%s)", file_name, content_type)

    try:
        file_bytes = await file.read(settings.MAX_UPLOAD_BYTES + 1)
        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="Arquivo vazio nao pode ser processado.",
            )
        if len(file_bytes) > settings.MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Arquivo excede o tamanho maximo permitido.",
            )

        raw_storage_path = await storage_service.upload_file(
            file_name,
            file_bytes,
            content_type,
        )
        jobs = IngestionJobRepository(session)
        job = await jobs.create_job(
            tenant_id=tenant.tenant_id,
            file_name=file_name,
            content_type=content_type,
            file_size=len(file_bytes),
            raw_storage_path=raw_storage_path,
            max_attempts=settings.INGESTION_JOB_MAX_ATTEMPTS,
        )
        try:
            await get_ingestion_queue().enqueue(job.id)
        except Exception as exc:
            logger.exception("Erro ao enfileirar upload job %s", job.id)
            await jobs.fail_job(
                job_id=job.id,
                error_message=f"Fila de ingestao indisponivel: {exc}",
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Fila de ingestao indisponivel.",
            ) from exc

        return upload_job_payload(job)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Erro ao processar upload %s", file_name)
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao processar o documento.",
        ) from None
    finally:
        await file.close()


@router.get("/uploads", response_model=UploadJobListResponse)
async def list_upload_jobs(
    limit: int = Query(default=50, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    jobs = await IngestionJobRepository(session).list_jobs(
        tenant_id=tenant.tenant_id,
        limit=limit,
    )
    return {"uploads": [upload_job_payload(job) for job in jobs]}


@router.get("/uploads/{job_id}", response_model=UploadJobResponse)
async def get_upload_job(
    job_id: str,
    session: AsyncSession = Depends(get_db_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    job = await IngestionJobRepository(session).get_job(
        tenant_id=tenant.tenant_id,
        job_id=parse_job_id(job_id),
    )
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload job nao encontrado.",
        )
    return upload_job_payload(job)
