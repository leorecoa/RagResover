from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import TenantContext, require_authenticated_context
from app.api.schemas.auth import LoginRequest, MeResponse, RegisterRequest, TokenResponse
from app.db.session import get_db_session
from app.services.identity import authenticate_user, register_user_with_organization


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
):
    return await register_user_with_organization(
        session=session,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        organization_name=request.organization_name,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
):
    return await authenticate_user(
        session=session,
        email=request.email,
        password=request.password,
        organization_id=request.organization_id,
    )


@router.get("/me", response_model=MeResponse)
async def me(context: TenantContext = Depends(require_authenticated_context)):
    return {
        "user_id": context.user_id or "",
        "email": context.email or "",
        "full_name": context.full_name,
        "organizations": [
            {"organization_id": organization_id, "role": role}
            for organization_id, role in sorted(context.memberships.items())
        ],
    }
