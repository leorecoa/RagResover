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
    DEBUG: bool = False
    CORS_ALLOW_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

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
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    ALLOWED_UPLOAD_CONTENT_TYPES: str = (
        "text/plain,text/markdown,application/json,application/pdf,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    COHERE_API_KEY: Optional[SecretStr] = None

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


settings = Settings()
