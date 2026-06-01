from unittest.mock import AsyncMock, patch
from uuid import UUID

from langchain_core.documents import Document

from app.repositories.documents import PersistedIngestion
from app.services.ingestion import IngestionResult
from app.services.parsing import DocumentParsingError


def test_upload_rejects_unsupported_content_type(client_with_fake_db):
    response = client_with_fake_db.post(
        "/upload",
        files={"file": ("sample.bin", b"binary", "application/octet-stream")},
    )

    assert response.status_code == 415
    assert "Tipo de arquivo nao suportado" in response.json()["detail"]


def test_upload_accepts_pdf_and_docx_content_types_with_mocked_services(
    client_with_fake_db,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.routes.ingestion.settings.ALLOWED_UPLOAD_CONTENT_TYPES",
        (
            "text/plain,text/markdown,application/json,application/pdf,"
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
    )
    document_id = UUID("11111111-1111-1111-1111-111111111111")
    chunk = Document(page_content="Conteudo extraido", metadata={"source": "documento"})
    ingestion_service = AsyncMock()
    ingestion_service.ingest_raw_file.return_value = IngestionResult(
        chunks=[chunk],
        storage_path="s3://documents/documento",
        file_size=16,
    )
    embedding_service = AsyncMock()
    embedding_service.embed_texts.return_value = [[0.1, 0.2]]

    class FakeDocumentRepository:
        def __init__(self, session):
            self.session = session

        async def persist_ingestion(self, **kwargs):
            return PersistedIngestion(document_id=document_id, chunks_count=1)

    with (
        patch("app.api.routes.ingestion.ingestion_service", ingestion_service),
        patch("app.api.routes.ingestion.embedding_service", embedding_service),
        patch("app.api.routes.ingestion.DocumentRepository", FakeDocumentRepository),
    ):
        pdf_response = client_with_fake_db.post(
            "/upload",
            files={"file": ("manual.pdf", b"fake pdf payload", "application/pdf")},
        )
        docx_response = client_with_fake_db.post(
            "/upload",
            files={
                "file": (
                    "manual.docx",
                    b"fake docx payload",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )

    assert pdf_response.status_code == 200
    assert docx_response.status_code == 200
    assert ingestion_service.ingest_raw_file.await_count == 2


def test_upload_rejects_empty_file(client_with_fake_db):
    response = client_with_fake_db.post(
        "/upload",
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Arquivo vazio nao pode ser processado."


def test_upload_returns_clear_error_when_document_cannot_be_parsed(
    client_with_fake_db,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.routes.ingestion.settings.ALLOWED_UPLOAD_CONTENT_TYPES",
        "application/pdf",
    )
    ingestion_service = AsyncMock()
    ingestion_service.ingest_raw_file.side_effect = DocumentParsingError(
        "Arquivo PDF invalido, corrompido ou ilegivel."
    )

    with patch("app.api.routes.ingestion.ingestion_service", ingestion_service):
        response = client_with_fake_db.post(
            "/upload",
            files={"file": ("broken.pdf", b"%PDF-broken", "application/pdf")},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Arquivo PDF invalido, corrompido ou ilegivel."


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
    assert captured["tenant_id"] == "anonymous"
    assert captured["embeddings"] == [[0.1, 0.2], [0.3, 0.4]]


def test_upload_persists_document_with_tenant_header(client_with_fake_db):
    document_id = UUID("11111111-1111-1111-1111-111111111111")
    chunks = [Document(page_content="Trecho", metadata={"source": "note.txt"})]
    ingestion_service = AsyncMock()
    ingestion_service.ingest_raw_file.return_value = IngestionResult(
        chunks=chunks,
        storage_path="s3://documents/note.txt",
        file_size=6,
    )
    embedding_service = AsyncMock()
    embedding_service.embed_texts.return_value = [[0.1, 0.2]]
    captured = {}

    class FakeDocumentRepository:
        def __init__(self, session):
            self.session = session

        async def persist_ingestion(self, **kwargs):
            captured.update(kwargs)
            return PersistedIngestion(document_id=document_id, chunks_count=1)

    with (
        patch("app.api.routes.ingestion.ingestion_service", ingestion_service),
        patch("app.api.routes.ingestion.embedding_service", embedding_service),
        patch("app.api.routes.ingestion.DocumentRepository", FakeDocumentRepository),
    ):
        response = client_with_fake_db.post(
            "/upload",
            files={"file": ("note.txt", b"Trecho", "text/plain")},
            headers={"X-Tenant-ID": "tenant-a"},
        )

    assert response.status_code == 200
    assert captured["tenant_id"] == "tenant-a"
