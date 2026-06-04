from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.auth import AuthUserResponse, OrganizationMembershipResponse
from app.core.config import settings
from app.repositories.identity import IdentityRepository, UserRecord
from app.services.security import create_access_token, hash_password, verify_password


def user_payload(
    *,
    user: UserRecord,
    memberships,
) -> AuthUserResponse:
    return AuthUserResponse(
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        organizations=[
            OrganizationMembershipResponse(
                organization_id=str(membership.organization_id),
                role=membership.role,
            )
            for membership in memberships
        ],
    )


async def register_user_with_organization(
    *,
    session: AsyncSession,
    email: str,
    password: str,
    full_name: str | None,
    organization_name: str,
):
    repository = IdentityRepository(session)
    try:
        user = await repository.create_user(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
        )
        organization = await repository.create_organization(name=organization_name)
        membership = await repository.create_membership(
            user_id=user.id,
            organization_id=organization.id,
            role="owner",
        )
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Usuario ja existe.",
        ) from exc

    memberships = [membership]
    return build_token_response(user=user, memberships=memberships)


async def authenticate_user(
    *,
    session: AsyncSession,
    email: str,
    password: str,
    organization_id: str | None,
):
    repository = IdentityRepository(session)
    user = await repository.get_user_by_email(email=email)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas.",
        )

    memberships = await repository.list_memberships(user_id=user.id)
    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sem organizacao ativa.",
        )

    if organization_id:
        try:
            selected_org = UUID(organization_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="organization_id invalido.",
            ) from exc
        if selected_org not in {membership.organization_id for membership in memberships}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario nao pertence a organizacao informada.",
            )

    return build_token_response(user=user, memberships=memberships)


def build_token_response(*, user: UserRecord, memberships):
    expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    access_token = create_access_token(
        subject=str(user.id),
        expires_in_seconds=expires_in,
        extra_claims={
            "email": user.email,
            "orgs": [
                {
                    "organization_id": str(membership.organization_id),
                    "role": membership.role,
                }
                for membership in memberships
            ],
        },
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": user_payload(user=user, memberships=memberships),
    }
