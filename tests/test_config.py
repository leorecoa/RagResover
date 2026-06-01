import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_cors_origins_are_split_and_trimmed():
    settings = Settings(
        CORS_ALLOW_ORIGINS="http://localhost:3000, http://127.0.0.1:3000,,"
    )

    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_chunk_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(ValidationError):
        Settings(CHUNK_SIZE=100, CHUNK_OVERLAP=100)


def test_production_cors_cannot_allow_wildcard():
    with pytest.raises(ValidationError):
        Settings(APP_ENV="production", CORS_ALLOW_ORIGINS="*")
