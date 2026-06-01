from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.repositories.documents import SearchResult
from app.services.chat import ChatAnswer
from app.services.retrieval import RetrievalDiagnostics, RetrievalResult


def test_chat_returns_answer_with_sources(client_with_fake_db):
    search_result = SearchResult(
        chunk_id=UUID("44444444-4444-4444-4444-444444444444"),
        document_id=UUID("55555555-5555-5555-5555-555555555555"),
        tenant_id="tenant-a",
        file_name="policy.md",
        content="Politica interna recuperada",
        score=0.88,
        metadata={"source": "policy.md"},
    )
    chat_service = AsyncMock()
    chat_service.answer_question.return_value = ChatAnswer(answer="Resposta com fonte [1].")
    retrieval_service = AsyncMock()
    retrieval_service.retrieve.return_value = RetrievalResult(
        results=[search_result],
        diagnostics=RetrievalDiagnostics(
            tenant_id="anonymous",
            requested_top_k=2,
            fetch_limit=8,
            returned_count=1,
            score_threshold=None,
            metadata_filters={},
            embedding_provider="ollama",
            reranker_provider="none",
            reranker_applied=False,
        ),
    )

    with (
        patch("app.api.routes.chat.retrieval_service", retrieval_service),
        patch("app.api.routes.chat.chat_service", chat_service),
    ):
        response = client_with_fake_db.post(
            "/chat",
            json={"question": "Qual e a politica?", "top_k": 2},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "Qual e a politica?"
    assert payload["answer"] == "Resposta com fonte [1]."
    assert payload["sources"][0]["index"] == 1
    assert payload["sources"][0]["file_name"] == "policy.md"
    assert payload["sources"][0]["excerpt"] == "Politica interna recuperada"
    chat_service.answer_question.assert_awaited_once()
    retrieval_service.retrieve.assert_awaited_once()


def test_chat_returns_clear_message_when_no_context_is_found(client_with_fake_db):
    chat_service = AsyncMock()
    retrieval_service = AsyncMock()
    retrieval_service.retrieve.return_value = RetrievalResult(
        results=[],
        diagnostics=RetrievalDiagnostics(
            tenant_id="anonymous",
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

    with (
        patch("app.api.routes.chat.retrieval_service", retrieval_service),
        patch("app.api.routes.chat.chat_service", chat_service),
    ):
        response = client_with_fake_db.post("/chat", json={"question": "Existe contexto?"})

    assert response.status_code == 200
    assert response.json()["sources"] == []
    assert (
        response.json()["answer"]
        == "Nao encontrei contexto suficiente nos documentos indexados."
    )
    chat_service.answer_question.assert_not_awaited()


def test_chat_returns_503_when_embedding_provider_is_unavailable(client_with_fake_db):
    retrieval_service = AsyncMock()
    retrieval_service.retrieve.side_effect = RuntimeError("embedding provider unavailable")

    with patch("app.api.routes.chat.retrieval_service", retrieval_service):
        response = client_with_fake_db.post("/chat", json={"question": "Qual e a politica?"})

    assert response.status_code == 503
    assert response.json()["detail"] == "embedding provider unavailable"


def test_chat_includes_retrieval_diagnostics_when_debug_is_enabled(
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
            score_threshold=0.8,
            metadata_filters={"section": "Policy"},
            embedding_provider="ollama",
            reranker_provider="none",
            reranker_applied=False,
        ),
    )
    monkeypatch.setattr("app.api.routes.chat.settings.DEBUG", True)

    with patch("app.api.routes.chat.retrieval_service", retrieval_service):
        response = client_with_fake_db.post(
            "/chat",
            json={
                "question": "Existe contexto?",
                "score_threshold": 0.8,
                "metadata_filters": {"section": "Policy"},
            },
        )

    assert response.status_code == 200
    assert response.json()["diagnostics"]["score_threshold"] == 0.8
    assert response.json()["diagnostics"]["metadata_filters"] == {"section": "Policy"}


def test_chat_uses_tenant_header_for_retrieval(client_with_fake_db):
    retrieval_service = AsyncMock()
    retrieval_service.retrieve.return_value = RetrievalResult(
        results=[],
        diagnostics=RetrievalDiagnostics(
            tenant_id="tenant-b",
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

    with patch("app.api.routes.chat.retrieval_service", retrieval_service):
        response = client_with_fake_db.post(
            "/chat",
            json={"question": "Existe contexto?"},
            headers={"X-Tenant-ID": "tenant-b"},
        )

    assert response.status_code == 200
    assert retrieval_service.retrieve.await_args.kwargs["tenant_id"] == "tenant-b"
