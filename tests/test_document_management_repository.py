from datetime import datetime
from uuid import UUID

import anyio

from app.repositories.documents import DocumentRepository


class FakeMappings:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


class FakeResult:
    def __init__(self, rows=None, scalar=None):
        self.rows = rows or []
        self.scalar = scalar

    def mappings(self):
        return FakeMappings(self.rows)

    def scalar_one(self):
        return self.scalar

    def scalar_one_or_none(self):
        return self.scalar


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


def document_row(tenant_id="tenant-a"):
    return {
        "id": UUID("11111111-1111-1111-1111-111111111111"),
        "tenant_id": tenant_id,
        "file_name": "manual.pdf",
        "content_type": "application/pdf",
        "file_size": 1234,
        "chunks_count": 2,
        "created_at": datetime(2026, 6, 1, 12, 0, 0),
        "metadata": '{"source": "manual.pdf"}',
    }


def test_list_documents_filters_by_tenant_and_metadata_filters():
    session = FakeSession([FakeResult(rows=[document_row()])])
    repository = DocumentRepository(session)

    async def call_repository():
        return await repository.list_documents(
            tenant_id="tenant-a",
            source="manual",
            content_type="application/pdf",
        )

    documents = anyio.run(call_repository)

    assert documents[0].tenant_id == "tenant-a"
    statement = str(session.calls[0][0])
    assert "sd.tenant_id = :tenant_id" in statement
    assert "dc.tenant_id = :tenant_id" in statement
    assert "sd.metadata ->> 'source'" in statement
    assert session.calls[0][1]["tenant_id"] == "tenant-a"
    assert session.calls[0][1]["source"] == "manual"
    assert session.calls[0][1]["content_type"] == "application/pdf"


def test_get_document_returns_none_for_missing_tenant_scoped_document():
    session = FakeSession([FakeResult(rows=[])])
    repository = DocumentRepository(session)

    async def call_repository():
        return await repository.get_document(
            tenant_id="tenant-a",
            document_id=UUID("11111111-1111-1111-1111-111111111111"),
        )

    document = anyio.run(call_repository)

    assert document is None
    statement = str(session.calls[0][0])
    assert "sd.id = :document_id" in statement
    assert "sd.tenant_id = :tenant_id" in statement
    assert session.calls[0][1]["tenant_id"] == "tenant-a"


def test_list_document_chunks_constrains_document_and_tenant():
    session = FakeSession([FakeResult(rows=[])])
    repository = DocumentRepository(session)

    async def call_repository():
        return await repository.list_document_chunks(
            tenant_id="tenant-a",
            document_id=UUID("11111111-1111-1111-1111-111111111111"),
            limit=20,
            offset=0,
        )

    chunks = anyio.run(call_repository)

    assert chunks == []
    statement = str(session.calls[0][0])
    assert "dc.source_document_id = :document_id" in statement
    assert "dc.tenant_id = :tenant_id" in statement
    assert "sd.tenant_id = :tenant_id" in statement
    assert session.calls[0][1]["tenant_id"] == "tenant-a"


def test_delete_document_removes_only_tenant_scoped_document_and_commits():
    session = FakeSession(
        [FakeResult(scalar=UUID("11111111-1111-1111-1111-111111111111"))]
    )
    repository = DocumentRepository(session)

    async def call_repository():
        return await repository.delete_document(
            tenant_id="tenant-a",
            document_id=UUID("11111111-1111-1111-1111-111111111111"),
        )

    deleted = anyio.run(call_repository)

    assert deleted is True
    assert session.committed is True
    statement = str(session.calls[0][0])
    assert "DELETE FROM source_documents" in statement
    assert "tenant_id = :tenant_id" in statement
    assert session.calls[0][1]["tenant_id"] == "tenant-a"


def test_delete_document_rolls_back_when_document_is_missing():
    session = FakeSession([FakeResult(scalar=None)])
    repository = DocumentRepository(session)

    async def call_repository():
        return await repository.delete_document(
            tenant_id="tenant-a",
            document_id=UUID("11111111-1111-1111-1111-111111111111"),
        )

    deleted = anyio.run(call_repository)

    assert deleted is False
    assert session.rolled_back is True
    assert session.committed is False
