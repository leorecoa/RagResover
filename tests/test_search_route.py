import logging
import unittest
import warnings
from unittest.mock import AsyncMock, patch
from uuid import UUID

warnings.filterwarnings(
    "ignore",
    message="Using `httpx` with `starlette.testclient` is deprecated.*",
)

from fastapi.testclient import TestClient

from app.core.app import create_app
from app.db.session import get_db_session
from app.repositories.documents import SearchResult


async def override_db_session():
    yield object()


class SearchRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        logging.getLogger("httpx").setLevel(logging.WARNING)

    def setUp(self):
        self.app = create_app()
        self.app.dependency_overrides[get_db_session] = override_db_session
        self.client = TestClient(self.app)

    def tearDown(self):
        self.app.dependency_overrides.clear()
        self.client.close()

    def test_search_returns_ranked_chunks(self):
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
            response = self.client.post("/search", json={"query": "manual", "top_k": 3})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["query"], "manual")
        self.assertEqual(response.json()["results"][0]["score"], 0.91)
        self.assertEqual(response.json()["results"][0]["file_name"], "manual.md")
        self.assertEqual(captured["embedding"], [0.1, 0.2])
        self.assertEqual(captured["limit"], 3)

    def test_search_returns_503_when_embedding_provider_is_unavailable(self):
        embedding_service = AsyncMock()
        embedding_service.embed_query.side_effect = RuntimeError("embedding provider unavailable")

        with patch("app.api.routes.search.embedding_service", embedding_service):
            response = self.client.post("/search", json={"query": "manual"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "embedding provider unavailable")

    def test_search_validates_top_k_range(self):
        response = self.client.post("/search", json={"query": "manual", "top_k": 0})

        self.assertEqual(response.status_code, 422)
