from fastapi import Request, Response

from app.api.dependencies.auth import ensure_admin_context, get_tenant_context
from app.core.config import settings
from app.core.metrics import request_metrics
from app.db.session import AsyncSessionLocal


async def metrics(request: Request) -> Response:
    if settings.METRICS_REQUIRE_ADMIN:
        async with AsyncSessionLocal() as session:
            context = await get_tenant_context(
                x_tenant_id=request.headers.get("X-Tenant-ID"),
                x_api_key=request.headers.get("X-API-Key"),
                x_user_id=request.headers.get("X-User-ID"),
                x_user_roles=request.headers.get("X-User-Roles"),
                authorization=request.headers.get("Authorization"),
                session=session,
            )
        ensure_admin_context(context)

    return Response(
        content=request_metrics.render_prometheus(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
