import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import TenantContext
from app.repositories.audit import AuditLogRepository


logger = logging.getLogger("rag_resover")


async def record_audit_event(
    *,
    session: AsyncSession,
    tenant: TenantContext,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    try:
        await AuditLogRepository(session).create_event(
            tenant_id=tenant.tenant_id,
            actor_user_id=tenant.user_id,
            actor_roles=sorted(tenant.roles),
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata or {},
        )
    except Exception:
        logger.exception("audit_event_failed action=%s resource_type=%s", action, resource_type)
