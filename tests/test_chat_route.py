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
from app.services.chat import ChatAnswer


async def override_db_session():
    yield object()


class ChatRouteTests(unittest.TestCase):
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

    def test_chat_returns_answer_with_sources(self):
        search_result = SearchResult(
            chunk_id=UUID("44444444-4444-4444-4444-444444444444"),
            document_id=UUID("55555555-5555-5555-5555-555555555555"),
            file_name="policy.md",
            content="Politica interna recuperada",
            score=0.88,
            metadata={"source": "policy.md"},
        )
        embedding_service = AsyncMock()
        embedding_service.embed_query.return_value = [0.1, 0.2]
        chat_service = AsyncMock()
        chat_service.answer_question.return_value = ChatAnswer(answer="Resposta com fonte [1].")

        class FakeDocumentRepository:
            def __init__(self, session):
                self.session = session

            async def search_similar_chunks(self, *, embedding, limit):
                self.embedding = embedding
                self.limit = limit
                return [search_result]

        with (
            patch("app.api.routes.chat.embedding_service", embedding_service),
            patch("app.api.routes.chat.chat_service", chat_service),
            patch("app.api.routes.chat.DocumentRepository", FakeDocumentRepository),
        ):
            response = self.client.post(
                "/chat",
                json={"question": "Qual e a politica?", "top_k": 2},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["question"], "Qual e a politica?")
        self.assertEqual(payload["answer"], "Resposta com fonte [1].")
        self.assertEqual(payload["sources"][0]["index"], 1)
        self.assertEqual(payload["sources"][0]["file_name"], "policy.md")
        self.assertEqual(payload["sources"][0]["excerpt"], "Politica interna recuperada")
        chat_service.answer_question.assert_awaited_once()

    def test_chat_returns_clear_message_when_no_context_is_found(self):
        embedding_service = AsyncMock()
        embedding_service.embed_query.return_value = [0.1, 0.2]
        chat_service = AsyncMock()

        class FakeDocumentRepository:
            def __init__(self, session):
                self.session = session

            async def search_similar_chunks(self, *, embedding, limit):
                return []

        with (
            patch("app.api.routes.chat.embedding_service", embedding_service),
            patch("app.api.routes.chat.chat_service", chat_service),
            patch("app.api.routes.chat.DocumentRepository", FakeDocumentRepository),
        ):
            response = self.client.post("/chat", json={"question": "Existe contexto?"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sources"], [])
        self.assertEqual(
            response.json()["answer"],
            "Nao encontrei contexto suficiente nos documentos indexados.",
        )
        chat_service.answer_question.assert_not_awaited()

    def test_chat_returns_503_when_embedding_provider_is_unavailable(self):
        embedding_service = AsyncMock()
        embedding_service.embed_query.side_effect = RuntimeError("embedding provider unavailable")

        with patch("app.api.routes.chat.embedding_service", embedding_service):
            response = self.client.post("/chat", json={"question": "Qual e a politica?"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "embedding provider unavailable")
