import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.ingestion import UploadResponse
from app.core.config import settings
from app.db.session import get_db_session
from app.repositories.documents import DocumentRepository
from app.services.embeddings import embedding_service
from app.services.ingestion import ingestion_service

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


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
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
        )

        return {
            "document_id": str(persisted.document_id),
            "filename": file_name,
            "status": "success",
            "chunks_count": persisted.chunks_count,
            "message": "Documento processado e pronto para indexacao.",
        }
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
