"""Add tenant isolation columns.

Revision ID: 20260601_0002
Revises: 20260601_0001
Create Date: 2026-06-01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260601_0002"
down_revision: str | None = "20260601_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE source_documents
        ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(128) NOT NULL DEFAULT 'anonymous'
        """
    )
    op.execute(
        """
        ALTER TABLE document_chunks
        ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(128) NOT NULL DEFAULT 'anonymous'
        """
    )
    op.execute(
        """
        ALTER TABLE documents
        ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(128) NOT NULL DEFAULT 'anonymous'
        """
    )
    op.execute(
        """
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(128) NOT NULL DEFAULT 'anonymous'
        """
    )
    op.execute(
        """
        ALTER TABLE messages
        ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(128) NOT NULL DEFAULT 'anonymous'
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_source_documents_tenant_id
        ON source_documents(tenant_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_tenant_id
        ON document_chunks(tenant_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_tenant_source
        ON document_chunks(tenant_id, source_document_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_conversations_tenant_id
        ON conversations(tenant_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_tenant_id
        ON messages(tenant_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_messages_tenant_id")
    op.execute("DROP INDEX IF EXISTS idx_conversations_tenant_id")
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_tenant_source")
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_tenant_id")
    op.execute("DROP INDEX IF EXISTS idx_source_documents_tenant_id")
    op.execute("ALTER TABLE messages DROP COLUMN IF EXISTS tenant_id")
    op.execute("ALTER TABLE conversations DROP COLUMN IF EXISTS tenant_id")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS tenant_id")
    op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS tenant_id")
    op.execute("ALTER TABLE source_documents DROP COLUMN IF EXISTS tenant_id")
