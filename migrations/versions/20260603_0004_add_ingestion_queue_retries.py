"""Add durable ingestion queue retry fields.

Revision ID: 20260603_0004
Revises: 20260601_0003
Create Date: 2026-06-03
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260603_0004"
down_revision: str | None = "20260601_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS raw_storage_path TEXT")
    op.execute(
        "ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS attempts INTEGER NOT NULL DEFAULT 0"
    )
    op.execute(
        "ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS max_attempts INTEGER NOT NULL DEFAULT 3"
    )
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS last_error TEXT")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMP")
    op.execute("ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS finished_at TIMESTAMP")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status_updated_at
        ON ingestion_jobs(status, updated_at)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status_attempts
        ON ingestion_jobs(status, attempts)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ingestion_jobs_status_attempts")
    op.execute("DROP INDEX IF EXISTS idx_ingestion_jobs_status_updated_at")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN IF EXISTS finished_at")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN IF EXISTS started_at")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN IF EXISTS last_error")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN IF EXISTS max_attempts")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN IF EXISTS attempts")
    op.execute("ALTER TABLE ingestion_jobs DROP COLUMN IF EXISTS raw_storage_path")
