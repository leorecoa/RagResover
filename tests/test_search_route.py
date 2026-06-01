from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.repositories.documents import SearchResult


def test_search_returns_ranked_chunks(client_with_fake_db):
    result = SearchResult(
        chunk_id=UUID("22222222-2222-2222-2222-222222222222"),
        document_id=UUID("33333333-3333-3333-3333-333333333333"),
        file_name="manual.md",
        content="Conteudo recuperado",
        score=0.91,
        metadata={"source": "manual.md"},
    )
    embedding_service = AsyncMock()
    embedding_service.embed_query.return_value = [0.1, 0.2]
    captured = {}

    class FakeDocumentRepository:
        def __init__(self, session):
            captured["session"] = session

        async def search_similar_chunks(self, *, embedding, limit):
            captured["embedding"] = embedding
            captured["limit"] = limit
            return [result]

    with (
        patch("app.api.routes.search.embedding_service", embedding_service),
        patch("app.api.routes.search.DocumentRepository", FakeDocumentRepository),
    ):
        response = client_with_fake_db.post("/search", json={"query": "manual", "top_k": 3})

    assert response.status_code == 200
    assert response.json()["query"] == "manual"
    assert response.json()["results"][0]["score"] == 0.91
    assert response.json()["results"][0]["file_name"] == "manual.md"
    assert captured["embedding"] == [0.1, 0.2]
    assert captured["limit"] == 3


def test_search_returns_503_when_embedding_provider_is_unavailable(client_with_fake_db):
    embedding_service = AsyncMock()
    embedding_service.embed_query.side_effect = RuntimeError("embedding provider unavailable")

    with patch("app.api.routes.search.embedding_service", embedding_service):
        response = client_with_fake_db.post("/search", json={"query": "manual"})

    assert response.status_code == 503
    assert response.json()["detail"] == "embedding provider unavailable"


def test_search_validates_top_k_range(client_with_fake_db):
    response = client_with_fake_db.post("/search", json={"query": "manual", "top_k": 0})

    assert response.status_code == 422
