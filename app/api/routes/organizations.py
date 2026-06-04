from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import TenantContext, require_authenticated_context
from app.api.schemas.organizations import (
    ApiKeyCreatedResponse,
    ApiKeysResponse,
    CreateApiKeyRequest,
    InvitationResponse,
    InvitationsResponse,
    InviteMemberRequest,
    OrganizationMembersResponse,
    OrganizationResponse,
    UpdateMemberRoleRequest,
    UpdateOrganizationRequest,
)
from app.db.session import get_db_session
from app.services.organizations import (
    create_organization_api_key,
    get_current_organization,
    invite_member,
    list_organization_api_keys,
    list_current_organization_invitations,
    list_current_organization_members,
    revoke_organization_api_key,
    update_current_organization,
    update_member_role,
)


router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("/current", response_model=OrganizationResponse)
async def current_organization(
    context: TenantContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    return await get_current_organization(session=session, context=context)


@router.patch("/current", response_model=OrganizationResponse)
async def update_organization(
    request: UpdateOrganizationRequest,
    context: TenantContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    return await update_current_organization(
        session=session,
        context=context,
        name=request.name,
    )


@router.get("/current/members", response_model=OrganizationMembersResponse)
async def list_members(
    context: TenantContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    return {
        "members": await list_current_organization_members(
            session=session,
            context=context,
        )
    }


@router.patch("/current/members/{user_id}", response_model=OrganizationMembersResponse)
async def change_member_role(
    user_id: str,
    request: UpdateMemberRoleRequest,
    context: TenantContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    member = await update_member_role(
        session=session,
        context=context,
        user_id=user_id,
        role=request.role,
    )
    return {"members": [member]}


@router.get("/current/invitations", response_model=InvitationsResponse)
async def list_invitations(
    context: TenantContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    return {
        "invitations": await list_current_organization_invitations(
            session=session,
            context=context,
        )
    }


@router.post("/current/invitations", response_model=InvitationResponse, status_code=201)
async def create_invitation(
    request: InviteMemberRequest,
    context: TenantContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    return await invite_member(
        session=session,
        context=context,
        email=request.email,
        role=request.role,
    )


@router.get("/current/api-keys", response_model=ApiKeysResponse)
async def list_api_keys(
    context: TenantContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    return {
        "api_keys": await list_organization_api_keys(
            session=session,
            context=context,
        )
    }


@router.post("/current/api-keys", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_api_key(
    request: CreateApiKeyRequest,
    context: TenantContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    return await create_organization_api_key(
        session=session,
        context=context,
        name=request.name,
        role=request.role,
    )


@router.delete("/current/api-keys/{api_key_id}", response_model=ApiKeysResponse)
async def revoke_api_key(
    api_key_id: str,
    context: TenantContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(get_db_session),
):
    return {
        "api_keys": [
            await revoke_organization_api_key(
                session=session,
                context=context,
                api_key_id=api_key_id,
            )
        ]
    }
