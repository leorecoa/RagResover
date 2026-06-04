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
