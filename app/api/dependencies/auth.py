import re
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db_session
from app.repositories.identity import IdentityRepository
from app.services.security import TokenError, decode_access_token


TENANT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    is_anonymous: bool
    user_id: str | None = None
    email: str | None = None
    full_name: str | None = None
    roles: frozenset[str] = frozenset()
    memberships: dict[str, str] = None

    def __post_init__(self):
        if self.memberships is None:
            object.__setattr__(self, "memberships", {})


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def validate_tenant_id(tenant_id: str) -> str:
    normalized = tenant_id.strip()
    if not TENANT_ID_PATTERN.fullmatch(normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "X-Tenant-ID invalido. Use letras, numeros, ponto, hifen, "
                "underscore ou dois-pontos, com ate 128 caracteres."
            ),
        )
    return normalized


def parse_roles(raw_roles: str | None) -> frozenset[str]:
    if not raw_roles:
        return frozenset()
    return frozenset(
        role.strip().lower()
        for role in raw_roles.split(",")
        if role.strip()
    )


def build_user_context(
    *,
    x_user_id: str | None,
    x_user_roles: str | None,
) -> tuple[str | None, frozenset[str]]:
    user_id = x_user_id.strip() if x_user_id and x_user_id.strip() else None
    return user_id, parse_roles(x_user_roles)


async def get_tenant_context(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
    x_user_roles: str | None = Header(default=None, alias="X-User-Roles"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    session: AsyncSession | None = Depends(get_db_session),
) -> TenantContext:
    user_id, roles = build_user_context(
        x_user_id=x_user_id,
        x_user_roles=x_user_roles,
    )
    bearer_token = extract_bearer_token(authorization)

    if bearer_token and (
        not settings.has_api_auth_token
        or bearer_token != settings.API_AUTH_TOKEN.get_secret_value().strip()
    ):
        return await get_jwt_tenant_context(
            token=bearer_token,
            requested_tenant_id=x_tenant_id,
            session=session if hasattr(session, "execute") else None,
        )

    if settings.has_api_auth_token:
        provided_token = bearer_token or (x_api_key or "").strip()
        expected_token = settings.API_AUTH_TOKEN.get_secret_value().strip()
        if not provided_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticacao obrigatoria.",
            )
        if provided_token != expected_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais invalidas.",
            )

    if x_tenant_id and x_tenant_id.strip():
        return TenantContext(
            tenant_id=validate_tenant_id(x_tenant_id),
            is_anonymous=False,
            user_id=user_id,
            roles=roles,
        )

    if not settings.ALLOW_ANONYMOUS_ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Tenant-ID obrigatorio quando acesso anonimo esta desabilitado.",
        )

    return TenantContext(
        tenant_id=validate_tenant_id(settings.DEFAULT_TENANT_ID),
        is_anonymous=True,
        user_id=user_id,
        roles=roles,
    )


async def get_jwt_tenant_context(
    *,
    token: str,
    requested_tenant_id: str | None,
    session: AsyncSession | None,
) -> TenantContext:
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessao de autenticacao indisponivel.",
        )

    try:
        payload = decode_access_token(token)
        user_id = UUID(str(payload["sub"]))
    except (TokenError, ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido.",
        ) from exc

    repository = IdentityRepository(session)
    user = await repository.get_user_by_id(user_id=user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inativo ou nao encontrado.",
        )

    memberships = await repository.list_memberships(user_id=user.id)
    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario sem organizacao ativa.",
        )

    membership_map = {
        str(membership.organization_id): membership.role
        for membership in memberships
    }
    tenant_id = (
        validate_tenant_id(requested_tenant_id)
        if requested_tenant_id and requested_tenant_id.strip()
        else next(iter(membership_map))
    )
    if tenant_id not in membership_map:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario nao pertence ao tenant informado.",
        )

    return TenantContext(
        tenant_id=tenant_id,
        is_anonymous=False,
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        roles=frozenset({membership_map[tenant_id]}),
        memberships=membership_map,
    )


def ensure_admin_context(context: TenantContext) -> TenantContext:
    admin_role = settings.ADMIN_ROLE_NAME.strip().lower()
    if admin_role not in context.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissao administrativa obrigatoria.",
        )
    return context


def ensure_authenticated_context(context: TenantContext) -> TenantContext:
    if not context.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticacao obrigatoria.",
        )
    return context


async def require_admin_context(
    context: TenantContext = Depends(get_tenant_context),
) -> TenantContext:
    return ensure_admin_context(context)


async def require_authenticated_context(
    context: TenantContext = Depends(get_tenant_context),
) -> TenantContext:
    return ensure_authenticated_context(context)
