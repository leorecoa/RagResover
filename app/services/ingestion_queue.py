import logging
from typing import Protocol
from uuid import UUID

import anyio

from app.core.config import settings

logger = logging.getLogger("rag_resover")


class IngestionQueue(Protocol):
    async def enqueue(self, job_id: UUID) -> None:
        ...

    async def dequeue(self, *, timeout_seconds: int = 5) -> UUID | None:
        ...

    async def close(self) -> None:
        ...


class InlineIngestionQueue:
    async def enqueue(self, job_id: UUID) -> None:
        from app.services.upload_jobs import process_queued_upload_job

        await process_queued_upload_job(job_id=job_id, queue=self)

    async def dequeue(self, *, timeout_seconds: int = 5) -> UUID | None:
        await anyio.sleep(timeout_seconds)
        return None

    async def close(self) -> None:
        return None


class RedisIngestionQueue:
    def __init__(self, *, redis_url: str, queue_name: str):
        from redis.asyncio import Redis

        self.queue_name = queue_name
        self.client = Redis.from_url(redis_url, decode_responses=True)

    async def enqueue(self, job_id: UUID) -> None:
        await self.client.rpush(self.queue_name, str(job_id))

    async def dequeue(self, *, timeout_seconds: int = 5) -> UUID | None:
        item = await self.client.blpop(self.queue_name, timeout=timeout_seconds)
        if item is None:
            return None

        _, raw_job_id = item
        try:
            return UUID(raw_job_id)
        except ValueError:
            logger.warning("Ignoring invalid ingestion queue payload: %s", raw_job_id)
            return None

    async def close(self) -> None:
        await self.client.aclose()


_queue: IngestionQueue | None = None


def create_ingestion_queue(provider: str | None = None) -> IngestionQueue:
    selected_provider = provider or settings.INGESTION_QUEUE_PROVIDER

    if selected_provider == "inline":
        return InlineIngestionQueue()

    if selected_provider == "redis":
        return RedisIngestionQueue(
            redis_url=str(settings.REDIS_URL),
            queue_name=settings.INGESTION_QUEUE_NAME,
        )

    raise ValueError(f"Unsupported ingestion queue provider: {selected_provider}")


def get_ingestion_queue() -> IngestionQueue:
    global _queue
    if _queue is None:
        _queue = create_ingestion_queue()
    return _queue


async def close_ingestion_queue() -> None:
    global _queue
    if _queue is not None:
        await _queue.close()
        _queue = None
