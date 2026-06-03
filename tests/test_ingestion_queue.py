from uuid import UUID

import anyio

import app.services.ingestion_queue as queue_module


JOB_ID = UUID("11111111-1111-1111-1111-111111111111")


def test_inline_queue_processes_job_immediately(monkeypatch):
    processed = []

    async def fake_process_queued_upload_job(**kwargs):
        processed.append(kwargs)

    monkeypatch.setattr(
        "app.services.upload_jobs.process_queued_upload_job",
        fake_process_queued_upload_job,
    )

    async def call_queue():
        queue = queue_module.InlineIngestionQueue()
        await queue.enqueue(JOB_ID)

    anyio.run(call_queue)

    assert len(processed) == 1
    assert processed[0]["job_id"] == JOB_ID
    assert isinstance(processed[0]["queue"], queue_module.InlineIngestionQueue)


def test_redis_queue_enqueues_and_dequeues_with_fake_client():
    calls = []

    class FakeRedisClient:
        async def rpush(self, queue_name, value):
            calls.append(("rpush", queue_name, value))

        async def blpop(self, queue_name, timeout):
            calls.append(("blpop", queue_name, timeout))
            return (queue_name, str(JOB_ID))

        async def aclose(self):
            calls.append(("close",))

    queue = queue_module.RedisIngestionQueue.__new__(queue_module.RedisIngestionQueue)
    queue.queue_name = "test:ingestion"
    queue.client = FakeRedisClient()

    async def call_queue():
        await queue.enqueue(JOB_ID)
        dequeued = await queue.dequeue(timeout_seconds=7)
        await queue.close()
        return dequeued

    dequeued = anyio.run(call_queue)

    assert dequeued == JOB_ID
    assert calls == [
        ("rpush", "test:ingestion", str(JOB_ID)),
        ("blpop", "test:ingestion", 7),
        ("close",),
    ]


def test_redis_queue_ignores_invalid_payload():
    class FakeRedisClient:
        async def blpop(self, queue_name, timeout):
            return (queue_name, "not-a-uuid")

    queue = queue_module.RedisIngestionQueue.__new__(queue_module.RedisIngestionQueue)
    queue.queue_name = "test:ingestion"
    queue.client = FakeRedisClient()

    async def call_queue():
        return await queue.dequeue(timeout_seconds=1)

    assert anyio.run(call_queue) is None
