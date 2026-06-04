"""Add organization API keys.

Revision ID: 20260604_0009
Revises: 20260604_0008
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260604_0009"
down_revision: str | None = "20260604_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_api_keys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            name VARCHAR(120) NOT NULL,
            key_prefix VARCHAR(32) NOT NULL UNIQUE,
            key_hash CHAR(64) NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'member',
            created_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            revoked_at TIMESTAMP,
            CONSTRAINT organization_api_keys_role_check
                CHECK (role IN ('admin', 'member', 'viewer'))
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_organization_api_keys_organization_id
        ON organization_api_keys(organization_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_organization_api_keys_organization_id")
    op.execute("DROP TABLE IF EXISTS organization_api_keys")
