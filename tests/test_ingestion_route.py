from datetime import datetime
from uuid import UUID

import pytest

from app.repositories.ingestion_jobs import IngestionJobRecord


JOB_ID = UUID("11111111-1111-1111-1111-111111111111")
DOCUMENT_ID = UUID("22222222-2222-2222-2222-222222222222")


def make_job(status="pending", tenant_id="anonymous", document_id=None, error_message=None):
    return IngestionJobRecord(
        id=JOB_ID,
        tenant_id=tenant_id,
        file_name="note.txt",
        content_type="text/plain",
        file_size=6,
        raw_storage_path="s3://documents/raw-note.txt",
        status=status,
        error_message=error_message,
        attempts=1 if status in {"processing", "completed", "failed"} else 0,
        max_attempts=3,
        last_error=error_message,
        document_id=document_id,
        created_at=datetime(2026, 6, 1, 12, 0, 0),
        updated_at=datetime(2026, 6, 1, 12, 0, 0),
        started_at=None,
        finished_at=None,
    )


def test_upload_rejects_unsupported_content_type(client_with_fake_db):
    response = client_with_fake_db.post(
        "/upload",
        files={"file": ("sample.bin", b"binary", "application/octet-stream")},
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


def test_upload_creates_job_and_enqueues_processing(
    client_with_fake_db,
    monkeypatch,
):
    captured = {}

    class FakeIngestionJobRepository:
        def __init__(self, session):
            captured["session"] = session

        async def create_job(self, **kwargs):
            captured["job_kwargs"] = kwargs
            return make_job(
                tenant_id=kwargs["tenant_id"],
            )

    class FakeStorageService:
        @staticmethod
        async def upload_file(file_name, file_bytes, content_type):
            captured["storage_kwargs"] = {
                "file_name": file_name,
                "file_bytes": file_bytes,
                "content_type": content_type,
            }
            return "s3://documents/raw-note.txt"

    class FakeQueue:
        async def enqueue(self, job_id):
            captured["queued_job_id"] = job_id

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )
    monkeypatch.setattr(
        "app.api.routes.ingestion.storage_service",
        FakeStorageService,
    )
    monkeypatch.setattr(
        "app.api.routes.ingestion.get_ingestion_queue",
        lambda: FakeQueue(),
    )

    response = client_with_fake_db.post(
        "/upload",
        files={"file": ("note.txt", b"Trecho", "text/plain")},
        headers={"X-Tenant-ID": "tenant-a"},
    )

    assert response.status_code == 202
    assert response.json()["job_id"] == str(JOB_ID)
    assert response.json()["status"] == "pending"
    assert response.json()["document_id"] is None
    assert captured["job_kwargs"] == {
        "tenant_id": "tenant-a",
        "file_name": "note.txt",
        "content_type": "text/plain",
        "file_size": 6,
        "raw_storage_path": "s3://documents/raw-note.txt",
        "max_attempts": 3,
    }
    assert captured["storage_kwargs"]["file_bytes"] == b"Trecho"
    assert captured["queued_job_id"] == JOB_ID


