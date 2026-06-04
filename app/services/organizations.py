from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import TenantContext
from app.api.schemas.organizations import (
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    InvitationResponse,
    OrganizationMemberResponse,
    OrganizationResponse,
)
from app.repositories.identity import IdentityRepository
from app.services.security import create_api_key


MANAGER_ROLES = frozenset({"owner", "admin"})


def _organization_id(context: TenantContext) -> UUID:
    try:
        return UUID(context.tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organizacao atual invalida.",
        ) from exc


def _user_id(context: TenantContext) -> UUID:
    if not context.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticacao obrigatoria.",
        )
    return UUID(context.user_id)


def _current_role(context: TenantContext) -> str:
    return next(iter(context.roles), "")


def ensure_manager(context: TenantContext) -> None:
    if not (context.roles & MANAGER_ROLES):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissao de owner ou admin obrigatoria.",
        )


def ensure_owner_for_admin_change(context: TenantContext, role: str) -> None:
    if role == "admin" and "owner" not in context.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente owner pode conceder role admin.",
        )


def member_payload(member) -> OrganizationMemberResponse:
    return OrganizationMemberResponse(
        user_id=str(member.user_id),
        email=member.email,
        full_name=member.full_name,
        role=member.role,
        created_at=member.created_at.isoformat(),
    )


def invitation_payload(invitation) -> InvitationResponse:
    return InvitationResponse(
        id=str(invitation.id),
        organization_id=str(invitation.organization_id),
        email=invitation.email,
        role=invitation.role,
        invited_by_user_id=str(invitation.invited_by_user_id),
        status=invitation.status,
        created_at=invitation.created_at.isoformat(),
    )


def api_key_payload(record) -> ApiKeyResponse:
    return ApiKeyResponse(
        id=str(record.id),
        name=record.name,
        key_prefix=record.key_prefix,
        role=record.role,
        created_by_user_id=str(record.created_by_user_id),
        created_at=record.created_at.isoformat(),
        revoked_at=record.revoked_at.isoformat() if record.revoked_at else None,
    )


async def get_current_organization(
    *,
    session: AsyncSession,
    context: TenantContext,
) -> OrganizationResponse:
    repository = IdentityRepository(session)
    organization = await repository.get_organization(organization_id=_organization_id(context))
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organizacao nao encontrada.")
    return OrganizationResponse(
        id=str(organization.id),
        name=organization.name,
        current_user_role=_current_role(context),
    )


async def update_current_organization(
    *,
    session: AsyncSession,
    context: TenantContext,
    name: str,
) -> OrganizationResponse:
    ensure_manager(context)
    repository = IdentityRepository(session)
    organization = await repository.update_organization_name(
        organization_id=_organization_id(context),
        name=name,
    )
    return OrganizationResponse(
        id=str(organization.id),
        name=organization.name,
        current_user_role=_current_role(context),
    )


async def list_current_organization_members(
    *,
    session: AsyncSession,
    context: TenantContext,
) -> list[OrganizationMemberResponse]:
    repository = IdentityRepository(session)
    members = await repository.list_organization_members(organization_id=_organization_id(context))
    return [member_payload(member) for member in members]


async def invite_member(
    *,
    session: AsyncSession,
    context: TenantContext,
    email: str,
    role: str,
) -> InvitationResponse:
    ensure_manager(context)
    ensure_owner_for_admin_change(context, role)
    repository = IdentityRepository(session)
    invitation = await repository.create_invitation(
        organization_id=_organization_id(context),
        email=email,
        role=role,
        invited_by_user_id=_user_id(context),
    )
    return invitation_payload(invitation)


async def list_current_organization_invitations(
    *,
    session: AsyncSession,
    context: TenantContext,
) -> list[InvitationResponse]:
    ensure_manager(context)
    repository = IdentityRepository(session)
    invitations = await repository.list_invitations(organization_id=_organization_id(context))
    return [invitation_payload(invitation) for invitation in invitations]


async def update_member_role(
    *,
    session: AsyncSession,
    context: TenantContext,
    user_id: str,
    role: str,
) -> OrganizationMemberResponse:
    ensure_manager(context)
    ensure_owner_for_admin_change(context, role)
    try:
        target_user_id = UUID(user_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id invalido.",
        ) from exc
    if target_user_id == _user_id(context):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao altere o proprio role.",
        )
    repository = IdentityRepository(session)
    membership = await repository.get_membership(
        user_id=target_user_id,
        organization_id=_organization_id(context),
    )
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membro nao encontrado.")
    if membership.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role owner nao pode ser alterado por este endpoint.",
        )
    updated = await repository.update_membership_role(
        organization_id=_organization_id(context),
        user_id=target_user_id,
        role=role,
    )
    user = await repository.get_user_by_id(user_id=updated.user_id)
    return OrganizationMemberResponse(
        user_id=str(updated.user_id),
        email=user.email if user else "",
        full_name=user.full_name if user else None,
        role=updated.role,
        created_at=updated.created_at.isoformat(),
    )


async def create_organization_api_key(
    *,
    session: AsyncSession,
    context: TenantContext,
    name: str,
    role: str,
) -> ApiKeyCreatedResponse:
    ensure_manager(context)
    ensure_owner_for_admin_change(context, role)
    raw_key, prefix, key_hash = create_api_key()
    repository = IdentityRepository(session)
    record = await repository.create_api_key(
        organization_id=_organization_id(context),
        name=name,
        key_prefix=prefix,
        key_hash=key_hash,
        role=role,
        created_by_user_id=_user_id(context),
    )
    payload = api_key_payload(record)
    return ApiKeyCreatedResponse(**payload.model_dump(), api_key=raw_key)


async def list_organization_api_keys(
    *,
    session: AsyncSession,
    context: TenantContext,
) -> list[ApiKeyResponse]:
    ensure_manager(context)
    repository = IdentityRepository(session)
    records = await repository.list_api_keys(organization_id=_organization_id(context))
    return [api_key_payload(record) for record in records]


async def revoke_organization_api_key(
    *,
    session: AsyncSession,
    context: TenantContext,
    api_key_id: str,
) -> ApiKeyResponse:
    ensure_manager(context)
    try:
        parsed_id = UUID(api_key_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key nao encontrada.",
        ) from exc
    repository = IdentityRepository(session)
    record = await repository.revoke_api_key(
        organization_id=_organization_id(context),
        api_key_id=parsed_id,
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key nao encontrada.",
        )
    return api_key_payload(record)
