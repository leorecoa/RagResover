from unittest.mock import AsyncMock, patch
from uuid import UUID

from langchain_core.documents import Document

from app.repositories.documents import PersistedIngestion
from app.services.ingestion import IngestionResult


def test_upload_rejects_unsupported_content_type(client_with_fake_db):
    response = client_with_fake_db.post(
        "/upload",
        files={"file": ("sample.pdf", b"%PDF-1.4", "application/pdf")},
    )

    assert response.status_code == 415
    assert "Tipo de arquivo nao suportado" in response.json()["detail"]


def test_upload_rejects_empty_file(client_with_fake_db):
    response = client_with_fake_db.post(
        "/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Arquivo vazio nao pode ser processado."


def test_upload_processes_valid_text_file_with_mocked_services(client_with_fake_db):
    document_id = UUID("11111111-1111-1111-1111-111111111111")
    chunks = [
        Document(page_content="Primeiro trecho", metadata={"source": "note.txt"}),
        Document(page_content="Segundo trecho", metadata={"source": "note.txt"}),
    ]
    ingestion_service = AsyncMock()
    ingestion_service.ingest_raw_file.return_value = IngestionResult(
        chunks=chunks,
        storage_path="s3://documents/note.txt",
        file_size=27,
    )
    embedding_service = AsyncMock()
    embedding_service.embed_texts.return_value = [[0.1, 0.2], [0.3, 0.4]]
    captured = {}

    class FakeDocumentRepository:
        def __init__(self, session):
            captured["session"] = session

        async def persist_ingestion(self, **kwargs):
            captured.update(kwargs)
            return PersistedIngestion(
                document_id=document_id,
                chunks_count=len(kwargs["chunks"]),
            )

    with (
        patch("app.api.routes.ingestion.ingestion_service", ingestion_service),
        patch("app.api.routes.ingestion.embedding_service", embedding_service),
        patch("app.api.routes.ingestion.DocumentRepository", FakeDocumentRepository),
    ):
        response = client_with_fake_db.post(
            "/upload",
            files={"file": ("note.txt", b"Primeiro trecho\nSegundo trecho", "text/plain")},
        )

    assert response.status_code == 200
    assert response.json() == {
        "document_id": str(document_id),
        "filename": "note.txt",
        "status": "success",
        "chunks_count": 2,
        "message": "Documento processado e pronto para indexacao.",
    }
    ingestion_service.ingest_raw_file.assert_awaited_once()
    embedding_service.embed_texts.assert_awaited_once_with(
        ["Primeiro trecho", "Segundo trecho"]
    )
    assert captured["file_name"] == "note.txt"
    assert captured["content_type"] == "text/plain"
    assert captured["embeddings"] == [[0.1, 0.2], [0.3, 0.4]]
