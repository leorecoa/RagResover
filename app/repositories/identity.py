from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class UserRecord:
    id: UUID
    email: str
    full_name: str | None
    password_hash: str
    is_active: bool
    created_at: datetime


@dataclass(frozen=True)
class OrganizationRecord:
    id: UUID
    name: str
    created_at: datetime


@dataclass(frozen=True)
class MembershipRecord:
    user_id: UUID
    organization_id: UUID
    role: str
    created_at: datetime


@dataclass(frozen=True)
class OrganizationMemberRecord:
    user_id: UUID
    email: str
    full_name: str | None
    role: str
    created_at: datetime


@dataclass(frozen=True)
class InvitationRecord:
    id: UUID
    organization_id: UUID
    email: str
    role: str
    invited_by_user_id: UUID
    status: str
    created_at: datetime


class IdentityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _user_from_row(row) -> UserRecord:
        return UserRecord(
            id=row["id"],
            email=row["email"],
            full_name=row["full_name"],
            password_hash=row["password_hash"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
        )

    @staticmethod
    def _organization_from_row(row) -> OrganizationRecord:
        return OrganizationRecord(
            id=row["id"],
            name=row["name"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _membership_from_row(row) -> MembershipRecord:
        return MembershipRecord(
            user_id=row["user_id"],
            organization_id=row["organization_id"],
            role=row["role"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _member_from_row(row) -> OrganizationMemberRecord:
        return OrganizationMemberRecord(
            user_id=row["user_id"],
            email=row["email"],
            full_name=row["full_name"],
            role=row["role"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _invitation_from_row(row) -> InvitationRecord:
        return InvitationRecord(
            id=row["id"],
            organization_id=row["organization_id"],
            email=row["email"],
            role=row["role"],
            invited_by_user_id=row["invited_by_user_id"],
            status=row["status"],
            created_at=row["created_at"],
        )

    async def create_user(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str | None,
    ) -> UserRecord:
        result = await self.session.execute(
            text(
                """
                INSERT INTO users (email, password_hash, full_name)
                VALUES (lower(:email), :password_hash, :full_name)
                RETURNING id, email, full_name, password_hash, is_active, created_at
                """
            ),
            {
                "email": email.strip().lower(),
                "password_hash": password_hash,
                "full_name": full_name.strip() if full_name and full_name.strip() else None,
            },
        )
        await self.session.commit()
        return self._user_from_row(result.mappings().one())

    async def get_user_by_email(self, *, email: str) -> UserRecord | None:
        result = await self.session.execute(
            text(
                """
                SELECT id, email, full_name, password_hash, is_active, created_at
                FROM users
                WHERE email = lower(:email)
                """
            ),
            {"email": email.strip().lower()},
        )
        row = result.mappings().first()
        return self._user_from_row(row) if row else None

    async def get_user_by_id(self, *, user_id: UUID) -> UserRecord | None:
        result = await self.session.execute(
            text(
                """
                SELECT id, email, full_name, password_hash, is_active, created_at
                FROM users
                WHERE id = :user_id
                """
            ),
            {"user_id": user_id},
        )
        row = result.mappings().first()
        return self._user_from_row(row) if row else None

    async def create_organization(self, *, name: str) -> OrganizationRecord:
        result = await self.session.execute(
            text(
                """
                INSERT INTO organizations (name)
                VALUES (:name)
                RETURNING id, name, created_at
                """
            ),
            {"name": name.strip()},
        )
        await self.session.commit()
        return self._organization_from_row(result.mappings().one())

    async def get_organization(self, *, organization_id: UUID) -> OrganizationRecord | None:
        result = await self.session.execute(
            text(
                """
                SELECT id, name, created_at
                FROM organizations
                WHERE id = :organization_id
                """
            ),
            {"organization_id": organization_id},
        )
        row = result.mappings().first()
        return self._organization_from_row(row) if row else None

    async def update_organization_name(
        self,
        *,
        organization_id: UUID,
        name: str,
    ) -> OrganizationRecord:
        result = await self.session.execute(
            text(
                """
                UPDATE organizations
                SET name = :name, updated_at = CURRENT_TIMESTAMP
                WHERE id = :organization_id
                RETURNING id, name, created_at
                """
            ),
            {"organization_id": organization_id, "name": name.strip()},
        )
        await self.session.commit()
        return self._organization_from_row(result.mappings().one())

    async def create_membership(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
        role: str,
    ) -> MembershipRecord:
        result = await self.session.execute(
            text(
                """
                INSERT INTO organization_memberships (user_id, organization_id, role)
                VALUES (:user_id, :organization_id, lower(:role))
                ON CONFLICT (user_id, organization_id)
                DO UPDATE SET role = EXCLUDED.role
                RETURNING user_id, organization_id, role, created_at
                """
            ),
            {
                "user_id": user_id,
                "organization_id": organization_id,
                "role": role.strip().lower(),
            },
        )
        await self.session.commit()
        return self._membership_from_row(result.mappings().one())

    async def list_memberships(self, *, user_id: UUID) -> list[MembershipRecord]:
        result = await self.session.execute(
            text(
                """
                SELECT user_id, organization_id, role, created_at
                FROM organization_memberships
                WHERE user_id = :user_id
                ORDER BY created_at ASC
                """
            ),
            {"user_id": user_id},
        )
        return [self._membership_from_row(row) for row in result.mappings().all()]

    async def get_membership(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
    ) -> MembershipRecord | None:
        result = await self.session.execute(
            text(
                """
                SELECT user_id, organization_id, role, created_at
                FROM organization_memberships
                WHERE user_id = :user_id
                AND organization_id = :organization_id
                """
            ),
            {"user_id": user_id, "organization_id": organization_id},
        )
        row = result.mappings().first()
        return self._membership_from_row(row) if row else None

    async def list_organization_members(
        self,
        *,
        organization_id: UUID,
    ) -> list[OrganizationMemberRecord]:
        result = await self.session.execute(
            text(
                """
                SELECT
                    users.id AS user_id,
                    users.email,
                    users.full_name,
                    organization_memberships.role,
                    organization_memberships.created_at
                FROM organization_memberships
                JOIN users ON users.id = organization_memberships.user_id
                WHERE organization_memberships.organization_id = :organization_id
                ORDER BY organization_memberships.created_at ASC
                """
            ),
            {"organization_id": organization_id},
        )
        return [self._member_from_row(row) for row in result.mappings().all()]

    async def update_membership_role(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
        role: str,
    ) -> MembershipRecord:
        result = await self.session.execute(
            text(
                """
                UPDATE organization_memberships
                SET role = lower(:role), updated_at = CURRENT_TIMESTAMP
                WHERE organization_id = :organization_id
                AND user_id = :user_id
                RETURNING user_id, organization_id, role, created_at
                """
            ),
            {
                "organization_id": organization_id,
                "user_id": user_id,
                "role": role.strip().lower(),
            },
        )
        await self.session.commit()
        return self._membership_from_row(result.mappings().one())

    async def create_invitation(
        self,
        *,
        organization_id: UUID,
        email: str,
        role: str,
        invited_by_user_id: UUID,
    ) -> InvitationRecord:
        result = await self.session.execute(
            text(
                """
                INSERT INTO organization_invitations (
                    organization_id,
                    email,
                    role,
                    invited_by_user_id
                )
                VALUES (:organization_id, lower(:email), lower(:role), :invited_by_user_id)
                ON CONFLICT (organization_id, email)
                WHERE status = 'pending'
                DO UPDATE SET
                    role = EXCLUDED.role,
                    invited_by_user_id = EXCLUDED.invited_by_user_id,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id, organization_id, email, role, invited_by_user_id, status, created_at
                """
            ),
            {
                "organization_id": organization_id,
                "email": email.strip().lower(),
                "role": role.strip().lower(),
                "invited_by_user_id": invited_by_user_id,
            },
        )
        await self.session.commit()
        return self._invitation_from_row(result.mappings().one())

    async def list_invitations(
        self,
        *,
        organization_id: UUID,
    ) -> list[InvitationRecord]:
        result = await self.session.execute(
            text(
                """
                SELECT id, organization_id, email, role, invited_by_user_id, status, created_at
                FROM organization_invitations
                WHERE organization_id = :organization_id
                ORDER BY created_at DESC
                """
            ),
            {"organization_id": organization_id},
        )
        return [self._invitation_from_row(row) for row in result.mappings().all()]
