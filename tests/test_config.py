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


def test_cohere_reranker_requires_api_key():
    with pytest.raises(ValidationError, match="COHERE_API_KEY"):
        Settings(RERANKER_PROVIDER="cohere", COHERE_API_KEY="")


def test_cohere_reranker_accepts_api_key_and_model():
    settings = Settings(
        RERANKER_PROVIDER="cohere",
        COHERE_API_KEY="cohere-key",
        COHERE_RERANK_MODEL="rerank-v4.0-pro",
    )

    assert settings.RERANKER_PROVIDER == "cohere"
    assert settings.COHERE_RERANK_MODEL == "rerank-v4.0-pro"


def test_metrics_admin_protection_requires_api_token():
    with pytest.raises(ValidationError, match="API_AUTH_TOKEN"):
        Settings(METRICS_REQUIRE_ADMIN=True, API_AUTH_TOKEN="")
