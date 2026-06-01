from uuid import UUID

import anyio

import app.services.chat as chat_module
import app.services.embeddings as embeddings_module
from app.repositories.documents import SearchResult
from app.services.chat import ChatAnswer, ChatService
from app.services.embeddings import EmbeddingService


def test_embedding_service_disables_openai_without_client(monkeypatch):
    monkeypatch.setattr(embeddings_module.settings, "EMBEDDINGS_ENABLED", True)
    monkeypatch.setattr(embeddings_module.settings, "EMBEDDING_PROVIDER", "openai")
    service = EmbeddingService()
    service.openai_client = None

    assert service.is_enabled is False


def test_embedding_service_enables_ollama_without_openai_key(monkeypatch):
    monkeypatch.setattr(embeddings_module.settings, "EMBEDDINGS_ENABLED", True)
    monkeypatch.setattr(embeddings_module.settings, "EMBEDDING_PROVIDER", "ollama")
    service = EmbeddingService()
    service.openai_client = None

    assert service.is_enabled is True


def test_embedding_service_returns_empty_vectors_when_optional_embeddings_are_disabled(
    monkeypatch,
):
    monkeypatch.setattr(embeddings_module.settings, "EMBEDDINGS_ENABLED", False)
    monkeypatch.setattr(embeddings_module.settings, "EMBEDDINGS_REQUIRED", False)
    service = EmbeddingService()

    result = anyio.run(service.embed_texts, ["primeiro", "segundo"])

    assert result == [None, None]


def test_embedding_service_dispatches_to_configured_provider_without_network(monkeypatch):
    monkeypatch.setattr(embeddings_module.settings, "EMBEDDINGS_ENABLED", True)
    monkeypatch.setattr(embeddings_module.settings, "EMBEDDING_PROVIDER", "ollama")
    service = EmbeddingService()

    async def fake_ollama_embedding(texts):
        return [[float(index)] for index, _ in enumerate(texts)]

    monkeypatch.setattr(service, "_embed_texts_ollama", fake_ollama_embedding)

    result = anyio.run(service.embed_texts, ["primeiro", "segundo"])

    assert result == [[0.0], [1.0]]


def test_chat_service_disables_openai_without_client(monkeypatch):
    monkeypatch.setattr(chat_module.settings, "LLM_PROVIDER", "openai")
    service = ChatService()
    service.openai_client = None

    assert service.is_enabled is False


def test_chat_service_enables_ollama_without_openai_key(monkeypatch):
    monkeypatch.setattr(chat_module.settings, "LLM_PROVIDER", "ollama")
    service = ChatService()
    service.openai_client = None

    assert service.is_enabled is True


def test_chat_service_dispatches_to_configured_provider_without_network(monkeypatch):
    monkeypatch.setattr(chat_module.settings, "LLM_PROVIDER", "ollama")
    service = ChatService()
    search_result = SearchResult(
        chunk_id=UUID("66666666-6666-6666-6666-666666666666"),
        document_id=UUID("77777777-7777-7777-7777-777777777777"),
        tenant_id="tenant-a",
        file_name="manual.md",
        content="Conteudo recuperado",
        score=0.9,
        metadata={"source": "manual.md"},
    )

    async def fake_ollama_answer(messages):
        assert messages[0]["role"] == "system"
        assert "Conteudo recuperado" in messages[1]["content"]
        return ChatAnswer(answer="Resposta fake [1].")

    monkeypatch.setattr(service, "_answer_with_ollama", fake_ollama_answer)

    async def call_service():
        return await service.answer_question(
            question="O que foi recuperado?",
            results=[search_result],
        )

    result = anyio.run(call_service)

    assert result.answer == "Resposta fake [1]."
