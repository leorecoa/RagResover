from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import TenantContext, get_tenant_context
from app.api.schemas.documents import (
    DeleteDocumentResponse,
    DocumentChunksResponse,
    DocumentDetailResponse,
    DocumentListResponse,
)
from app.db.session import get_db_session
from app.repositories.documents import DocumentChunkRecord, DocumentRecord, DocumentRepository

router = APIRouter(tags=["Documents"])


def document_payload(document: DocumentRecord) -> dict:
    return {
        "id": str(document.id),
        "file_name": document.file_name,
        "content_type": document.content_type,
        "file_size": document.file_size,
        "chunks_count": document.chunks_count,
        "tenant_id": document.tenant_id,
        "created_at": document.created_at,
        "metadata": document.metadata,
    }


def chunk_payload(chunk: DocumentChunkRecord) -> dict:
    return {
        "id": str(chunk.id),
        "document_id": str(chunk.document_id),
        "chunk_index": chunk.chunk_index,
        "content": chunk.content,
        "metadata": chunk.metadata,
        "created_at": chunk.created_at,
    }


def parse_document_id(document_id: str) -> UUID:
    try:
        return UUID(document_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento nao encontrado.",
        ) from exc


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    source: str | None = Query(default=None),
    content_type: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    documents = await DocumentRepository(session).list_documents(
        tenant_id=tenant.tenant_id,
        source=source,
        content_type=content_type,
    )
    return {"documents": [document_payload(document) for document in documents]}


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    session: AsyncSession = Depends(get_db_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    document = await DocumentRepository(session).get_document(
        tenant_id=tenant.tenant_id,
        document_id=parse_document_id(document_id),
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento nao encontrado.",
        )
    return document_payload(document)


@router.get("/documents/{document_id}/chunks", response_model=DocumentChunksResponse)
async def list_document_chunks(
    document_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    parsed_document_id = parse_document_id(document_id)
    repository = DocumentRepository(session)
    document = await repository.get_document(
        tenant_id=tenant.tenant_id,
        document_id=parsed_document_id,
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento nao encontrado.",
        )

    offset = (page - 1) * page_size
    total = await repository.count_document_chunks(
        tenant_id=tenant.tenant_id,
        document_id=parsed_document_id,
    )
    chunks = await repository.list_document_chunks(
        tenant_id=tenant.tenant_id,
        document_id=parsed_document_id,
        limit=page_size,
        offset=offset,
    )
    return {
        "document_id": str(parsed_document_id),
        "page": page,
        "page_size": page_size,
        "total": total,
        "chunks": [chunk_payload(chunk) for chunk in chunks],
    }


@router.delete("/documents/{document_id}", response_model=DeleteDocumentResponse)
async def delete_document(
    document_id: str,
    session: AsyncSession = Depends(get_db_session),
    tenant: TenantContext = Depends(get_tenant_context),
):
    parsed_document_id = parse_document_id(document_id)
    deleted = await DocumentRepository(session).delete_document(
        tenant_id=tenant.tenant_id,
        document_id=parsed_document_id,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento nao encontrado.",
        )
    return {
        "document_id": str(parsed_document_id),
        "status": "deleted",
        "message": "Documento e chunks removidos.",
    }
