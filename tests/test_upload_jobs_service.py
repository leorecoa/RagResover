from uuid import UUID

import anyio
from langchain_core.documents import Document

import app.services.upload_jobs as upload_jobs_module
from app.repositories.documents import PersistedIngestion
from app.services.ingestion import IngestionResult


JOB_ID = UUID("11111111-1111-1111-1111-111111111111")
DOCUMENT_ID = UUID("22222222-2222-2222-2222-222222222222")


class FakeSessionContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return False


def test_process_upload_job_marks_completed(monkeypatch):
    status_updates = []
    persist_kwargs = {}
    chunks = [Document(page_content="Trecho", metadata={"source": "note.txt"})]

    class FakeJobRepository:
        def __init__(self, session):
            self.session = session

        async def update_status(self, **kwargs):
            status_updates.append(kwargs)
            return object()

    class FakeDocumentRepository:
        def __init__(self, session):
            self.session = session

        async def persist_ingestion(self, **kwargs):
            persist_kwargs.update(kwargs)
            return PersistedIngestion(document_id=DOCUMENT_ID, chunks_count=1)

    ingestion_service = type(
        "FakeIngestionService",
        (),
        {
            "ingest_raw_file": staticmethod(
                lambda **kwargs: _async_value(
                    IngestionResult(
                        chunks=chunks,
                        storage_path="s3://documents/note.txt",
                        file_size=6,
                    )
                )
            )
        },
    )
    embedding_service = type(
        "FakeEmbeddingService",
        (),
        {"embed_texts": staticmethod(lambda texts: _async_value([[0.1, 0.2]]))},
    )

    monkeypatch.setattr(upload_jobs_module, "AsyncSessionLocal", lambda: FakeSessionContext())
    monkeypatch.setattr(upload_jobs_module, "IngestionJobRepository", FakeJobRepository)
    monkeypatch.setattr(upload_jobs_module, "DocumentRepository", FakeDocumentRepository)
    monkeypatch.setattr(upload_jobs_module, "ingestion_service", ingestion_service)
    monkeypatch.setattr(upload_jobs_module, "embedding_service", embedding_service)

    async def call_service():
        await upload_jobs_module.process_upload_job(
            job_id=JOB_ID,
            tenant_id="tenant-a",
            file_name="note.txt",
            file_bytes=b"Trecho",
            content_type="text/plain",
        )

    anyio.run(call_service)

    assert status_updates[0] == {"job_id": JOB_ID, "status": "processing"}
    assert status_updates[1] == {
        "job_id": JOB_ID,
        "status": "completed",
        "document_id": DOCUMENT_ID,
        "error_message": None,
    }
    assert persist_kwargs["tenant_id"] == "tenant-a"
    assert persist_kwargs["file_name"] == "note.txt"
    assert persist_kwargs["embeddings"] == [[0.1, 0.2]]


def test_process_upload_job_marks_failed_on_error(monkeypatch):
    status_updates = []

    class FakeJobRepository:
        def __init__(self, session):
            self.session = session

        async def update_status(self, **kwargs):
            status_updates.append(kwargs)
            return object()

    class FakeIngestionService:
        @staticmethod
        async def ingest_raw_file(**kwargs):
            raise RuntimeError("parser unavailable")

    monkeypatch.setattr(upload_jobs_module, "AsyncSessionLocal", lambda: FakeSessionContext())
    monkeypatch.setattr(upload_jobs_module, "IngestionJobRepository", FakeJobRepository)
    monkeypatch.setattr(upload_jobs_module, "ingestion_service", FakeIngestionService)

    async def call_service():
        await upload_jobs_module.process_upload_job(
            job_id=JOB_ID,
            tenant_id="tenant-a",
            file_name="broken.pdf",
            file_bytes=b"broken",
            content_type="application/pdf",
        )

    anyio.run(call_service)

    assert status_updates[0] == {"job_id": JOB_ID, "status": "processing"}
    assert status_updates[1] == {
        "job_id": JOB_ID,
        "status": "failed",
        "error_message": "parser unavailable",
    }


def test_process_upload_job_stops_when_job_is_missing(monkeypatch):
    status_updates = []
    ingest_called = False

    class FakeJobRepository:
        def __init__(self, session):
            self.session = session

        async def update_status(self, **kwargs):
            status_updates.append(kwargs)
            return None

    class FakeIngestionService:
        @staticmethod
        async def ingest_raw_file(**kwargs):
            nonlocal ingest_called
            ingest_called = True

    monkeypatch.setattr(upload_jobs_module, "AsyncSessionLocal", lambda: FakeSessionContext())
    monkeypatch.setattr(upload_jobs_module, "IngestionJobRepository", FakeJobRepository)
    monkeypatch.setattr(upload_jobs_module, "ingestion_service", FakeIngestionService)

    async def call_service():
        await upload_jobs_module.process_upload_job(
            job_id=JOB_ID,
            tenant_id="tenant-a",
            file_name="missing.txt",
            file_bytes=b"missing",
            content_type="text/plain",
        )

    anyio.run(call_service)

    assert status_updates == [{"job_id": JOB_ID, "status": "processing"}]
    assert ingest_called is False


async def _async_value(value):
    return value
