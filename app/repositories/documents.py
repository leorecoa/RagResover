import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from langchain_core.documents import Document
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class PersistedIngestion:
    document_id: UUID
    chunks_count: int


@dataclass(frozen=True)
class SearchResult:
    chunk_id: UUID
    document_id: UUID
    tenant_id: str
    file_name: str
    content: str
    score: float
    metadata: dict[str, Any]


def serialize_vector(vector: list[float] | None) -> str | None:
    if vector is None:
        return None
    return "[" + ",".join(str(value) for value in vector) + "]"


def normalize_metadata(metadata: Any) -> dict[str, Any]:
    if isinstance(metadata, dict):
        return metadata
    if isinstance(metadata, str):
        try:
            parsed = json.loads(metadata)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_source_document(
        self,
        *,
        title: str,
        file_name: str,
        content_type: str,
        file_size: int,
        storage_path: str,
        metadata: dict[str, Any],
        tenant_id: str,
    ) -> UUID:
        result = await self.session.execute(
            text(
                """
                INSERT INTO source_documents (
                    tenant_id,
                    title,
                    file_name,
                    content_type,
                    file_size,
                    storage_path,
                    metadata
                )
                VALUES (
                    :tenant_id,
                    :title,
                    :file_name,
                    :content_type,
                    :file_size,
                    :storage_path,
                    CAST(:metadata AS jsonb)
                )
                RETURNING id
                """
            ),
            {
                "tenant_id": tenant_id,
                "title": title,
                "file_name": file_name,
                "content_type": content_type,
                "file_size": file_size,
                "storage_path": storage_path,
                "metadata": json.dumps(metadata),
            },
        )
        return result.scalar_one()

    async def create_chunks(
        self,
        *,
        document_id: UUID,
        tenant_id: str,
        chunks: list[Document],
        embeddings: list[list[float] | None],
    ) -> None:
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")

        await self.session.execute(
            text(
                """
                INSERT INTO document_chunks (
                    source_document_id,
                    tenant_id,
                    chunk_index,
                    content,
                    metadata,
                    embedding
                )
                VALUES (
                    :source_document_id,
                    :tenant_id,
                    :chunk_index,
                    :content,
                    CAST(:metadata AS jsonb),
                    CAST(:embedding AS vector)
                )
                """
            ),
            [
                {
                    "source_document_id": document_id,
                    "tenant_id": tenant_id,
                    "chunk_index": index,
                    "content": chunk.page_content,
                    "metadata": json.dumps(chunk.metadata),
                    "embedding": serialize_vector(embeddings[index]),
                }
                for index, chunk in enumerate(chunks)
            ],
        )

    async def persist_ingestion(
        self,
        *,
        file_name: str,
        content_type: str,
        file_size: int,
        storage_path: str,
        chunks: list[Document],
        embeddings: list[list[float] | None],
        tenant_id: str,
    ) -> PersistedIngestion:
        try:
            document_id = await self.create_source_document(
                title=file_name,
                file_name=file_name,
                content_type=content_type,
                file_size=file_size,
                storage_path=storage_path,
                metadata={"source": file_name, "tenant_id": tenant_id},
                tenant_id=tenant_id,
            )
            await self.create_chunks(
                document_id=document_id,
                tenant_id=tenant_id,
                chunks=chunks,
                embeddings=embeddings,
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

        return PersistedIngestion(
            document_id=document_id,
            chunks_count=len(chunks),
        )

    async def search_similar_chunks(
        self,
        *,
        tenant_id: str,
        embedding: list[float],
        limit: int,
        score_threshold: float | None = None,
        metadata_filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        result = await self.session.execute(
            text(
                """
                SELECT
                    dc.id AS chunk_id,
                    dc.source_document_id AS document_id,
                    dc.tenant_id,
                    sd.file_name,
                    dc.content,
                    dc.metadata,
                    1 - (dc.embedding <=> CAST(:embedding AS vector)) AS score
                FROM document_chunks dc
                JOIN source_documents sd ON sd.id = dc.source_document_id
                WHERE
                    dc.embedding IS NOT NULL
                    AND dc.tenant_id = :tenant_id
                    AND sd.tenant_id = :tenant_id
                    AND (
                        :score_threshold IS NULL
                        OR 1 - (dc.embedding <=> CAST(:embedding AS vector)) >= :score_threshold
                    )
                    AND (
                        :metadata_filters IS NULL
                        OR dc.metadata @> CAST(:metadata_filters AS jsonb)
                    )
                ORDER BY dc.embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
                """
            ),
            {
                "tenant_id": tenant_id,
                "embedding": serialize_vector(embedding),
                "limit": limit,
                "score_threshold": score_threshold,
                "metadata_filters": (
                    json.dumps(metadata_filters)
                    if metadata_filters
                    else None
                ),
            },
        )
        rows = result.mappings().all()
        return [
            SearchResult(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                tenant_id=row["tenant_id"],
                file_name=row["file_name"],
                content=row["content"],
                score=float(row["score"]),
                metadata=normalize_metadata(row["metadata"]),
            )
            for row in rows
        ]
