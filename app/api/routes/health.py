import anyio
from fastapi import APIRouter, HTTPException

from app.api.schemas.health import HealthResponse, ReadinessResponse
from app.core.config import settings
from app.core.constants import APP_VERSION
from app.db.session import is_database_available
from app.services.storage import storage_service

router = APIRouter(tags=["Infrastructure"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "env": settings.APP_ENV,
        "version": APP_VERSION,
    }


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    checks = {"database": False, "storage": False}

    async def check_database() -> None:
        checks["database"] = await is_database_available()

    async def check_storage() -> None:
        try:
            checks["storage"] = await storage_service.is_available()
        except Exception:
            checks["storage"] = False

    async with anyio.create_task_group() as task_group:
        task_group.start_soon(check_database)
        task_group.start_soon(check_storage)

    is_ready = checks["database"] and checks["storage"]
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "database": "available" if checks["database"] else "unavailable",
        "storage": "available" if checks["storage"] else "unavailable",
        "env": settings.APP_ENV,
        "version": APP_VERSION,
    }
    if not is_ready:
        raise HTTPException(status_code=503, detail=payload)
    return payload
