from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


IngestionJobStatus = Literal["pending", "processing", "completed", "failed"]


@dataclass(frozen=True)
class IngestionJobRecord:
    id: UUID
    tenant_id: str
    file_name: str
    content_type: str
    file_size: int
    status: IngestionJobStatus
    error_message: str | None
    document_id: UUID | None
    created_at: datetime
    updated_at: datetime


class IngestionJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _job_from_row(row) -> IngestionJobRecord:
        return IngestionJobRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            file_name=row["file_name"],
            content_type=row["content_type"],
            file_size=int(row["file_size"]),
            status=row["status"],
            error_message=row["error_message"],
            document_id=row["document_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def create_job(
        self,
        *,
        tenant_id: str,
        file_name: str,
        content_type: str,
        file_size: int,
    ) -> IngestionJobRecord:
        result = await self.session.execute(
            text(
                """
                INSERT INTO ingestion_jobs (
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    status
                )
                VALUES (
                    :tenant_id,
                    :file_name,
                    :content_type,
                    :file_size,
                    'pending'
                )
                RETURNING
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    status,
                    error_message,
                    document_id,
                    created_at,
                    updated_at
                """
            ),
            {
                "tenant_id": tenant_id,
                "file_name": file_name,
                "content_type": content_type,
                "file_size": int(file_size),
            },
        )
        await self.session.commit()
        return self._job_from_row(result.mappings().one())

    async def list_jobs(self, *, tenant_id: str, limit: int = 50) -> list[IngestionJobRecord]:
        result = await self.session.execute(
            text(
                """
                SELECT
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    status,
                    error_message,
                    document_id,
                    created_at,
                    updated_at
                FROM ingestion_jobs
                WHERE tenant_id = :tenant_id
                ORDER BY created_at DESC
                LIMIT :limit
                """
            ),
            {"tenant_id": tenant_id, "limit": int(limit)},
        )
        return [self._job_from_row(row) for row in result.mappings().all()]

    async def get_job(
        self,
        *,
        tenant_id: str,
        job_id: UUID,
    ) -> IngestionJobRecord | None:
        result = await self.session.execute(
            text(
                """
                SELECT
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    status,
                    error_message,
                    document_id,
                    created_at,
                    updated_at
                FROM ingestion_jobs
                WHERE id = :job_id
                AND tenant_id = :tenant_id
                """
            ),
            {"tenant_id": tenant_id, "job_id": job_id},
        )
        row = result.mappings().first()
        return self._job_from_row(row) if row else None

    async def update_status(
        self,
        *,
        job_id: UUID,
        status: IngestionJobStatus,
        document_id: UUID | None = None,
        error_message: str | None = None,
    ) -> IngestionJobRecord | None:
        result = await self.session.execute(
            text(
                """
                UPDATE ingestion_jobs
                SET
                    status = :status,
                    document_id = COALESCE(:document_id, document_id),
                    error_message = :error_message,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :job_id
                RETURNING
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    status,
                    error_message,
                    document_id,
                    created_at,
                    updated_at
                """
            ),
            {
                "job_id": job_id,
                "status": status,
                "document_id": document_id,
                "error_message": error_message,
            },
        )
        row = result.mappings().first()
        if row is None:
            await self.session.rollback()
            return None
        await self.session.commit()
        return self._job_from_row(row)
