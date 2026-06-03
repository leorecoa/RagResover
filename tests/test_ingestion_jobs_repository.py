from datetime import datetime
from uuid import UUID

import anyio

from app.repositories.ingestion_jobs import IngestionJobRepository


class FakeMappings:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None

    def one(self):
        return self.rows[0]


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def mappings(self):
        return FakeMappings(self.rows)


class FakeSession:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []
        self.committed = False
        self.rolled_back = False

    async def execute(self, statement, params):
        self.calls.append((statement, params))
        return self.results.pop(0)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True


def job_row(status="pending", document_id=None):
    return {
        "id": UUID("11111111-1111-1111-1111-111111111111"),
        "tenant_id": "tenant-a",
        "file_name": "manual.pdf",
        "content_type": "application/pdf",
        "file_size": 2048,
        "raw_storage_path": "s3://documents/manual.pdf",
        "status": status,
        "error_message": None,
        "attempts": 1 if status in {"processing", "completed", "failed"} else 0,
        "max_attempts": 3,
        "last_error": None,
        "document_id": document_id,
        "created_at": datetime(2026, 6, 1, 12, 0, 0),
        "updated_at": datetime(2026, 6, 1, 12, 1, 0),
        "started_at": datetime(2026, 6, 1, 12, 0, 30) if status == "processing" else None,
        "finished_at": datetime(2026, 6, 1, 12, 1, 0)
        if status in {"completed", "failed"}
        else None,
    }


def test_create_job_persists_pending_job_and_commits():
    session = FakeSession([FakeResult([job_row()])])
    repository = IngestionJobRepository(session)

    async def call_repository():
        return await repository.create_job(
            tenant_id="tenant-a",
            file_name="manual.pdf",
            content_type="application/pdf",
            file_size=2048,
            raw_storage_path="s3://documents/manual.pdf",
            max_attempts=3,
        )

    job = anyio.run(call_repository)

    assert job.status == "pending"
    assert session.committed is True
    statement = str(session.calls[0][0])
    assert "INSERT INTO ingestion_jobs" in statement
    assert session.calls[0][1]["tenant_id"] == "tenant-a"
    assert session.calls[0][1]["raw_storage_path"] == "s3://documents/manual.pdf"
    assert session.calls[0][1]["max_attempts"] == 3


def test_list_jobs_filters_by_tenant():
    session = FakeSession([FakeResult([job_row(status="completed")])])
    repository = IngestionJobRepository(session)

    async def call_repository():
        return await repository.list_jobs(tenant_id="tenant-a", limit=25)

    jobs = anyio.run(call_repository)

    assert jobs[0].status == "completed"
    statement = str(session.calls[0][0])
    assert "WHERE tenant_id = :tenant_id" in statement
    assert session.calls[0][1]["tenant_id"] == "tenant-a"
    assert session.calls[0][1]["limit"] == 25


def test_get_job_constrains_by_job_and_tenant():
    session = FakeSession([FakeResult([job_row()])])
    repository = IngestionJobRepository(session)

    async def call_repository():
        return await repository.get_job(
            tenant_id="tenant-a",
            job_id=UUID("11111111-1111-1111-1111-111111111111"),
        )

    job = anyio.run(call_repository)

    assert job is not None
    statement = str(session.calls[0][0])
    assert "WHERE id = :job_id" in statement
    assert "AND tenant_id = :tenant_id" in statement


def test_update_status_marks_completed_document_and_commits():
    document_id = UUID("22222222-2222-2222-2222-222222222222")
    session = FakeSession([FakeResult([job_row(status="completed", document_id=document_id)])])
    repository = IngestionJobRepository(session)

    async def call_repository():
        return await repository.update_status(
            job_id=UUID("11111111-1111-1111-1111-111111111111"),
            status="completed",
            document_id=document_id,
        )

    job = anyio.run(call_repository)

    assert job is not None
    assert job.document_id == document_id
    assert session.committed is True
    statement = str(session.calls[0][0])
    assert "UPDATE ingestion_jobs" in statement
    assert "updated_at = CURRENT_TIMESTAMP" in statement


def test_update_status_rolls_back_when_job_is_missing():
    session = FakeSession([FakeResult([])])
    repository = IngestionJobRepository(session)

    async def call_repository():
        return await repository.update_status(
            job_id=UUID("11111111-1111-1111-1111-111111111111"),
            status="processing",
        )

    job = anyio.run(call_repository)

    assert job is None
    assert session.rolled_back is True
    assert session.committed is False


def test_start_attempt_increments_attempts_and_marks_processing():
    session = FakeSession([FakeResult([job_row(status="processing")])])
    repository = IngestionJobRepository(session)

    async def call_repository():
        return await repository.start_attempt(
            job_id=UUID("11111111-1111-1111-1111-111111111111"),
        )

    job = anyio.run(call_repository)

    assert job is not None
    assert job.status == "processing"
    assert session.committed is True
    statement = str(session.calls[0][0])
    assert "attempts = attempts + 1" in statement
    assert "status IN ('pending', 'failed')" in statement
    assert "attempts < max_attempts" in statement


def test_retry_job_records_last_error_and_marks_pending():
    row = job_row(status="pending")
    row["last_error"] = "temporary parser failure"
    session = FakeSession([FakeResult([row])])
    repository = IngestionJobRepository(session)

    async def call_repository():
        return await repository.mark_retry_pending(
            job_id=UUID("11111111-1111-1111-1111-111111111111"),
            error_message="temporary parser failure",
        )

    job = anyio.run(call_repository)

    assert job is not None
    assert job.status == "pending"
    assert session.committed is True
    assert session.calls[0][1]["error_message"] == "temporary parser failure"


def test_fail_job_sets_error_and_finished_at():
    row = job_row(status="failed")
    row["error_message"] = "parser unavailable"
    row["last_error"] = "parser unavailable"
    session = FakeSession([FakeResult([row])])
    repository = IngestionJobRepository(session)

    async def call_repository():
        return await repository.fail_job(
            job_id=UUID("11111111-1111-1111-1111-111111111111"),
            error_message="parser unavailable",
        )

    job = anyio.run(call_repository)

    assert job is not None
    assert job.status == "failed"
    assert job.error_message == "parser unavailable"
    assert job.last_error == "parser unavailable"


def test_fail_stale_processing_jobs_returns_updated_count():
    session = FakeSession([FakeResult([{"id": UUID("11111111-1111-1111-1111-111111111111")}])])
    repository = IngestionJobRepository(session)

    async def call_repository():
        return await repository.fail_stale_processing_jobs(stale_after_seconds=900)

    count = anyio.run(call_repository)

    assert count == 1
    assert session.committed is True
    statement = str(session.calls[0][0])
    assert "status = 'processing'" in statement
    assert session.calls[0][1]["stale_after_seconds"] == 900
