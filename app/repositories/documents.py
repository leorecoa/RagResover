import json
from dataclasses import dataclass
from datetime import datetime
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


@dataclass(frozen=True)
class DocumentRecord:
    id: UUID
    tenant_id: str
    file_name: str
    content_type: str
    file_size: int
    chunks_count: int
    created_at: datetime
    metadata: dict[str, Any]


@dataclass(frozen=True)
class DocumentChunkRecord:
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    metadata: dict[str, Any]
    created_at: datetime


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

    @staticmethod
    def _document_from_row(row) -> DocumentRecord:
        return DocumentRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            file_name=row["file_name"],
            content_type=row["content_type"],
            file_size=int(row["file_size"]),
            chunks_count=int(row["chunks_count"]),
            created_at=row["created_at"],
            metadata=normalize_metadata(row["metadata"]),
        )

    @staticmethod
    def _chunk_from_row(row) -> DocumentChunkRecord:
        return DocumentChunkRecord(
            id=row["id"],
            document_id=row["document_id"],
            chunk_index=int(row["chunk_index"]),
            content=row["content"],
            metadata=normalize_metadata(row["metadata"]),
            created_at=row["created_at"],
        )

    async def list_documents(
        self,
        *,
        tenant_id: str,
        source: str | None = None,
        content_type: str | None = None,
    ) -> list[DocumentRecord]:
        result = await self.session.execute(
            text(
                """
                SELECT
                    sd.id,
                    sd.tenant_id,
                    sd.file_name,
                    sd.content_type,
                    sd.file_size,
                    sd.created_at,
                    sd.metadata,
                    COUNT(dc.id)::int AS chunks_count
                FROM source_documents sd
                LEFT JOIN document_chunks dc
                    ON dc.source_document_id = sd.id
                    AND dc.tenant_id = :tenant_id
                WHERE
                    sd.tenant_id = :tenant_id
                    AND (
                        :source IS NULL
                        OR sd.file_name ILIKE '%' || :source || '%'
                        OR sd.metadata ->> 'source' ILIKE '%' || :source || '%'
                    )
                    AND (
                        :content_type IS NULL
                        OR sd.content_type = :content_type
                    )
                GROUP BY
                    sd.id,
                    sd.tenant_id,
                    sd.file_name,
                    sd.content_type,
                    sd.file_size,
                    sd.created_at,
                    sd.metadata
                ORDER BY sd.created_at DESC
                """
            ),
            {
                "tenant_id": tenant_id,
                "source": source.strip() if source and source.strip() else None,
                "content_type": (
                    content_type.strip() if content_type and content_type.strip() else None
                ),
            },
        )
        return [self._document_from_row(row) for row in result.mappings().all()]

    async def get_document(
        self,
        *,
        tenant_id: str,
        document_id: UUID,
    ) -> DocumentRecord | None:
        result = await self.session.execute(
            text(
                """
                SELECT
                    sd.id,
                    sd.tenant_id,
                    sd.file_name,
                    sd.content_type,
                    sd.file_size,
                    sd.created_at,
                    sd.metadata,
                    COUNT(dc.id)::int AS chunks_count
                FROM source_documents sd
                LEFT JOIN document_chunks dc
                    ON dc.source_document_id = sd.id
                    AND dc.tenant_id = :tenant_id
                WHERE
                    sd.id = :document_id
                    AND sd.tenant_id = :tenant_id
                GROUP BY
                    sd.id,
                    sd.tenant_id,
                    sd.file_name,
                    sd.content_type,
                    sd.file_size,
                    sd.created_at,
                    sd.metadata
                """
            ),
            {"tenant_id": tenant_id, "document_id": document_id},
        )
        row = result.mappings().first()
        return self._document_from_row(row) if row else None

    async def count_document_chunks(
        self,
        *,
        tenant_id: str,
        document_id: UUID,
    ) -> int:
        result = await self.session.execute(
            text(
                """
                SELECT COUNT(dc.id)::int
                FROM document_chunks dc
                JOIN source_documents sd ON sd.id = dc.source_document_id
                WHERE
                    dc.source_document_id = :document_id
                    AND dc.tenant_id = :tenant_id
                    AND sd.tenant_id = :tenant_id
                """
            ),
            {"tenant_id": tenant_id, "document_id": document_id},
        )
        return int(result.scalar_one())

    async def list_document_chunks(
        self,
        *,
        tenant_id: str,
        document_id: UUID,
        limit: int,
        offset: int,
    ) -> list[DocumentChunkRecord]:
        result = await self.session.execute(
            text(
                """
                SELECT
                    dc.id,
                    dc.source_document_id AS document_id,
                    dc.chunk_index,
                    dc.content,
                    dc.metadata,
                    dc.created_at
                FROM document_chunks dc
                JOIN source_documents sd ON sd.id = dc.source_document_id
                WHERE
                    dc.source_document_id = :document_id
                    AND dc.tenant_id = :tenant_id
                    AND sd.tenant_id = :tenant_id
                ORDER BY dc.chunk_index ASC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {
                "tenant_id": tenant_id,
                "document_id": document_id,
                "limit": int(limit),
                "offset": int(offset),
            },
        )
        return [self._chunk_from_row(row) for row in result.mappings().all()]

    async def delete_document(
        self,
        *,
        tenant_id: str,
        document_id: UUID,
    ) -> bool:
        try:
            result = await self.session.execute(
                text(
                    """
                    DELETE FROM source_documents
                    WHERE id = :document_id
                    AND tenant_id = :tenant_id
                    RETURNING id
                    """
                ),
                {"tenant_id": tenant_id, "document_id": document_id},
            )
            deleted_id = result.scalar_one_or_none()
            if deleted_id is None:
                await self.session.rollback()
                return False
            await self.session.commit()
            return True
        except Exception:
            await self.session.rollback()
            raise

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
        normalized_score_threshold = (
            None if score_threshold is None else float(score_threshold)
        )

        serialized_metadata_filters = (
            json.dumps(metadata_filters)
            if metadata_filters
            else None
        )

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
                        CAST(:score_threshold AS DOUBLE PRECISION) IS NULL
                        OR 1 - (dc.embedding <=> CAST(:embedding AS vector)) >= CAST(:score_threshold AS DOUBLE PRECISION)
                    )
                    AND (
                        CAST(:metadata_filters AS jsonb) IS NULL
                        OR dc.metadata @> CAST(:metadata_filters AS jsonb)
                    )
                ORDER BY dc.embedding <=> CAST(:embedding AS vector)
                LIMIT :limit
                """
            ),
            {
                "tenant_id": tenant_id,
                "embedding": serialize_vector(embedding),
                "limit": int(limit),
                "score_threshold": normalized_score_threshold,
                "metadata_filters": serialized_metadata_filters,
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
