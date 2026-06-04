import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class AuditEventRecord:
    id: UUID
    tenant_id: str
    actor_user_id: str | None
    actor_roles: list[str]
    action: str
    resource_type: str
    resource_id: str | None
    metadata: dict[str, Any]
    created_at: datetime


class AuditLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _event_from_row(row) -> AuditEventRecord:
        actor_roles = row["actor_roles"]
        metadata = row["metadata"]
        return AuditEventRecord(
            id=row["id"],
            tenant_id=row["tenant_id"],
            actor_user_id=row["actor_user_id"],
            actor_roles=actor_roles if isinstance(actor_roles, list) else [],
            action=row["action"],
            resource_type=row["resource_type"],
            resource_id=row["resource_id"],
            metadata=metadata if isinstance(metadata, dict) else {},
            created_at=row["created_at"],
        )

    async def create_event(
        self,
        *,
        tenant_id: str,
        actor_user_id: str | None,
        actor_roles: list[str],
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEventRecord:
        result = await self.session.execute(
            text(
                """
                INSERT INTO audit_events (
                    tenant_id,
                    actor_user_id,
                    actor_roles,
                    action,
                    resource_type,
                    resource_id,
                    metadata
                )
                VALUES (
                    :tenant_id,
                    :actor_user_id,
                    CAST(:actor_roles AS jsonb),
                    :action,
                    :resource_type,
                    :resource_id,
                    CAST(:metadata AS jsonb)
                )
                RETURNING
                    id,
                    tenant_id,
                    actor_user_id,
                    actor_roles,
                    action,
                    resource_type,
                    resource_id,
                    metadata,
                    created_at
                """
            ),
            {
                "tenant_id": tenant_id,
                "actor_user_id": actor_user_id,
                "actor_roles": json.dumps(actor_roles),
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "metadata": json.dumps(metadata or {}),
            },
        )
        await self.session.commit()
        return self._event_from_row(result.mappings().one())
