from dataclasses import dataclass
from typing import Protocol

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


class RetrievalService:
    def __init__(self, reranker: Reranker | None = None):
        self.reranker = reranker or NoOpReranker()

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
