from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID

from app.repositories.documents import DocumentChunkRecord, DocumentRecord


DOCUMENT_ID = UUID("11111111-1111-1111-1111-111111111111")
CHUNK_ID = UUID("22222222-2222-2222-2222-222222222222")
ADMIN_HEADERS = {"X-Tenant-ID": "tenant-a", "X-User-Roles": "admin"}


def make_document(tenant_id="tenant-a"):
    return DocumentRecord(
        id=DOCUMENT_ID,
        tenant_id=tenant_id,
        file_name="manual.pdf",
        content_type="application/pdf",
        file_size=1234,
        chunks_count=2,
        created_at=datetime(2026, 6, 1, 12, 0, 0),
        metadata={"source": "manual.pdf", "page_count": 4},
    )


def make_chunk():
    return DocumentChunkRecord(
        id=CHUNK_ID,
        document_id=DOCUMENT_ID,
        chunk_index=0,
        content="Chunk recuperado",
        metadata={"source": "manual.pdf", "page": 1},
        created_at=datetime(2026, 6, 1, 12, 1, 0),
    )


def patch_repository(repository):
    return patch("app.api.routes.documents.DocumentRepository", lambda session: repository)


def test_list_documents_returns_only_tenant_documents(client_with_fake_db):
    repository = AsyncMock()
    repository.list_documents.return_value = [make_document()]

    with patch_repository(repository):
        response = client_with_fake_db.get(
            "/documents",
            headers={"X-Tenant-ID": "tenant-a"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["documents"][0]["id"] == str(DOCUMENT_ID)
    assert payload["documents"][0]["tenant_id"] == "tenant-a"
    assert payload["documents"][0]["chunks_count"] == 2
    repository.list_documents.assert_awaited_once()
    assert repository.list_documents.await_args.kwargs["tenant_id"] == "tenant-a"


def test_list_documents_passes_filters_to_repository(client_with_fake_db):
    repository = AsyncMock()
    repository.list_documents.return_value = []

    with patch_repository(repository):
        response = client_with_fake_db.get(
            "/documents?source=manual&content_type=application/pdf",
            headers={"X-Tenant-ID": "tenant-a"},
        )

    assert response.status_code == 200
    call_kwargs = repository.list_documents.await_args.kwargs
    assert call_kwargs["source"] == "manual"
    assert call_kwargs["content_type"] == "application/pdf"


def test_get_document_returns_detail_for_tenant_document(client_with_fake_db):
    repository = AsyncMock()
    repository.get_document.return_value = make_document()

    with patch_repository(repository):
        response = client_with_fake_db.get(
            f"/documents/{DOCUMENT_ID}",
            headers={"X-Tenant-ID": "tenant-a"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["file_name"] == "manual.pdf"
    assert payload["metadata"]["source"] == "manual.pdf"
    assert repository.get_document.await_args.kwargs["tenant_id"] == "tenant-a"


def test_get_document_returns_404_for_other_tenant_document(client_with_fake_db):
    repository = AsyncMock()
    repository.get_document.return_value = None

    with patch_repository(repository):
        response = client_with_fake_db.get(
            f"/documents/{DOCUMENT_ID}",
            headers={"X-Tenant-ID": "tenant-a"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Documento nao encontrado."
    assert repository.get_document.await_args.kwargs["tenant_id"] == "tenant-a"


def test_list_document_chunks_returns_paginated_chunks(client_with_fake_db):
    repository = AsyncMock()
    repository.get_document.return_value = make_document()
    repository.count_document_chunks.return_value = 1
    repository.list_document_chunks.return_value = [make_chunk()]

    with patch_repository(repository):
        response = client_with_fake_db.get(
            f"/documents/{DOCUMENT_ID}/chunks?page=1&page_size=10",
            headers={"X-Tenant-ID": "tenant-a"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == str(DOCUMENT_ID)
    assert payload["total"] == 1
    assert payload["chunks"][0]["content"] == "Chunk recuperado"
    assert repository.list_document_chunks.await_args.kwargs["tenant_id"] == "tenant-a"
    assert repository.list_document_chunks.await_args.kwargs["limit"] == 10
    assert repository.list_document_chunks.await_args.kwargs["offset"] == 0


def test_list_document_chunks_returns_404_for_other_tenant_document(client_with_fake_db):
    repository = AsyncMock()
    repository.get_document.return_value = None

    with patch_repository(repository):
        response = client_with_fake_db.get(
            f"/documents/{DOCUMENT_ID}/chunks",
            headers={"X-Tenant-ID": "tenant-a"},
        )

    assert response.status_code == 404
    repository.list_document_chunks.assert_not_awaited()


def test_delete_document_removes_tenant_document(client_with_fake_db):
    repository = AsyncMock()
    repository.delete_document.return_value = True

    with patch_repository(repository):
        response = client_with_fake_db.delete(
            f"/documents/{DOCUMENT_ID}",
            headers=ADMIN_HEADERS,
        )

    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert repository.delete_document.await_args.kwargs["tenant_id"] == "tenant-a"


def test_delete_document_returns_404_for_other_tenant_document(client_with_fake_db):
    repository = AsyncMock()
    repository.delete_document.return_value = False

    with patch_repository(repository):
        response = client_with_fake_db.delete(
            f"/documents/{DOCUMENT_ID}",
            headers=ADMIN_HEADERS,
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Documento nao encontrado."


def test_viewer_cannot_delete_document(client_with_fake_db):
    response = client_with_fake_db.delete(
        f"/documents/{DOCUMENT_ID}",
        headers={"X-Tenant-ID": "tenant-a", "X-User-Roles": "viewer"},
    )

    assert response.status_code == 403
