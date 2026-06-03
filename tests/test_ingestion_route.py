from datetime import datetime
from uuid import UUID

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
        status=status,
        error_message=error_message,
        document_id=document_id,
        created_at=datetime(2026, 6, 1, 12, 0, 0),
        updated_at=datetime(2026, 6, 1, 12, 0, 0),
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


def test_upload_creates_job_and_schedules_background_processing(
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

    async def fake_process_upload_job(**kwargs):
        captured["background_kwargs"] = kwargs

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )
    monkeypatch.setattr(
        "app.api.routes.ingestion.process_upload_job",
        fake_process_upload_job,
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
    }
    assert captured["background_kwargs"]["job_id"] == JOB_ID
    assert captured["background_kwargs"]["tenant_id"] == "tenant-a"
    assert captured["background_kwargs"]["file_bytes"] == b"Trecho"


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

    async def fake_process_upload_job(**kwargs):
        return None

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )
    monkeypatch.setattr(
        "app.api.routes.ingestion.process_upload_job",
        fake_process_upload_job,
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
    class FakeIngestionJobRepository:
        def __init__(self, session):
            self.session = session

        async def list_jobs(self, **kwargs):
            assert kwargs["tenant_id"] == "tenant-a"
            assert kwargs["limit"] == 25
            return [make_job(status="completed", tenant_id="tenant-a", document_id=DOCUMENT_ID)]

    monkeypatch.setattr(
        "app.api.routes.ingestion.IngestionJobRepository",
        FakeIngestionJobRepository,
    )

    response = client_with_fake_db.get(
        "/uploads?limit=25",
        headers={"X-Tenant-ID": "tenant-a"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["uploads"][0]["status"] == "completed"
    assert payload["uploads"][0]["document_id"] == str(DOCUMENT_ID)
    assert payload["uploads"][0]["tenant_id"] == "tenant-a"


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
