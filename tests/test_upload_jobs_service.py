from datetime import datetime
from uuid import UUID

import anyio
from langchain_core.documents import Document

import app.services.upload_jobs as upload_jobs_module
from app.repositories.documents import PersistedIngestion
from app.repositories.ingestion_jobs import IngestionJobRecord
from app.services.ingestion import IngestionResult


JOB_ID = UUID("11111111-1111-1111-1111-111111111111")
DOCUMENT_ID = UUID("22222222-2222-2222-2222-222222222222")


class FakeSessionContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_job(*, attempts=1, max_attempts=3, raw_storage_path="s3://documents/note.txt"):
    return IngestionJobRecord(
        id=JOB_ID,
        tenant_id="tenant-a",
        file_name="note.txt",
        content_type="text/plain",
        file_size=6,
        raw_storage_path=raw_storage_path,
        status="processing",
        error_message=None,
        attempts=attempts,
        max_attempts=max_attempts,
        last_error=None,
        document_id=None,
        created_at=datetime(2026, 6, 1, 12, 0, 0),
        updated_at=datetime(2026, 6, 1, 12, 0, 0),
        started_at=datetime(2026, 6, 1, 12, 0, 1),
        finished_at=None,
    )


def test_process_queued_upload_job_marks_completed(monkeypatch):
    completed = {}
    persist_kwargs = {}
    chunks = [Document(page_content="Trecho", metadata={"source": "note.txt"})]

    class FakeJobRepository:
        def __init__(self, session):
            self.session = session

        async def start_attempt(self, **kwargs):
            assert kwargs["job_id"] == JOB_ID
            return make_job()

        async def complete_job(self, **kwargs):
            completed.update(kwargs)

    class FakeDocumentRepository:
        def __init__(self, session):
            self.session = session

        async def persist_ingestion(self, **kwargs):
            persist_kwargs.update(kwargs)
            return PersistedIngestion(document_id=DOCUMENT_ID, chunks_count=1)

    class FakeStorageService:
        @staticmethod
        async def download_file(storage_path):
            assert storage_path == "s3://documents/note.txt"
            return b"Trecho"

    ingestion_service = type(
        "FakeIngestionService",
        (),
        {
            "ingest_stored_file": staticmethod(
                lambda **kwargs: _async_value(
                    IngestionResult(
                        chunks=chunks,
                        storage_path=kwargs["storage_path"],
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
    monkeypatch.setattr(upload_jobs_module, "storage_service", FakeStorageService)
    monkeypatch.setattr(upload_jobs_module, "ingestion_service", ingestion_service)
    monkeypatch.setattr(upload_jobs_module, "embedding_service", embedding_service)

    async def call_service():
        await upload_jobs_module.process_queued_upload_job(job_id=JOB_ID)

    anyio.run(call_service)

    assert completed == {"job_id": JOB_ID, "document_id": DOCUMENT_ID}
    assert persist_kwargs["tenant_id"] == "tenant-a"
    assert persist_kwargs["file_name"] == "note.txt"
    assert persist_kwargs["storage_path"] == "s3://documents/note.txt"
    assert persist_kwargs["embeddings"] == [[0.1, 0.2]]


def test_process_queued_upload_job_retries_temporary_failure(monkeypatch):
    retry = {}
    queued = []

    class FakeJobRepository:
        def __init__(self, session):
            self.session = session

        async def start_attempt(self, **kwargs):
            return make_job(attempts=1, max_attempts=3)

        async def mark_retry_pending(self, **kwargs):
            retry.update(kwargs)
            return object()

    class FakeStorageService:
        @staticmethod
        async def download_file(storage_path):
            raise RuntimeError("storage unavailable")

    class FakeQueue:
        async def enqueue(self, job_id):
            queued.append(job_id)

    monkeypatch.setattr(upload_jobs_module, "AsyncSessionLocal", lambda: FakeSessionContext())
    monkeypatch.setattr(upload_jobs_module, "IngestionJobRepository", FakeJobRepository)
    monkeypatch.setattr(upload_jobs_module, "storage_service", FakeStorageService)
    monkeypatch.setattr(upload_jobs_module.settings, "INGESTION_RETRY_DELAY_SECONDS", 0)

    async def call_service():
        await upload_jobs_module.process_queued_upload_job(job_id=JOB_ID, queue=FakeQueue())

    anyio.run(call_service)

    assert retry == {"job_id": JOB_ID, "error_message": "storage unavailable"}
    assert queued == [JOB_ID]


def test_process_queued_upload_job_marks_failed_after_max_attempts(monkeypatch):
    failed = {}

    class FakeJobRepository:
        def __init__(self, session):
            self.session = session

        async def start_attempt(self, **kwargs):
            return make_job(attempts=3, max_attempts=3)

        async def fail_job(self, **kwargs):
            failed.update(kwargs)

    class FakeStorageService:
        @staticmethod
        async def download_file(storage_path):
            raise RuntimeError("parser unavailable")

    monkeypatch.setattr(upload_jobs_module, "AsyncSessionLocal", lambda: FakeSessionContext())
    monkeypatch.setattr(upload_jobs_module, "IngestionJobRepository", FakeJobRepository)
    monkeypatch.setattr(upload_jobs_module, "storage_service", FakeStorageService)

    async def call_service():
        await upload_jobs_module.process_queued_upload_job(job_id=JOB_ID)

    anyio.run(call_service)

    assert failed == {"job_id": JOB_ID, "error_message": "parser unavailable"}


def test_process_queued_upload_job_stops_when_job_is_missing(monkeypatch):
    started = []

    class FakeJobRepository:
        def __init__(self, session):
            self.session = session

        async def start_attempt(self, **kwargs):
            started.append(kwargs)
            return None

    class FakeStorageService:
        @staticmethod
        async def download_file(storage_path):
            raise AssertionError("download should not be called")

    monkeypatch.setattr(upload_jobs_module, "AsyncSessionLocal", lambda: FakeSessionContext())
    monkeypatch.setattr(upload_jobs_module, "IngestionJobRepository", FakeJobRepository)
    monkeypatch.setattr(upload_jobs_module, "storage_service", FakeStorageService)

    async def call_service():
        await upload_jobs_module.process_queued_upload_job(job_id=JOB_ID)

    anyio.run(call_service)

    assert started == [{"job_id": JOB_ID}]


async def _async_value(value):
    return value
