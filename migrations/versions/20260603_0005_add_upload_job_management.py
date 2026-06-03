"""Add upload job management status.

Revision ID: 20260603_0005
Revises: 20260603_0004
Create Date: 2026-06-03
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260603_0005"
down_revision: str | None = "20260603_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE ingestion_jobs DROP CONSTRAINT IF EXISTS ingestion_jobs_status_check")
    op.execute(
        """
        ALTER TABLE ingestion_jobs
        ADD CONSTRAINT ingestion_jobs_status_check
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'canceled'))
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE ingestion_jobs
        SET
            status = 'failed',
            error_message = COALESCE(error_message, 'Upload cancelado.'),
            last_error = COALESCE(last_error, 'Upload cancelado.')
        WHERE status = 'canceled'
        """
    )
    op.execute("ALTER TABLE ingestion_jobs DROP CONSTRAINT IF EXISTS ingestion_jobs_status_check")
    op.execute(
        """
        ALTER TABLE ingestion_jobs
        ADD CONSTRAINT ingestion_jobs_status_check
        CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
        """
    )
