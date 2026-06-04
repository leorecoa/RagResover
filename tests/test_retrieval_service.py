from uuid import UUID

import anyio

import app.services.retrieval as retrieval_module
from app.repositories.documents import SearchResult
from app.services.retrieval import CohereReranker, RetrievalService, create_reranker


class FakeRepository:
    def __init__(self, results):
        self.results = results
        self.calls = []

    async def search_similar_chunks(
        self,
        *,
        tenant_id,
        embedding,
        limit,
        score_threshold=None,
        metadata_filters=None,
    ):
        self.calls.append(
            {
                "embedding": embedding,
                "tenant_id": tenant_id,
                "limit": limit,
                "score_threshold": score_threshold,
                "metadata_filters": metadata_filters,
            }
        )
        return self.results


class FakeEmbeddingService:
    async def embed_query(self, query):
        return [0.1, 0.2, 0.3]


class FakeReranker:
    provider_name = "fake"
    is_enabled = True

    async def rerank(self, *, query, results, limit):
        return sorted(results, key=lambda item: item.score, reverse=True)[:limit]


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeCohereClient:
    def __init__(self, payload):
        self.payload = payload
        self.requests = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def post(self, path, json):
        self.requests.append({"path": path, "json": json})
        return FakeResponse(self.payload)


def make_result(index: int, score: float) -> SearchResult:
    return SearchResult(
        chunk_id=UUID(f"00000000-0000-0000-0000-{index:012d}"),
        document_id=UUID("99999999-9999-9999-9999-999999999999"),
        tenant_id="tenant-a",
        file_name=f"file-{index}.md",
        content=f"content-{index}",
        score=score,
        metadata={"source": f"file-{index}.md"},
    )


def test_retrieval_service_passes_threshold_and_metadata_filters_to_repository(monkeypatch):
    monkeypatch.setattr(retrieval_module, "embedding_service", FakeEmbeddingService())
    monkeypatch.setattr(retrieval_module.settings, "RETRIEVAL_FETCH_MULTIPLIER", 4)
    repository = FakeRepository([make_result(1, 0.9)])
    service = RetrievalService()

    async def call_service():
        return await service.retrieve(
            repository=repository,
            tenant_id="tenant-a",
            query="manual",
            top_k=3,
            score_threshold=0.75,
            metadata_filters={"source": "manual.pdf", "page": 1},
        )

    result = anyio.run(call_service)

    assert repository.calls == [
        {
            "embedding": [0.1, 0.2, 0.3],
            "tenant_id": "tenant-a",
            "limit": 12,
            "score_threshold": 0.75,
            "metadata_filters": {"source": "manual.pdf", "page": 1},
        }
    ]
    assert result.results[0].score == 0.9
    assert result.diagnostics.as_dict()["fetch_limit"] == 12
    assert result.diagnostics.as_dict()["metadata_filters"] == {
        "source": "manual.pdf",
        "page": 1,
    }


def test_retrieval_service_uses_default_score_threshold_from_settings(monkeypatch):
    monkeypatch.setattr(retrieval_module, "embedding_service", FakeEmbeddingService())
    monkeypatch.setattr(retrieval_module.settings, "RETRIEVAL_SCORE_THRESHOLD", 0.6)
    repository = FakeRepository([])
    service = RetrievalService()

    async def call_service():
        return await service.retrieve(
            repository=repository,
            tenant_id="tenant-a",
            query="manual",
            top_k=2,
        )

    result = anyio.run(call_service)

    assert repository.calls[0]["score_threshold"] == 0.6
    assert result.diagnostics.as_dict()["score_threshold"] == 0.6


def test_retrieval_service_reranker_interface_can_reorder_results(monkeypatch):
    monkeypatch.setattr(retrieval_module, "embedding_service", FakeEmbeddingService())
    repository = FakeRepository(
        [
            make_result(1, 0.2),
            make_result(2, 0.95),
            make_result(3, 0.7),
        ]
    )
    service = RetrievalService(reranker=FakeReranker())

    async def call_service():
        return await service.retrieve(
            repository=repository,
            tenant_id="tenant-a",
            query="manual",
            top_k=2,
        )

    result = anyio.run(call_service)

    assert [item.score for item in result.results] == [0.95, 0.7]
    assert result.diagnostics.as_dict()["tenant_id"] == "tenant-a"
    assert result.diagnostics.as_dict()["reranker_provider"] == "fake"
    assert result.diagnostics.as_dict()["reranker_applied"] is True


def test_create_reranker_uses_cohere_provider(monkeypatch):
    monkeypatch.setattr(retrieval_module.settings, "RERANKER_PROVIDER", "cohere")
    monkeypatch.setattr(retrieval_module.settings, "COHERE_RERANK_MODEL", "rerank-v4.0-pro")
    monkeypatch.setattr(
        retrieval_module.settings,
        "COHERE_API_KEY",
        type("FakeSecret", (), {"get_secret_value": lambda self: "cohere-key"})(),
    )

    reranker = create_reranker()

    assert isinstance(reranker, CohereReranker)
    assert reranker.provider_name == "cohere"
    assert reranker.is_enabled is True


def test_cohere_reranker_reorders_results_and_uses_relevance_score():
    fake_client = FakeCohereClient(
        {
            "results": [
                {"index": 2, "relevance_score": 0.99},
                {"index": 0, "relevance_score": 0.72},
            ]
        }
    )
    reranker = CohereReranker(
        api_key="cohere-key",
        model="rerank-v4.0-pro",
        client_factory=lambda: fake_client,
    )
    results = [make_result(1, 0.2), make_result(2, 0.6), make_result(3, 0.4)]

    async def call_reranker():
        return await reranker.rerank(
            query="manual",
            results=results,
            limit=2,
        )

    reranked = anyio.run(call_reranker)

    assert [item.chunk_id for item in reranked] == [
        results[2].chunk_id,
        results[0].chunk_id,
    ]
    assert [item.score for item in reranked] == [0.99, 0.72]
    assert fake_client.requests == [
        {
            "path": "/v2/rerank",
            "json": {
                "model": "rerank-v4.0-pro",
                "query": "manual",
                "documents": ["content-1", "content-2", "content-3"],
                "top_n": 2,
            },
        }
    ]
