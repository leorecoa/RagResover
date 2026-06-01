"""Initial RagResover schema.

Revision ID: 20260601_0001
Revises:
Create Date: 2026-06-01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260601_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE SCHEMA IF NOT EXISTS tenant_common")
    op.execute(
        """
        DO $$
        DECLARE
            db_name text;
        BEGIN
            SELECT current_database() INTO db_name;
            EXECUTE format(
                'ALTER DATABASE %I SET search_path TO public, tenant_common',
                db_name
            );
        END $$;
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR(500) NOT NULL,
            content TEXT NOT NULL,
            file_name VARCHAR(255),
            file_type VARCHAR(50),
            file_size BIGINT,
            metadata JSONB,
            embedding vector,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS source_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR(500) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            content_type VARCHAR(100) NOT NULL,
            file_size BIGINT NOT NULL,
            storage_path TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_document_id UUID NOT NULL
                REFERENCES source_documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            embedding vector,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (source_document_id, chunk_index)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            sources JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_source_documents_created_at
        ON source_documents(created_at)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_chunks_source_document_id
        ON document_chunks(source_document_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
        ON messages(conversation_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_documents_created_at
        ON documents(created_at)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_documents_created_at")
    op.execute("DROP INDEX IF EXISTS idx_messages_conversation_id")
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_source_document_id")
    op.execute("DROP INDEX IF EXISTS idx_source_documents_created_at")
    op.execute("DROP TABLE IF EXISTS messages")
    op.execute("DROP TABLE IF EXISTS conversations")
    op.execute("DROP TABLE IF EXISTS document_chunks")
    op.execute("DROP TABLE IF EXISTS source_documents")
    op.execute("DROP TABLE IF EXISTS documents")
    op.execute("DROP SCHEMA IF EXISTS tenant_common")
