from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


IngestionJobStatus = Literal["pending", "processing", "completed", "failed", "canceled"]


@dataclass(frozen=True)
class IngestionJobRecord:
    id: UUID
    tenant_id: str
    file_name: str
    content_type: str
    file_size: int
    raw_storage_path: str | None
    status: IngestionJobStatus
    error_message: str | None
    attempts: int
    max_attempts: int
    last_error: str | None
    document_id: UUID | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


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
            raw_storage_path=row["raw_storage_path"],
            status=row["status"],
            error_message=row["error_message"],
            attempts=int(row["attempts"]),
            max_attempts=int(row["max_attempts"]),
            last_error=row["last_error"],
            document_id=row["document_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
        )

    async def create_job(
        self,
        *,
        tenant_id: str,
        file_name: str,
        content_type: str,
        file_size: int,
        raw_storage_path: str | None,
        max_attempts: int,
    ) -> IngestionJobRecord:
        result = await self.session.execute(
            text(
                """
                INSERT INTO ingestion_jobs (
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    raw_storage_path,
                    max_attempts,
                    status
                )
                VALUES (
                    :tenant_id,
                    :file_name,
                    :content_type,
                    :file_size,
                    :raw_storage_path,
                    :max_attempts,
                    'pending'
                )
                RETURNING
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    raw_storage_path,
                    status,
                    error_message,
                    attempts,
                    max_attempts,
                    last_error,
                    document_id,
                    created_at,
                    updated_at,
                    started_at,
                    finished_at
                """
            ),
            {
                "tenant_id": tenant_id,
                "file_name": file_name,
                "content_type": content_type,
                "file_size": int(file_size),
                "raw_storage_path": raw_storage_path,
                "max_attempts": int(max_attempts),
            },
        )
        await self.session.commit()
        return self._job_from_row(result.mappings().one())

    async def list_jobs(
        self,
        *,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
        status: IngestionJobStatus | None = None,
        filename: str | None = None,
        content_type: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        document_id: UUID | None = None,
    ) -> list[IngestionJobRecord]:
        where_clauses = ["tenant_id = :tenant_id"]
        params: dict[str, object] = {
            "tenant_id": tenant_id,
            "limit": int(limit),
            "offset": int(offset),
        }

        if status:
            where_clauses.append("status = :status")
            params["status"] = status
        if filename and filename.strip():
            where_clauses.append("file_name ILIKE :filename")
            params["filename"] = f"%{filename.strip()}%"
        if content_type and content_type.strip():
            where_clauses.append("content_type = :content_type")
            params["content_type"] = content_type.strip()
        if created_from is not None:
            where_clauses.append("created_at >= :created_from")
            params["created_from"] = created_from
        if created_to is not None:
            where_clauses.append("created_at <= :created_to")
            params["created_to"] = created_to
        if document_id is not None:
            where_clauses.append("document_id = :document_id")
            params["document_id"] = document_id

        result = await self.session.execute(
            text(
                f"""
                SELECT
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    raw_storage_path,
                    status,
                    error_message,
                    attempts,
                    max_attempts,
                    last_error,
                    document_id,
                    created_at,
                    updated_at,
                    started_at,
                    finished_at
                FROM ingestion_jobs
                WHERE {" AND ".join(where_clauses)}
                ORDER BY created_at DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            params,
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
                    raw_storage_path,
                    status,
                    error_message,
                    attempts,
                    max_attempts,
                    last_error,
                    document_id,
                    created_at,
                    updated_at,
                    started_at,
                    finished_at
                FROM ingestion_jobs
                WHERE id = :job_id
                AND tenant_id = :tenant_id
                """
            ),
            {"tenant_id": tenant_id, "job_id": job_id},
        )
        row = result.mappings().first()
        return self._job_from_row(row) if row else None

    async def get_job_by_id(self, *, job_id: UUID) -> IngestionJobRecord | None:
        result = await self.session.execute(
            text(
                """
                SELECT
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    raw_storage_path,
                    status,
                    error_message,
                    attempts,
                    max_attempts,
                    last_error,
                    document_id,
                    created_at,
                    updated_at,
                    started_at,
                    finished_at
                FROM ingestion_jobs
                WHERE id = :job_id
                """
            ),
            {"job_id": job_id},
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
                    raw_storage_path,
                    status,
                    error_message,
                    attempts,
                    max_attempts,
                    last_error,
                    document_id,
                    created_at,
                    updated_at,
                    started_at,
                    finished_at
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

    async def start_attempt(self, *, job_id: UUID) -> IngestionJobRecord | None:
        result = await self.session.execute(
            text(
                """
                UPDATE ingestion_jobs
                SET
                    status = 'processing',
                    attempts = attempts + 1,
                    error_message = NULL,
                    started_at = CURRENT_TIMESTAMP,
                    finished_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :job_id
                AND status IN ('pending', 'failed')
                AND attempts < max_attempts
                RETURNING
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    raw_storage_path,
                    status,
                    error_message,
                    attempts,
                    max_attempts,
                    last_error,
                    document_id,
                    created_at,
                    updated_at,
                    started_at,
                    finished_at
                """
            ),
            {"job_id": job_id},
        )
        row = result.mappings().first()
        if row is None:
            await self.session.rollback()
            return None
        await self.session.commit()
        return self._job_from_row(row)

    async def complete_job(
        self,
        *,
        job_id: UUID,
        document_id: UUID,
    ) -> IngestionJobRecord | None:
        result = await self.session.execute(
            text(
                """
                UPDATE ingestion_jobs
                SET
                    status = 'completed',
                    document_id = :document_id,
                    error_message = NULL,
                    last_error = NULL,
                    finished_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :job_id
                RETURNING
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    raw_storage_path,
                    status,
                    error_message,
                    attempts,
                    max_attempts,
                    last_error,
                    document_id,
                    created_at,
                    updated_at,
                    started_at,
                    finished_at
                """
            ),
            {"job_id": job_id, "document_id": document_id},
        )
        row = result.mappings().first()
        if row is None:
            await self.session.rollback()
            return None
        await self.session.commit()
        return self._job_from_row(row)

    async def mark_retry_pending(
        self,
        *,
        job_id: UUID,
        error_message: str,
    ) -> IngestionJobRecord | None:
        result = await self.session.execute(
            text(
                """
                UPDATE ingestion_jobs
                SET
                    status = 'pending',
                    error_message = NULL,
                    last_error = :error_message,
                    finished_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :job_id
                RETURNING
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    raw_storage_path,
                    status,
                    error_message,
                    attempts,
                    max_attempts,
                    last_error,
                    document_id,
                    created_at,
                    updated_at,
                    started_at,
                    finished_at
                """
            ),
            {"job_id": job_id, "error_message": error_message},
        )
        row = result.mappings().first()
        if row is None:
            await self.session.rollback()
            return None
        await self.session.commit()
        return self._job_from_row(row)

    async def fail_job(
        self,
        *,
        job_id: UUID,
        error_message: str,
    ) -> IngestionJobRecord | None:
        result = await self.session.execute(
            text(
                """
                UPDATE ingestion_jobs
                SET
                    status = 'failed',
                    error_message = :error_message,
                    last_error = :error_message,
                    finished_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :job_id
                RETURNING
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    raw_storage_path,
                    status,
                    error_message,
                    attempts,
                    max_attempts,
                    last_error,
                    document_id,
                    created_at,
                    updated_at,
                    started_at,
                    finished_at
                """
            ),
            {"job_id": job_id, "error_message": error_message},
        )
        row = result.mappings().first()
        if row is None:
            await self.session.rollback()
            return None
        await self.session.commit()
        return self._job_from_row(row)

    async def retry_failed_job(
        self,
        *,
        tenant_id: str,
        job_id: UUID,
    ) -> IngestionJobRecord | None:
        result = await self.session.execute(
            text(
                """
                UPDATE ingestion_jobs
                SET
                    status = 'pending',
                    attempts = 0,
                    error_message = NULL,
                    last_error = COALESCE(last_error, error_message),
                    started_at = NULL,
                    finished_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :job_id
                AND tenant_id = :tenant_id
                AND status = 'failed'
                RETURNING
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    raw_storage_path,
                    status,
                    error_message,
                    attempts,
                    max_attempts,
                    last_error,
                    document_id,
                    created_at,
                    updated_at,
                    started_at,
                    finished_at
                """
            ),
            {"tenant_id": tenant_id, "job_id": job_id},
        )
        row = result.mappings().first()
        if row is None:
            await self.session.rollback()
            return None
        await self.session.commit()
        return self._job_from_row(row)

    async def cancel_pending_job(
        self,
        *,
        tenant_id: str,
        job_id: UUID,
        reason: str = "Upload cancelado pelo usuario.",
    ) -> IngestionJobRecord | None:
        result = await self.session.execute(
            text(
                """
                UPDATE ingestion_jobs
                SET
                    status = 'canceled',
                    error_message = :reason,
                    last_error = NULL,
                    finished_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :job_id
                AND tenant_id = :tenant_id
                AND status = 'pending'
                RETURNING
                    id,
                    tenant_id,
                    file_name,
                    content_type,
                    file_size,
                    raw_storage_path,
                    status,
                    error_message,
                    attempts,
                    max_attempts,
                    last_error,
                    document_id,
                    created_at,
                    updated_at,
                    started_at,
                    finished_at
                """
            ),
            {"tenant_id": tenant_id, "job_id": job_id, "reason": reason},
        )
        row = result.mappings().first()
        if row is None:
            await self.session.rollback()
            return None
        await self.session.commit()
        return self._job_from_row(row)

    async def fail_stale_processing_jobs(self, *, stale_after_seconds: int) -> int:
        error_message = "Job de ingestao expirou durante processamento."
        result = await self.session.execute(
            text(
                """
                UPDATE ingestion_jobs
                SET
                    status = 'failed',
                    error_message = :error_message,
                    last_error = :error_message,
                    finished_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE status = 'processing'
                AND started_at IS NOT NULL
                AND started_at < CURRENT_TIMESTAMP - (:stale_after_seconds * INTERVAL '1 second')
                RETURNING id
                """
            ),
            {
                "error_message": error_message,
                "stale_after_seconds": int(stale_after_seconds),
            },
        )
        rows = result.mappings().all()
        await self.session.commit()
        return len(rows)
