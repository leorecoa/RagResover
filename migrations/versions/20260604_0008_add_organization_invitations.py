"""Add organization invitations.

Revision ID: 20260604_0008
Revises: 20260604_0007
Create Date: 2026-06-04
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260604_0008"
down_revision: str | None = "20260604_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS organization_invitations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
            email VARCHAR(320) NOT NULL,
            role VARCHAR(50) NOT NULL DEFAULT 'member',
            invited_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT organization_invitations_role_check
                CHECK (role IN ('admin', 'member', 'viewer')),
            CONSTRAINT organization_invitations_status_check
                CHECK (status IN ('pending', 'accepted', 'revoked'))
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_organization_invitations_pending_email
        ON organization_invitations(organization_id, email)
        WHERE status = 'pending'
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_organization_invitations_organization_id
        ON organization_invitations(organization_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_organization_invitations_organization_id")
    op.execute("DROP INDEX IF EXISTS idx_organization_invitations_pending_email")
    op.execute("DROP TABLE IF EXISTS organization_invitations")
