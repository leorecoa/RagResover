import pytest
from fastapi import HTTPException

import app.api.dependencies.auth as auth_module
from app.api.dependencies.auth import (
    extract_bearer_token,
    get_tenant_context,
    validate_tenant_id,
)


def test_extract_bearer_token_accepts_authorization_header():
    assert extract_bearer_token("Bearer secret-token") == "secret-token"
    assert extract_bearer_token("Basic abc") is None


def test_validate_tenant_id_rejects_unsafe_values():
    with pytest.raises(HTTPException):
        validate_tenant_id("../tenant")


def test_get_tenant_context_uses_explicit_tenant(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "ALLOW_ANONYMOUS_ACCESS", True)
    monkeypatch.setattr(auth_module.settings, "API_AUTH_TOKEN", _Secret(""))

    async def call_dependency():
        return await get_tenant_context(
            x_tenant_id="tenant-a",
            x_api_key=None,
            authorization=None,
        )

    import anyio

    context = anyio.run(call_dependency)

    assert context.tenant_id == "tenant-a"
    assert context.is_anonymous is False


def test_get_tenant_context_uses_default_anonymous_tenant(monkeypatch):
    monkeypatch.setattr(auth_module.settings, "ALLOW_ANONYMOUS_ACCESS", True)
    monkeypatch.setattr(auth_module.settings, "DEFAULT_TENANT_ID", "public")
    monkeypatch.setattr(auth_module.settings, "API_AUTH_TOKEN", _Secret(""))

    async def call_dependency():
        return await get_tenant_context(
            x_tenant_id=None,
            x_api_key=None,
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
            authorization="Bearer expected",
        )

    import anyio

    context = anyio.run(call_dependency)

    assert context.tenant_id == "tenant-a"


class _Secret:
    def __init__(self, value: str):
        self.value = value

    def get_secret_value(self):
        return self.value
