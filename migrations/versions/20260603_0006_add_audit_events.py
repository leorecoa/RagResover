"""Add audit events.

Revision ID: 20260603_0006
Revises: 20260603_0005
Create Date: 2026-06-03
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260603_0006"
down_revision: str | None = "20260603_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id VARCHAR(128) NOT NULL,
            actor_user_id VARCHAR(255),
            actor_roles JSONB NOT NULL DEFAULT '[]'::jsonb,
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(100) NOT NULL,
            resource_id TEXT,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_events_tenant_created_at
        ON audit_events(tenant_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_events_action
        ON audit_events(action)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_audit_events_action")
    op.execute("DROP INDEX IF EXISTS idx_audit_events_tenant_created_at")
    op.execute("DROP TABLE IF EXISTS audit_events")
