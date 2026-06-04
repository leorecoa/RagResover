from dataclasses import dataclass, replace
from typing import Callable, Protocol

import httpx

from app.core.config import settings
from app.repositories.documents import DocumentRepository, SearchResult
from app.services.embeddings import embedding_service


@dataclass(frozen=True)
class RetrievalDiagnostics:
    tenant_id: str
    requested_top_k: int
    fetch_limit: int
    returned_count: int
    score_threshold: float | None
    metadata_filters: dict
    embedding_provider: str
    reranker_provider: str
    reranker_applied: bool

    def as_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "requested_top_k": self.requested_top_k,
            "fetch_limit": self.fetch_limit,
            "returned_count": self.returned_count,
            "score_threshold": self.score_threshold,
            "metadata_filters": self.metadata_filters,
            "embedding_provider": self.embedding_provider,
            "reranker_provider": self.reranker_provider,
            "reranker_applied": self.reranker_applied,
        }


@dataclass(frozen=True)
class RetrievalResult:
    results: list[SearchResult]
    diagnostics: RetrievalDiagnostics


class Reranker(Protocol):
    provider_name: str
    is_enabled: bool

    async def rerank(
        self,
        *,
        query: str,
        results: list[SearchResult],
        limit: int,
    ) -> list[SearchResult]:
        ...


class NoOpReranker:
    provider_name = "none"
    is_enabled = False

    async def rerank(
        self,
        *,
        query: str,
        results: list[SearchResult],
        limit: int,
    ) -> list[SearchResult]:
        return results[:limit]


class CohereReranker:
    provider_name = "cohere"
    is_enabled = True

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        client_factory: Callable[[], httpx.AsyncClient] | None = None,
    ):
        self.api_key = api_key
        self.model = model
        self.client_factory = client_factory or self._default_client_factory

    def _default_client_factory(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url="https://api.cohere.com",
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    async def rerank(
        self,
        *,
        query: str,
        results: list[SearchResult],
        limit: int,
    ) -> list[SearchResult]:
        if not results:
            return []

        documents = [result.content for result in results]
        try:
            async with self.client_factory() as client:
                response = await client.post(
                    "/v2/rerank",
                    json={
                        "model": self.model,
                        "query": query,
                        "documents": documents,
                        "top_n": min(limit, len(documents)),
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError("Cohere reranker unavailable.") from exc

        payload = response.json()
        ranked_items = payload.get("results")
        if not isinstance(ranked_items, list):
            raise RuntimeError("Cohere reranker response did not include results.")

        reranked: list[SearchResult] = []
        seen_indexes: set[int] = set()
        for item in ranked_items:
            if not isinstance(item, dict):
                continue
            index = item.get("index")
            relevance_score = item.get("relevance_score")
            if not isinstance(index, int) or index < 0 or index >= len(results):
                continue
            seen_indexes.add(index)
            score = (
                float(relevance_score)
                if isinstance(relevance_score, int | float)
                else results[index].score
            )
            reranked.append(replace(results[index], score=score))

        if len(reranked) < limit:
            reranked.extend(
                result
                for index, result in enumerate(results)
                if index not in seen_indexes
            )

        return reranked[:limit]


def create_reranker() -> Reranker:
    if settings.RERANKER_PROVIDER == "none":
        return NoOpReranker()

    if settings.RERANKER_PROVIDER == "cohere":
        api_key = (
            settings.COHERE_API_KEY.get_secret_value().strip()
            if settings.COHERE_API_KEY
            else ""
        )
        if not api_key:
            raise RuntimeError("COHERE_API_KEY must be configured when RERANKER_PROVIDER=cohere")
        return CohereReranker(
            api_key=api_key,
            model=settings.COHERE_RERANK_MODEL,
        )

    raise RuntimeError(f"Unsupported reranker provider: {settings.RERANKER_PROVIDER}")


class RetrievalService:
    def __init__(self, reranker: Reranker | None = None):
        self.reranker = reranker or create_reranker()

    async def retrieve(
        self,
        *,
        repository: DocumentRepository,
        tenant_id: str,
        query: str,
        top_k: int,
        score_threshold: float | None = None,
        metadata_filters: dict | None = None,
    ) -> RetrievalResult:
        effective_threshold = (
            score_threshold
            if score_threshold is not None
            else settings.RETRIEVAL_SCORE_THRESHOLD
        )
        normalized_filters = metadata_filters or {}
        fetch_limit = max(top_k, top_k * settings.RETRIEVAL_FETCH_MULTIPLIER)

        query_embedding = await embedding_service.embed_query(query)
        results = await repository.search_similar_chunks(
            tenant_id=tenant_id,
            embedding=query_embedding,
            limit=fetch_limit,
            score_threshold=effective_threshold,
            metadata_filters=normalized_filters,
        )
        reranked_results = await self.reranker.rerank(
            query=query,
            results=results,
            limit=top_k,
        )
        final_results = reranked_results[:top_k]

        return RetrievalResult(
            results=final_results,
            diagnostics=RetrievalDiagnostics(
                requested_top_k=top_k,
                tenant_id=tenant_id,
                fetch_limit=fetch_limit,
                returned_count=len(final_results),
                score_threshold=effective_threshold,
                metadata_filters=normalized_filters,
                embedding_provider=settings.EMBEDDING_PROVIDER,
                reranker_provider=self.reranker.provider_name,
                reranker_applied=self.reranker.is_enabled,
            ),
        )


retrieval_service = RetrievalService()
