import asyncio
import logging
import signal

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.repositories.ingestion_jobs import IngestionJobRepository
from app.services.ingestion_queue import close_ingestion_queue, get_ingestion_queue
from app.services.upload_jobs import process_queued_upload_job

logger = logging.getLogger("rag_resover")


async def mark_stale_jobs_failed() -> int:
    async with AsyncSessionLocal() as session:
        return await IngestionJobRepository(session).fail_stale_processing_jobs(
            stale_after_seconds=settings.INGESTION_STALE_JOB_TIMEOUT_SECONDS,
        )


async def run_worker() -> None:
    queue = get_ingestion_queue()
    stop_event = asyncio.Event()

    def request_stop() -> None:
        logger.info("Stopping ingestion worker.")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_stop)
        except NotImplementedError:
            signal.signal(sig, lambda *_: request_stop())

    logger.info(
        "Ingestion worker started with provider=%s queue=%s",
        settings.INGESTION_QUEUE_PROVIDER,
        settings.INGESTION_QUEUE_NAME,
    )

    try:
        while not stop_event.is_set():
            failed_count = await mark_stale_jobs_failed()
            if failed_count:
                logger.warning("Marked %s stale ingestion job(s) as failed.", failed_count)

            job_id = await queue.dequeue(
                timeout_seconds=settings.INGESTION_WORKER_POLL_TIMEOUT_SECONDS,
            )
            if job_id is None:
                continue

            await process_queued_upload_job(job_id=job_id, queue=queue)
    finally:
        await close_ingestion_queue()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
