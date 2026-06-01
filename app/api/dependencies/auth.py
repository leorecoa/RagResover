import re
from dataclasses import dataclass

from fastapi import Header, HTTPException, status

from app.core.config import settings


TENANT_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    is_anonymous: bool


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


async def get_tenant_context(
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> TenantContext:
    if settings.has_api_auth_token:
        provided_token = extract_bearer_token(authorization) or (x_api_key or "").strip()
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
        )

    if not settings.ALLOW_ANONYMOUS_ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Tenant-ID obrigatorio quando acesso anonimo esta desabilitado.",
        )

    return TenantContext(
        tenant_id=validate_tenant_id(settings.DEFAULT_TENANT_ID),
        is_anonymous=True,
    )
