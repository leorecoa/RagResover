import pytest
from fastapi import HTTPException
from uuid import UUID

import app.api.dependencies.auth as auth_module
from app.api.dependencies.auth import (
    ensure_admin_context,
    ensure_authenticated_context,
    extract_bearer_token,
    get_tenant_context,
    parse_roles,
    validate_tenant_id,
)
from app.repositories.identity import ApiKeyRecord, MembershipRecord, UserRecord


def test_extract_bearer_token_accepts_authorization_header():
    assert extract_bearer_token("Bearer secret-token") == "secret-token"
    assert extract_bearer_token("Basic abc") is None


def test_validate_tenant_id_rejects_unsafe_values():
    with pytest.raises(HTTPException):
        validate_tenant_id("../tenant")


def test_parse_roles_normalizes_comma_separated_roles():
    assert parse_roles(" Admin, viewer,admin , ") == frozenset({"admin", "viewer"})


def test_get_tenant_context_uses_explicit_tenant(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "ALLOW_ANONYMOUS_ACCESS", True)
    monkeypatch.setattr(auth_module.settings, "API_AUTH_TOKEN", _Secret(""))

    async def call_dependency():
        return await get_tenant_context(
            x_tenant_id="tenant-a",
            x_api_key=None,
            x_user_id="user-1",
            x_user_roles="Admin,Viewer",
            authorization=None,
        )

    import anyio

    context = anyio.run(call_dependency)

    assert context.tenant_id == "tenant-a"
    assert context.is_anonymous is False
    assert context.user_id == "user-1"
    assert context.roles == frozenset({"admin", "viewer"})


def test_get_tenant_context_uses_default_anonymous_tenant(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "ALLOW_ANONYMOUS_ACCESS", True)
    monkeypatch.setattr(auth_module.settings, "DEFAULT_TENANT_ID", "public")
    monkeypatch.setattr(auth_module.settings, "API_AUTH_TOKEN", _Secret(""))

    async def call_dependency():
        return await get_tenant_context(
            x_tenant_id=None,
            x_api_key=None,
            x_user_id=None,
            x_user_roles=None,
            authorization=None,
        )

    import anyio

    context = anyio.run(call_dependency)

    assert context.tenant_id == "public"
    assert context.is_anonymous is True


def test_get_tenant_context_can_disable_anonymous_access(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "ALLOW_ANONYMOUS_ACCESS", False)
    monkeypatch.setattr(auth_module.settings, "API_AUTH_TOKEN", _Secret(""))

    async def call_dependency():
        return await get_tenant_context(
            x_tenant_id=None,
            x_api_key=None,
            x_user_id=None,
            x_user_roles=None,
            authorization=None,
        )

    import anyio

    with pytest.raises(HTTPException) as exc:
        anyio.run(call_dependency)

    assert exc.value.status_code == 401


def test_get_tenant_context_requires_api_token_when_configured(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "API_AUTH_TOKEN", _Secret("expected"))

    async def call_dependency():
        return await get_tenant_context(
            x_tenant_id="tenant-a",
            x_api_key=None,
            x_user_id=None,
            x_user_roles=None,
            authorization=None,
        )

    import anyio

    with pytest.raises(HTTPException) as exc:
        anyio.run(call_dependency)

    assert exc.value.status_code == 401


def test_get_tenant_context_accepts_api_token_when_configured(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "API_AUTH_TOKEN", _Secret("expected"))

    async def call_dependency():
        return await get_tenant_context(
            x_tenant_id="tenant-a",
            x_api_key=None,
            x_user_id=None,
            x_user_roles=None,
            authorization="Bearer expected",
        )

    import anyio

    context = anyio.run(call_dependency)

    assert context.tenant_id == "tenant-a"


def test_get_tenant_context_accepts_jwt_membership(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "API_AUTH_TOKEN", _Secret(""))

    class FakeIdentityRepository:
        def __init__(self, session):
            self.session = session

        async def get_user_by_id(self, *, user_id):
            return UserRecord(
                id=user_id,
                email="owner@example.com",
                full_name="Owner",
                password_hash="hash",
                is_active=True,
                created_at=None,
            )

        async def list_memberships(self, *, user_id):
            return [
                MembershipRecord(
                    user_id=user_id,
                    organization_id=UUID("11111111-1111-1111-1111-111111111111"),
                    role="owner",
                    created_at=None,
                )
            ]

    monkeypatch.setattr(auth_module, "IdentityRepository", FakeIdentityRepository)
    monkeypatch.setattr(
        auth_module,
        "decode_access_token",
        lambda token: {"sub": "99999999-9999-9999-9999-999999999999"},
    )

    async def call_dependency():
        return await get_tenant_context(
            x_tenant_id="11111111-1111-1111-1111-111111111111",
            x_api_key=None,
            x_user_id=None,
            x_user_roles=None,
            authorization="Bearer jwt-token",
            session=_FakeSession(),
        )

    import anyio

    context = anyio.run(call_dependency)

    assert context.tenant_id == "11111111-1111-1111-1111-111111111111"
    assert context.user_id == "99999999-9999-9999-9999-999999999999"
    assert context.email == "owner@example.com"
    assert context.roles == frozenset({"owner"})


