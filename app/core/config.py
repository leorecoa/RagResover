from typing import Literal, Optional

from pydantic import PostgresDsn, RedisDsn, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    DATABASE_URL: PostgresDsn = "postgresql+asyncpg://postgres:password@localhost:5432/ragdb"
    DATABASE_CONNECT_TIMEOUT_SECONDS: float = 2.0
    REDIS_URL: RedisDsn = "redis://localhost:6379"
    INGESTION_QUEUE_PROVIDER: Literal["inline", "redis"] = "inline"
    INGESTION_QUEUE_NAME: str = "ragresover:ingestion"
    INGESTION_JOB_MAX_ATTEMPTS: int = 3
    INGESTION_RETRY_DELAY_SECONDS: float = 1.0
    INGESTION_WORKER_POLL_TIMEOUT_SECONDS: int = 5
    INGESTION_STALE_JOB_TIMEOUT_SECONDS: int = 15 * 60
    DEBUG: bool = False
    CORS_ALLOW_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    ALLOW_ANONYMOUS_ACCESS: bool = True
    DEFAULT_TENANT_ID: str = "anonymous"
    API_AUTH_TOKEN: SecretStr = SecretStr("")
    ADMIN_ROLE_NAME: str = "admin"
    METRICS_REQUIRE_ADMIN: bool = False
    JWT_SECRET_KEY: SecretStr = SecretStr("dev-only-change-me")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    PASSWORD_HASH_ITERATIONS: int = 210_000

    STORAGE_ENDPOINT: str = "localhost:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: SecretStr = SecretStr("minioadmin")
    STORAGE_BUCKET_NAME: str = "documents"
    STORAGE_SECURE: bool = False
    STORAGE_REQUIRED: bool = False
    STORAGE_CONNECT_TIMEOUT_SECONDS: float = 1.0
    STORAGE_READ_TIMEOUT_SECONDS: float = 30.0
    STORAGE_MAX_RETRIES: int = 0

    OPENAI_API_KEY: SecretStr = SecretStr("")
    LLM_PROVIDER: Literal["openai", "ollama"] = "openai"
    EMBEDDING_PROVIDER: Literal["openai", "ollama"] = "openai"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "gpt-4o"
    CHAT_MAX_CONTEXT_CHARS: int = 6000
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDINGS_ENABLED: bool = True
    EMBEDDINGS_REQUIRED: bool = False
    EMBEDDING_DIMENSIONS: int = 1536
    TEMPERATURE: float = 0.0

    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    VECTOR_SEARCH_TOP_K: int = 5
    RETRIEVAL_SCORE_THRESHOLD: Optional[float] = None
    RETRIEVAL_FETCH_MULTIPLIER: int = 4
    RERANKER_PROVIDER: Literal["none", "cohere"] = "none"
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    ALLOWED_UPLOAD_CONTENT_TYPES: str = (
        "text/plain,text/markdown,text/html,application/xhtml+xml,application/json,application/pdf,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    COHERE_API_KEY: Optional[SecretStr] = None
    COHERE_RERANK_MODEL: str = "rerank-v4.0-pro"

    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: Optional[SecretStr] = None

    @field_validator("TEMPERATURE")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @field_validator("DEBUG", mode="before")
    @classmethod
    def validate_debug(cls, v):
        if isinstance(v, str) and v.lower() == "release":
            return False
        return v

    @model_validator(mode="after")
    def validate_rag_settings(self):
        if self.CHUNK_SIZE <= 0:
            raise ValueError("CHUNK_SIZE must be greater than 0")
        if self.CHUNK_OVERLAP < 0:
            raise ValueError("CHUNK_OVERLAP must be greater than or equal to 0")
        if self.CHUNK_OVERLAP >= self.CHUNK_SIZE:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")
        if self.VECTOR_SEARCH_TOP_K <= 0:
            raise ValueError("VECTOR_SEARCH_TOP_K must be greater than 0")
        if (
            self.RETRIEVAL_SCORE_THRESHOLD is not None
            and not -1.0 <= self.RETRIEVAL_SCORE_THRESHOLD <= 1.0
        ):
            raise ValueError("RETRIEVAL_SCORE_THRESHOLD must be between -1.0 and 1.0")
        if self.RETRIEVAL_FETCH_MULTIPLIER <= 0:
            raise ValueError("RETRIEVAL_FETCH_MULTIPLIER must be greater than 0")
        if self.MAX_UPLOAD_BYTES <= 0:
            raise ValueError("MAX_UPLOAD_BYTES must be greater than 0")
        if self.EMBEDDING_DIMENSIONS <= 0:
            raise ValueError("EMBEDDING_DIMENSIONS must be greater than 0")
        if self.CHAT_MAX_CONTEXT_CHARS <= 0:
            raise ValueError("CHAT_MAX_CONTEXT_CHARS must be greater than 0")
        if self.STORAGE_CONNECT_TIMEOUT_SECONDS <= 0:
            raise ValueError("STORAGE_CONNECT_TIMEOUT_SECONDS must be greater than 0")
        if self.STORAGE_READ_TIMEOUT_SECONDS <= 0:
            raise ValueError("STORAGE_READ_TIMEOUT_SECONDS must be greater than 0")
        if self.STORAGE_MAX_RETRIES < 0:
            raise ValueError("STORAGE_MAX_RETRIES must be greater than or equal to 0")
        if self.DATABASE_CONNECT_TIMEOUT_SECONDS <= 0:
            raise ValueError("DATABASE_CONNECT_TIMEOUT_SECONDS must be greater than 0")
        if not self.INGESTION_QUEUE_NAME.strip():
            raise ValueError("INGESTION_QUEUE_NAME must not be empty")
        if self.INGESTION_JOB_MAX_ATTEMPTS <= 0:
            raise ValueError("INGESTION_JOB_MAX_ATTEMPTS must be greater than 0")
        if self.INGESTION_RETRY_DELAY_SECONDS < 0:
            raise ValueError("INGESTION_RETRY_DELAY_SECONDS must be greater than or equal to 0")
        if self.INGESTION_WORKER_POLL_TIMEOUT_SECONDS <= 0:
            raise ValueError("INGESTION_WORKER_POLL_TIMEOUT_SECONDS must be greater than 0")
        if self.INGESTION_STALE_JOB_TIMEOUT_SECONDS <= 0:
            raise ValueError("INGESTION_STALE_JOB_TIMEOUT_SECONDS must be greater than 0")
        if self.RERANKER_PROVIDER == "cohere" and not (
            self.COHERE_API_KEY and self.COHERE_API_KEY.get_secret_value().strip()
        ):
            raise ValueError("COHERE_API_KEY must be configured when RERANKER_PROVIDER=cohere")
        if not self.COHERE_RERANK_MODEL.strip():
            raise ValueError("COHERE_RERANK_MODEL must not be empty")
        if not self.DEFAULT_TENANT_ID.strip():
            raise ValueError("DEFAULT_TENANT_ID must not be empty")
        if not self.ADMIN_ROLE_NAME.strip():
            raise ValueError("ADMIN_ROLE_NAME must not be empty")
        if self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
            raise ValueError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be greater than 0")
        if self.PASSWORD_HASH_ITERATIONS < 100_000:
            raise ValueError("PASSWORD_HASH_ITERATIONS must be at least 100000")
        if self.is_production and self.ALLOW_ANONYMOUS_ACCESS:
            raise ValueError("ALLOW_ANONYMOUS_ACCESS must be false in production")
        if self.is_production and self.JWT_SECRET_KEY.get_secret_value() == "dev-only-change-me":
            raise ValueError("JWT_SECRET_KEY must be changed in production")
        if self.is_production and "*" in self.cors_origins:
            raise ValueError("CORS_ALLOW_ORIGINS cannot contain '*' in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def storage_required(self) -> bool:
        return self.STORAGE_REQUIRED or self.is_production

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ALLOW_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def allowed_upload_content_types(self) -> set[str]:
        return {
            content_type.strip().lower()
            for content_type in self.ALLOWED_UPLOAD_CONTENT_TYPES.split(",")
            if content_type.strip()
        }

    @property
    def has_openai_api_key(self) -> bool:
        return bool(self.OPENAI_API_KEY.get_secret_value().strip())

    @property
    def uses_openai(self) -> bool:
        return self.LLM_PROVIDER == "openai" or self.EMBEDDING_PROVIDER == "openai"

    @property
    def has_api_auth_token(self) -> bool:
        return bool(self.API_AUTH_TOKEN.get_secret_value().strip())


settings = Settings()
