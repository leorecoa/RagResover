from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.repositories.documents import SearchResult
from app.services.retrieval import RetrievalDiagnostics, RetrievalResult


def test_search_returns_ranked_chunks(client_with_fake_db):
    result = SearchResult(
        chunk_id=UUID("22222222-2222-2222-2222-222222222222"),
        document_id=UUID("33333333-3333-3333-3333-333333333333"),
        tenant_id="tenant-a",
        file_name="manual.md",
        content="Conteudo recuperado",
        score=0.91,
        metadata={"source": "manual.md"},
    )
    retrieval_service = AsyncMock()
    retrieval_service.retrieve.return_value = RetrievalResult(
        results=[result],
        diagnostics=RetrievalDiagnostics(
            tenant_id="anonymous",
            requested_top_k=3,
            fetch_limit=12,
            returned_count=1,
            score_threshold=None,
            metadata_filters={},
            embedding_provider="ollama",
            reranker_provider="none",
            reranker_applied=False,
        ),
    )

    with patch("app.api.routes.search.retrieval_service", retrieval_service):
        response = client_with_fake_db.post("/search", json={"query": "manual", "top_k": 3})

    assert response.status_code == 200
    assert response.json()["query"] == "manual"
    assert response.json()["results"][0]["score"] == 0.91
    assert response.json()["results"][0]["file_name"] == "manual.md"
    retrieval_service.retrieve.assert_awaited_once()
    call_kwargs = retrieval_service.retrieve.await_args.kwargs
    assert call_kwargs["query"] == "manual"
    assert call_kwargs["top_k"] == 3
    assert call_kwargs["tenant_id"] == "anonymous"


def test_search_returns_503_when_embedding_provider_is_unavailable(client_with_fake_db):
    retrieval_service = AsyncMock()
    retrieval_service.retrieve.side_effect = RuntimeError("embedding provider unavailable")

    with patch("app.api.routes.search.retrieval_service", retrieval_service):
        response = client_with_fake_db.post("/search", json={"query": "manual"})

    assert response.status_code == 503
    assert response.json()["detail"] == "embedding provider unavailable"


def test_search_validates_top_k_range(client_with_fake_db):
    response = client_with_fake_db.post("/search", json={"query": "manual", "top_k": 0})

    assert response.status_code == 422


def test_search_passes_threshold_and_metadata_filters_to_retrieval(client_with_fake_db):
    retrieval_service = AsyncMock()
    retrieval_service.retrieve.return_value = RetrievalResult(
        results=[],
        diagnostics=RetrievalDiagnostics(
            tenant_id="anonymous",
            requested_top_k=5,
            fetch_limit=20,
            returned_count=0,
            score_threshold=0.72,
            metadata_filters={"source": "manual.pdf"},
            embedding_provider="ollama",
            reranker_provider="none",
            reranker_applied=False,
        ),
    )

    with patch("app.api.routes.search.retrieval_service", retrieval_service):
        response = client_with_fake_db.post(
            "/search",
            json={
                "query": "manual",
                "score_threshold": 0.72,
                "metadata_filters": {"source": "manual.pdf"},
            },
        )

    assert response.status_code == 200
    call_kwargs = retrieval_service.retrieve.await_args.kwargs
    assert call_kwargs["score_threshold"] == 0.72
    assert call_kwargs["metadata_filters"] == {"source": "manual.pdf"}


def test_search_includes_diagnostics_only_when_debug_is_enabled(
    client_with_fake_db,
    monkeypatch,
):
    retrieval_service = AsyncMock()
    retrieval_service.retrieve.return_value = RetrievalResult(
        results=[],
        diagnostics=RetrievalDiagnostics(
            tenant_id="anonymous",
            requested_top_k=5,
            fetch_limit=20,
            returned_count=0,
            score_threshold=0.7,
            metadata_filters={"source": "manual.pdf"},
            embedding_provider="ollama",
            reranker_provider="none",
            reranker_applied=False,
        ),
    )
    monkeypatch.setattr("app.api.routes.search.settings.DEBUG", True)

    with patch("app.api.routes.search.retrieval_service", retrieval_service):
        response = client_with_fake_db.post("/search", json={"query": "manual"})

    assert response.status_code == 200
    assert response.json()["diagnostics"]["score_threshold"] == 0.7
    assert response.json()["diagnostics"]["metadata_filters"] == {"source": "manual.pdf"}


def test_search_uses_tenant_header_for_retrieval(client_with_fake_db):
    retrieval_service = AsyncMock()
    retrieval_service.retrieve.return_value = RetrievalResult(
        results=[],
        diagnostics=RetrievalDiagnostics(
            tenant_id="tenant-a",
            requested_top_k=5,
            fetch_limit=20,
            returned_count=0,
            score_threshold=None,
            metadata_filters={},
            embedding_provider="ollama",
            reranker_provider="none",
            reranker_applied=False,
        ),
    )

    with patch("app.api.routes.search.retrieval_service", retrieval_service):
        response = client_with_fake_db.post(
            "/search",
            json={"query": "manual"},
            headers={"X-Tenant-ID": "tenant-a"},
        )

    assert response.status_code == 200
    assert retrieval_service.retrieve.await_args.kwargs["tenant_id"] == "tenant-a"


def test_search_rejects_anonymous_access_when_disabled(
    client_with_fake_db,
    monkeypatch,
):
    monkeypatch.setattr("app.api.dependencies.auth.settings.ALLOW_ANONYMOUS_ACCESS", False)
    retrieval_service = AsyncMock()

    with patch("app.api.routes.search.retrieval_service", retrieval_service):
        response = client_with_fake_db.post("/search", json={"query": "manual"})

    assert response.status_code == 401
    assert "X-Tenant-ID obrigatorio" in response.json()["detail"]
    retrieval_service.retrieve.assert_not_awaited()
