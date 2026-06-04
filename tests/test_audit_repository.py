from datetime import datetime
from uuid import UUID

import anyio

from app.api.dependencies.auth import TenantContext
from app.repositories.audit import AuditLogRepository
from app.services.audit import record_audit_event


class FakeMappings:
    def __init__(self, row):
        self.row = row

    def one(self):
        return self.row


class FakeResult:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return FakeMappings(self.row)


class FakeSession:
    def __init__(self, result=None, should_fail=False):
        self.result = result
        self.should_fail = should_fail
        self.calls = []
        self.committed = False

    async def execute(self, statement, params):
        if self.should_fail:
            raise RuntimeError("database unavailable")
        self.calls.append((statement, params))
        return self.result

    async def commit(self):
        self.committed = True


def audit_row():
    return {
        "id": UUID("11111111-1111-1111-1111-111111111111"),
        "tenant_id": "tenant-a",
        "actor_user_id": "user-a",
        "actor_roles": ["admin", "viewer"],
        "action": "document.delete",
        "resource_type": "document",
        "resource_id": "doc-1",
        "metadata": {"reason": "test"},
        "created_at": datetime(2026, 6, 3, 12, 0, 0),
    }


def test_audit_repository_creates_event_with_json_payloads():
    session = FakeSession(FakeResult(audit_row()))
    repository = AuditLogRepository(session)

    async def call_repository():
        return await repository.create_event(
            tenant_id="tenant-a",
            actor_user_id="user-a",
            actor_roles=["admin", "viewer"],
            action="document.delete",
            resource_type="document",
            resource_id="doc-1",
            metadata={"reason": "test"},
        )

    event = anyio.run(call_repository)

    assert event.action == "document.delete"
    assert event.actor_roles == ["admin", "viewer"]
    assert session.committed is True
    params = session.calls[0][1]
    assert params["tenant_id"] == "tenant-a"
    assert params["actor_roles"] == '["admin", "viewer"]'
    assert params["metadata"] == '{"reason": "test"}'


def test_record_audit_event_is_best_effort():
    session = FakeSession(should_fail=True)
    tenant = TenantContext(
        tenant_id="tenant-a",
        is_anonymous=False,
        user_id="user-a",
        roles=frozenset({"admin"}),
    )

    async def call_service():
        await record_audit_event(
            session=session,
            tenant=tenant,
            action="upload.retry",
            resource_type="upload_job",
            resource_id="job-1",
        )

    anyio.run(call_service)
