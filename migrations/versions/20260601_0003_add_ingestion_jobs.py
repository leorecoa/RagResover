"""Add ingestion jobs for async uploads.

Revision ID: 20260601_0003
Revises: 20260601_0002
Create Date: 2026-06-03
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260601_0003"
down_revision: str | None = "20260601_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS ingestion_jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(128) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            content_type VARCHAR(100) NOT NULL,
            file_size BIGINT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            error_message TEXT,
            document_id UUID REFERENCES source_documents(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT ingestion_jobs_status_check
                CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_tenant_id
        ON ingestion_jobs(tenant_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_tenant_created_at
        ON ingestion_jobs(tenant_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_tenant_status
        ON ingestion_jobs(tenant_id, status)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_ingestion_jobs_tenant_status")
    op.execute("DROP INDEX IF EXISTS idx_ingestion_jobs_tenant_created_at")
    op.execute("DROP INDEX IF EXISTS idx_ingestion_jobs_tenant_id")
    op.execute("DROP TABLE IF EXISTS ingestion_jobs")
