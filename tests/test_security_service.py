import time

import pytest

from app.services import security
from app.services.security import TokenError, create_access_token, decode_access_token


def test_password_hash_verification_roundtrip(monkeypatch):
    monkeypatch.setattr(security.settings, "PASSWORD_HASH_ITERATIONS", 100_000)

    password_hash = security.hash_password("correct horse battery staple")

    assert security.verify_password("correct horse battery staple", password_hash) is True
    assert security.verify_password("wrong password", password_hash) is False


def test_access_token_roundtrip(monkeypatch):
    monkeypatch.setattr(security.settings, "JWT_SECRET_KEY", _Secret("jwt-secret"))

    token = create_access_token(
        subject="user-1",
        expires_in_seconds=60,
        extra_claims={"email": "user@example.com"},
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "user-1"
    assert payload["email"] == "user@example.com"


def test_access_token_rejects_expired_token(monkeypatch):
    monkeypatch.setattr(security.settings, "JWT_SECRET_KEY", _Secret("jwt-secret"))

    token = create_access_token(subject="user-1", expires_in_seconds=-1)

    with pytest.raises(TokenError):
        decode_access_token(token)


def test_access_token_rejects_invalid_signature(monkeypatch):
    monkeypatch.setattr(security.settings, "JWT_SECRET_KEY", _Secret("jwt-secret"))
    token = create_access_token(subject="user-1", expires_in_seconds=60)
    monkeypatch.setattr(security.settings, "JWT_SECRET_KEY", _Secret("other-secret"))

    with pytest.raises(TokenError):
        decode_access_token(token)


class _Secret:
    def __init__(self, value: str):
        self.value = value

    def get_secret_value(self):
        return self.value
