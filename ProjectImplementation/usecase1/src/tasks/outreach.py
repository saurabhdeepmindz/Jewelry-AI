"""Celery tasks for outreach generation.

Task: generate_outreach_task
Queue: outreach
Retry: up to 3 times with exponential backoff (60s, 120s, 240s)
"""
import asyncio
from typing import Any
from uuid import UUID

from src.core.logging import get_logger
from src.tasks.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="tasks.generate_outreach",
    bind=True,
    queue="outreach",
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=3,
)
def generate_outreach_task(self: Any, job_id: str, lead_id: str) -> dict[str, Any]:
    """Generate an AI outreach email draft for a lead asynchronously.

    Parameters
    ----------
    job_id:
        UUID string for polling via GET /api/v1/outreach/jobs/{job_id}.
    lead_id:
        UUID string of the lead to generate outreach for.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(_run(self, job_id, lead_id))
    finally:
        loop.close()


async def _run(task: Any, job_id: str, lead_id: str) -> dict[str, Any]:
    from src.core.job_store import set_job_status
    from src.db.session import AsyncSessionLocal
    from src.services.outreach_service import generate_draft

    await set_job_status(
        job_id,
        {
            "job_id": job_id,
            "lead_id": lead_id,
            "status": "processing",
        },
    )

    try:
        async with AsyncSessionLocal() as session:
            result = await generate_draft(session, UUID(lead_id))
            await session.commit()

        status_data: dict[str, Any] = {
            "job_id": job_id,
            "lead_id": lead_id,
            "status": "completed",
            "message_id": str(result.id),
        }
        await set_job_status(job_id, status_data)
        return status_data

    except Exception as exc:
        logger.error(
            "Outreach task %s failed for lead %s (attempt %d): %s",
            job_id,
            lead_id,
            task.request.retries,
            exc,
        )
        retry_count = task.request.retries
        countdown = 60 * (2**retry_count)

        try:
            raise task.retry(exc=exc, countdown=countdown)
        except task.MaxRetriesExceededError:
            error_data: dict[str, Any] = {
                "job_id": job_id,
                "lead_id": lead_id,
                "status": "failed",
                "error": str(exc),
            }
            await set_job_status(job_id, error_data)
            return error_data
