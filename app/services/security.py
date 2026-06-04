import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from app.core.config import settings


PASSWORD_ALGORITHM = "pbkdf2_sha256"
JWT_ALGORITHM = "HS256"


class TokenError(ValueError):
    """Raised when a JWT cannot be decoded or verified."""


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = settings.PASSWORD_HASH_ITERATIONS
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return "$".join(
        [
            PASSWORD_ALGORITHM,
            str(iterations),
            _b64url_encode(salt),
            _b64url_encode(digest),
        ]
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, raw_iterations, raw_salt, raw_digest = password_hash.split("$", 3)
        if algorithm != PASSWORD_ALGORITHM:
            return False
        iterations = int(raw_iterations)
        salt = _b64url_decode(raw_salt)
        expected_digest = _b64url_decode(raw_digest)
    except Exception:
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual_digest, expected_digest)


def create_access_token(
    *,
    subject: str,
    expires_in_seconds: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = int(time.time())
    expires_at = now + (
        expires_in_seconds
        if expires_in_seconds is not None
        else settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": subject,
        "iat": now,
        "exp": expires_at,
        **(extra_claims or {}),
    }
    signing_input = ".".join(
        [
            _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = hmac.new(
        settings.JWT_SECRET_KEY.get_secret_value().encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        raw_header, raw_payload, raw_signature = token.split(".", 2)
        signing_input = f"{raw_header}.{raw_payload}"
        expected_signature = hmac.new(
            settings.JWT_SECRET_KEY.get_secret_value().encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        provided_signature = _b64url_decode(raw_signature)
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise TokenError("Invalid token signature.")

        header = json.loads(_b64url_decode(raw_header))
        if header.get("alg") != JWT_ALGORITHM:
            raise TokenError("Unsupported token algorithm.")

        payload = json.loads(_b64url_decode(raw_payload))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise TokenError("Token expired.")
        if not payload.get("sub"):
            raise TokenError("Token subject missing.")
        return payload
    except TokenError:
        raise
    except Exception as exc:
        raise TokenError("Invalid token.") from exc
