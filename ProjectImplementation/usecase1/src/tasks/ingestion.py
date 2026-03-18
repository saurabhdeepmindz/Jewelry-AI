"""Celery tasks for lead ingestion.

Task: ingest_lead_file
Queue: ingestion
Retry: up to 3 times with exponential backoff (60s, 120s, 240s)
"""
import asyncio

from src.core.logging import get_logger
from src.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="tasks.ingest_lead_file",
    bind=True,
    queue="ingestion",
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=3,
)
def ingest_lead_file(self, job_id: str, csv_content: str) -> dict:  # type: ignore[return]
    """Process a CSV file upload and persist Lead records asynchronously.

    Parameters
    ----------
    job_id:
        UUID string for polling via GET /api/v1/leads/jobs/{job_id}.
    csv_content:
        Raw CSV text decoded from the uploaded file.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run(self, job_id, csv_content))
    finally:
        loop.close()


async def _run(task, job_id: str, csv_content: str) -> dict:
    from src.core.job_store import set_job_status
    from src.db.session import AsyncSessionLocal
    from src.services.ingestion_service import ingest_csv

    # Mark as in-progress immediately
    await set_job_status(
        job_id,
        {
            "job_id": job_id,
            "status": "processing",
            "created": 0,
            "skipped_duplicates": 0,
            "skipped_invalid": 0,
            "errors": 0,
        },
    )

    try:
        async with AsyncSessionLocal() as session:
            result = await ingest_csv(session, csv_content)
            await session.commit()

        status_data: dict = {
            "job_id": job_id,
            "status": "completed",
            "created": result.created,
            "skipped_duplicates": result.skipped_duplicates,
            "skipped_invalid": result.skipped_invalid,
            "errors": result.errors,
        }
        await set_job_status(job_id, status_data)
        return status_data

    except Exception as exc:
        logger.error("Ingestion task %s failed (attempt %d): %s", job_id, task.request.retries, exc)
        retry_count = task.request.retries
        countdown = 60 * (2**retry_count)

        try:
            raise task.retry(exc=exc, countdown=countdown)
        except task.MaxRetriesExceededError:
            error_data: dict = {
                "job_id": job_id,
                "status": "failed",
                "created": 0,
                "skipped_duplicates": 0,
                "skipped_invalid": 0,
                "errors": 1,
                "error": str(exc),
            }
            await set_job_status(job_id, error_data)
            return error_data
