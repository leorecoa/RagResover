from datetime import datetime

from pydantic import BaseModel, Field


class DocumentItem(BaseModel):
    id: str
    file_name: str
    content_type: str
    file_size: int
    chunks_count: int
    tenant_id: str
    created_at: datetime
    metadata: dict


class DocumentListResponse(BaseModel):
    documents: list[DocumentItem]


class DocumentDetailResponse(DocumentItem):
    pass


class DocumentChunkItem(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    metadata: dict
    created_at: datetime


class DocumentChunksResponse(BaseModel):
    document_id: str
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    chunks: list[DocumentChunkItem]


class DeleteDocumentResponse(BaseModel):
    document_id: str
    status: str
    message: str