def test_upload_accepts_pdf_and_docx_content_types(
    client_with_fake_db,
    monkeypatch,
):
    created_jobs = []

    class FakeIngestionJobRepository:
        def __init__(self, session):
            self.session = session

        async def create_job(self, **kwargs):
            created_jobs.append(kwargs)
            return make_job(
                tenant_id=kwargs["tenant_id"],
            )

    class FakeStorageService:
        @staticmethod
        async def upload_file(file_name, file_bytes, content_type):
            return f"s3://documents/{file_name}"

    class FakeQueue:
        async def enqueue(self, job_id):
            return None

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )
    monkeypatch.setattr(
        "app.api.routes.ingestion.storage_service",
        FakeStorageService,
    )
    monkeypatch.setattr(
        "app.api.routes.ingestion.get_ingestion_queue",
        lambda: FakeQueue(),
    )

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

    assert pdf_response.status_code == 202
    assert docx_response.status_code == 202
    assert created_jobs[0]["content_type"] == "application/pdf"
    assert (
        created_jobs[1]["content_type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


def test_list_upload_jobs_returns_tenant_jobs(client_with_fake_db, monkeypatch):
    created_from = "2026-06-01T00:00:00"
    created_to = "2026-06-03T00:00:00"

    class FakeIngestionJobRepository:
        def __init__(self, session):
            self.session = session

        async def list_jobs(self, **kwargs):
            assert kwargs["tenant_id"] == "tenant-a"
            assert kwargs["limit"] == 25
            assert kwargs["offset"] == 5
            assert kwargs["status"] == "completed"
            assert kwargs["filename"] == "note"
            assert kwargs["content_type"] == "text/plain"
            assert kwargs["created_from"] == datetime.fromisoformat(created_from)
            assert kwargs["created_to"] == datetime.fromisoformat(created_to)
            assert kwargs["document_id"] == DOCUMENT_ID
            return [make_job(status="completed", tenant_id="tenant-a", document_id=DOCUMENT_ID)]

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )

    response = client_with_fake_db.get(
        (
            "/uploads?limit=25&offset=5&status=completed&filename=note"
            f"&content_type=text/plain&created_from={created_from}"
            f"&created_to={created_to}&document_id={DOCUMENT_ID}"
        ),
        headers={"X-Tenant-ID": "tenant-a"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["uploads"][0]["status"] == "completed"
    assert payload["uploads"][0]["document_id"] == str(DOCUMENT_ID)
    assert payload["uploads"][0]["tenant_id"] == "tenant-a"
    assert payload["limit"] == 25
    assert payload["offset"] == 5
    assert payload["count"] == 1


def test_get_upload_job_returns_404_for_other_tenant(client_with_fake_db, monkeypatch):
    class FakeIngestionJobRepository:
        def __init__(self, session):
            self.session = session

        async def get_job(self, **kwargs):
            assert kwargs["tenant_id"] == "tenant-a"
            return None

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )

    response = client_with_fake_db.get(
        f"/uploads/{JOB_ID}",
        headers={"X-Tenant-ID": "tenant-a"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Upload job nao encontrado."


def test_get_upload_job_returns_failed_error_message(client_with_fake_db, monkeypatch):
    class FakeIngestionJobRepository:
        def __init__(self, session):
            self.session = session

        async def get_job(self, **kwargs):
            assert kwargs["tenant_id"] == "tenant-a"
            return make_job(
                status="failed",
                tenant_id="tenant-a",
                error_message="Arquivo PDF invalido.",
            )

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )

    response = client_with_fake_db.get(
        f"/uploads/{JOB_ID}",
        headers={"X-Tenant-ID": "tenant-a"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["error_message"] == "Arquivo PDF invalido."


def test_retry_failed_upload_job_reenqueues_job(client_with_fake_db, monkeypatch):
    captured = {}

    class FakeIngestionJobRepository:
        def __init__(self, session):
            self.session = session

        async def get_job(self, **kwargs):
            assert kwargs["tenant_id"] == "tenant-a"
            return make_job(
                status="failed",
                tenant_id="tenant-a",
                error_message="Arquivo PDF invalido.",
            )

        async def retry_failed_job(self, **kwargs):
            captured["retry_kwargs"] = kwargs
            return make_job(status="pending", tenant_id="tenant-a")

        async def fail_job(self, **kwargs):
            captured["fail_kwargs"] = kwargs

    class FakeQueue:
        async def enqueue(self, job_id):
            captured["queued_job_id"] = job_id

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )
    monkeypatch.setattr(
        "app.api.routes.ingestion.get_ingestion_queue",
        lambda: FakeQueue(),
    )

    response = client_with_fake_db.post(
        f"/uploads/{JOB_ID}/retry",
        headers={"X-Tenant-ID": "tenant-a"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["message"] == "Upload job reenfileirado para processamento."
    assert captured["retry_kwargs"] == {"tenant_id": "tenant-a", "job_id": JOB_ID}
    assert captured["queued_job_id"] == JOB_ID


@pytest.mark.parametrize("job_status", ["pending", "processing", "completed", "canceled"])
def test_retry_upload_job_rejects_invalid_states(
    client_with_fake_db,
    monkeypatch,
    job_status,
):
    class FakeIngestionJobRepository:
        def __init__(self, session):
            self.session = session

        async def get_job(self, **kwargs):
            return make_job(status=job_status, tenant_id="tenant-a")

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )

    response = client_with_fake_db.post(
        f"/uploads/{JOB_ID}/retry",
        headers={"X-Tenant-ID": "tenant-a"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Apenas upload jobs failed podem receber retry manual."


def test_retry_upload_job_returns_404_for_other_tenant(client_with_fake_db, monkeypatch):
    class FakeIngestionJobRepository:
        def __init__(self, session):
            self.session = session

        async def get_job(self, **kwargs):
            assert kwargs["tenant_id"] == "tenant-a"
            return None

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )

    response = client_with_fake_db.post(
        f"/uploads/{JOB_ID}/retry",
        headers={"X-Tenant-ID": "tenant-a"},
    )

    assert response.status_code == 404


def test_cancel_pending_upload_job(client_with_fake_db, monkeypatch):
    captured = {}

    class FakeIngestionJobRepository:
        def __init__(self, session):
            self.session = session

        async def get_job(self, **kwargs):
            assert kwargs["tenant_id"] == "tenant-a"
            return make_job(status="pending", tenant_id="tenant-a")

        async def cancel_pending_job(self, **kwargs):
            captured["cancel_kwargs"] = kwargs
            return make_job(
                status="canceled",
                tenant_id="tenant-a",
                error_message="Upload cancelado pelo usuario.",
            )

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )

    response = client_with_fake_db.post(
        f"/uploads/{JOB_ID}/cancel",
        headers={"X-Tenant-ID": "tenant-a"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "canceled"
    assert response.json()["message"] == "Upload job cancelado."
    assert captured["cancel_kwargs"] == {"tenant_id": "tenant-a", "job_id": JOB_ID}


@pytest.mark.parametrize("job_status", ["completed", "failed", "canceled"])
def test_cancel_upload_job_rejects_terminal_states(
    client_with_fake_db,
    monkeypatch,
    job_status,
):
    class FakeIngestionJobRepository:
        def __init__(self, session):
            self.session = session

        async def get_job(self, **kwargs):
            return make_job(status=job_status, tenant_id="tenant-a")

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )

    response = client_with_fake_db.post(
        f"/uploads/{JOB_ID}/cancel",
        headers={"X-Tenant-ID": "tenant-a"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Apenas upload jobs pending podem ser cancelados."


def test_cancel_upload_job_rejects_processing_state(client_with_fake_db, monkeypatch):
    class FakeIngestionJobRepository:
        def __init__(self, session):
            self.session = session

        async def get_job(self, **kwargs):
            return make_job(status="processing", tenant_id="tenant-a")

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )

    response = client_with_fake_db.post(
        f"/uploads/{JOB_ID}/cancel",
        headers={"X-Tenant-ID": "tenant-a"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Upload job em processamento nao pode ser cancelado com seguranca."
    )