def test_get_tenant_context_rejects_cross_organization_jwt(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "API_AUTH_TOKEN", _Secret(""))

    class FakeIdentityRepository:
        def __init__(self, session):
            self.session = session

        async def get_user_by_id(self, *, user_id):
            return UserRecord(
                id=user_id,
                email="owner@example.com",
                full_name="Owner",
                password_hash="hash",
                is_active=True,
                created_at=None,
            )

        async def list_memberships(self, *, user_id):
            return [
                MembershipRecord(
                    user_id=user_id,
                    organization_id=UUID("11111111-1111-1111-1111-111111111111"),
                    role="owner",
                    created_at=None,
                )
            ]

    monkeypatch.setattr(auth_module, "IdentityRepository", FakeIdentityRepository)
    monkeypatch.setattr(
        auth_module,
        "decode_access_token",
        lambda token: {"sub": "99999999-9999-9999-9999-999999999999"},
    )

    async def call_dependency():
        return await get_tenant_context(
            x_tenant_id="22222222-2222-2222-2222-222222222222",
            x_api_key=None,
            x_user_id=None,
            x_user_roles=None,
            authorization="Bearer jwt-token",
            session=_FakeSession(),
        )

    import anyio

    with pytest.raises(HTTPException) as exc:
        anyio.run(call_dependency)

    assert exc.value.status_code == 403


def test_get_tenant_context_accepts_tenant_api_key(monkeypatch):
    raw_key = "rrk_abcdefghijkl_secret"
    monkeypatch.setattr(auth_module.settings, "API_AUTH_TOKEN", _Secret(""))
    monkeypatch.setattr(auth_module, "api_key_prefix", lambda value: "abcdefghijkl")
    monkeypatch.setattr(auth_module, "verify_api_key", lambda value, hashed: value == raw_key)

    class FakeIdentityRepository:
        def __init__(self, session):
            self.session = session

        async def get_active_api_key_by_prefix(self, *, key_prefix):
            assert key_prefix == "abcdefghijkl"
            return ApiKeyRecord(
                id=UUID("33333333-3333-3333-3333-333333333333"),
                organization_id=UUID("11111111-1111-1111-1111-111111111111"),
                name="automation",
                key_prefix="abcdefghijkl",
                key_hash="hash",
                role="member",
                created_by_user_id=UUID("99999999-9999-9999-9999-999999999999"),
                created_at=None,
                revoked_at=None,
            )

    monkeypatch.setattr(auth_module, "IdentityRepository", FakeIdentityRepository)

    async def call_dependency():
        return await get_tenant_context(
            x_tenant_id="11111111-1111-1111-1111-111111111111",
            x_api_key=raw_key,
            x_user_id=None,
            x_user_roles=None,
            authorization=None,
            session=_FakeSession(),
        )

    import anyio

    context = anyio.run(call_dependency)

    assert context.tenant_id == "11111111-1111-1111-1111-111111111111"
    assert context.user_id == "99999999-9999-9999-9999-999999999999"
    assert context.roles == frozenset({"member"})


def test_production_rejects_header_only_tenant_context(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "APP_ENV", "production")
    monkeypatch.setattr(auth_module.settings, "API_AUTH_TOKEN", _Secret(""))

    async def call_dependency():
        return await get_tenant_context(
            x_tenant_id="tenant-a",
            x_api_key=None,
            x_user_id=None,
            x_user_roles="admin",
            authorization=None,
            session=_FakeSession(),
        )

    import anyio

    with pytest.raises(HTTPException) as exc:
        anyio.run(call_dependency)

    assert exc.value.status_code == 401


def test_ensure_admin_context_accepts_admin_role(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "ADMIN_ROLE_NAME", "admin")
    context = auth_module.TenantContext(
        tenant_id="tenant-a",
        is_anonymous=False,
        user_id="user-1",
        roles=frozenset({"admin"}),
    )

    assert ensure_admin_context(context) is context


def test_ensure_admin_context_rejects_missing_admin_role(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "ADMIN_ROLE_NAME", "admin")
    context = auth_module.TenantContext(
        tenant_id="tenant-a",
        is_anonymous=False,
        user_id="user-1",
        roles=frozenset({"viewer"}),
    )

    with pytest.raises(HTTPException) as exc:
        ensure_admin_context(context)

    assert exc.value.status_code == 403


def test_ensure_authenticated_context_rejects_anonymous_context():
    context = auth_module.TenantContext(
        tenant_id="anonymous",
        is_anonymous=True,
    )

    with pytest.raises(HTTPException) as exc:
        ensure_authenticated_context(context)

    assert exc.value.status_code == 401


class _Secret:
    def __init__(self, value: str):
        self.value = value

    def get_secret_value(self):
        return self.value


class _FakeSession:
    async def execute(self, *args, **kwargs):
        return None
