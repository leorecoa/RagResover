import logging

import httpx
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        self.openai_client = (
            AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())
            if settings.has_openai_api_key
            else None
        )

    @property
    def is_enabled(self) -> bool:
        if not settings.EMBEDDINGS_ENABLED:
            return False
        if settings.EMBEDDING_PROVIDER == "openai":
            return self.openai_client is not None
        if settings.EMBEDDING_PROVIDER == "ollama":
            return True
        return False

    async def embed_texts(self, texts: list[str]) -> list[list[float] | None]:
        if not texts:
            return []
        if not self.is_enabled:
            if settings.EMBEDDINGS_REQUIRED:
                raise RuntimeError("Embeddings are required, but no embedding provider is configured.")
            logger.warning("Embeddings disabled or unavailable; returning empty vectors.")
            return [None for _ in texts]

        if settings.EMBEDDING_PROVIDER == "openai":
            return await self._embed_texts_openai(texts)
        if settings.EMBEDDING_PROVIDER == "ollama":
            return await self._embed_texts_ollama(texts)

        raise RuntimeError(f"Unsupported embedding provider: {settings.EMBEDDING_PROVIDER}")

    async def embed_query(self, query: str) -> list[float]:
        if not self.is_enabled:
            raise RuntimeError("Query embeddings require a configured embedding provider.")
        embeddings = await self.embed_texts([query])
        embedding = embeddings[0] if embeddings else None
        if embedding is None:
            raise RuntimeError("Query embedding unavailable.")
        return embedding

    async def _embed_texts_openai(self, texts: list[str]) -> list[list[float]]:
        if self.openai_client is None:
            raise RuntimeError("OpenAI embeddings require OPENAI_API_KEY to be configured.")

        response = await self.openai_client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )
        return [item.embedding for item in response.data]

    async def _embed_texts_ollama(self, texts: list[str]) -> list[list[float]]:
        try:
            async with httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=60.0) as client:
                response = await client.post(
                    "/api/embed",
                    json={"model": settings.EMBEDDING_MODEL, "input": texts},
                )
                if response.status_code == 404:
                    return await self._embed_texts_ollama_legacy(client, texts)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                "Ollama embedding provider unavailable. Start Ollama and run "
                f"`ollama pull {settings.EMBEDDING_MODEL}`."
            ) from exc

        payload = response.json()
        embeddings = payload.get("embeddings")
        if not isinstance(embeddings, list):
            raise RuntimeError("Ollama embedding response did not include embeddings.")
        return embeddings

    async def _embed_texts_ollama_legacy(
        self,
        client: httpx.AsyncClient,
        texts: list[str],
    ) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for text in texts:
            try:
                response = await client.post(
                    "/api/embeddings",
                    json={"model": settings.EMBEDDING_MODEL, "prompt": text},
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise RuntimeError(
                    "Ollama legacy embedding provider unavailable. Start Ollama and run "
                    f"`ollama pull {settings.EMBEDDING_MODEL}`."
                ) from exc
            embedding = response.json().get("embedding")
            if not isinstance(embedding, list):
                raise RuntimeError("Ollama legacy embedding response did not include embedding.")
            embeddings.append(embedding)
        return embeddings


embedding_service = EmbeddingService()
