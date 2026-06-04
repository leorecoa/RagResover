"""Add identity tables.

Revision ID: 20260604_0007
Revises: 20260603_0006
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260604_0007"
down_revision: str | None = "20260603_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(320) NOT NULL UNIQUE,
            full_name VARCHAR(255),
            password_hash TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS organizations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_memberships (
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            role VARCHAR(50) NOT NULL DEFAULT 'member',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, organization_id),
            CONSTRAINT organization_memberships_role_check
                CHECK (role IN ('owner', 'admin', 'member', 'viewer'))
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_organization_memberships_organization_id
        ON organization_memberships(organization_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_organization_memberships_organization_id")
    op.execute("DROP TABLE IF EXISTS organization_memberships")
    op.execute("DROP INDEX IF EXISTS idx_users_email")
    op.execute("DROP TABLE IF EXISTS organizations")
    op.execute("DROP TABLE IF EXISTS users")
