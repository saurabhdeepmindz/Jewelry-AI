"""Enrichment API endpoints.

US-010: POST /api/v1/enrichment/{lead_id}  — trigger enrichment, return job_id
US-013: GET  /api/v1/enrichment/jobs/{job_id} — poll Celery job status
US-014: POST /api/v1/enrichment/batch — enqueue enrichment for multiple leads
"""
import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.core.job_store import get_job_status
from src.core.logging import get_logger
from src.tasks.enrichment import enrich_lead_task

router = APIRouter(prefix="/api/v1/enrichment", tags=["enrichment"])
logger = get_logger(__name__)


class BatchEnrichRequest(BaseModel):
    lead_ids: list[str]


@router.post("/batch", status_code=status.HTTP_202_ACCEPTED)
async def trigger_batch_enrichment(body: BatchEnrichRequest) -> dict:  # type: ignore[type-arg]
    """Queue enrichment jobs for multiple leads.

    Dispatches one Celery task per lead_id.
    Returns a single batch job_id and the total count dispatched.
    """
    batch_job_id = str(uuid.uuid4())
    for lead_id in body.lead_ids:
        job_id = str(uuid.uuid4())
        enrich_lead_task.delay(job_id=job_id, lead_id=lead_id)

    logger.info(
        "Batch enrichment dispatched batch_job_id=%s total=%d",
        batch_job_id,
        len(body.lead_ids),
    )
    return {
        "success": True,
        "message": "Batch enrichment jobs queued",
        "data": {
            "job_id": batch_job_id,
            "total": len(body.lead_ids),
            "status": "queued",
        },
    }


@router.post("/{lead_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_enrichment(lead_id: str) -> dict:  # type: ignore[type-arg]
    """Queue an enrichment job for a single lead.

    Dispatches async Celery task; returns job_id for polling.
    Does not validate lead_id existence synchronously — task handles 404.
    """
    job_id = str(uuid.uuid4())
    enrich_lead_task.delay(job_id=job_id, lead_id=lead_id)
    logger.info("Enrichment job dispatched job_id=%s lead_id=%s", job_id, lead_id)

    return {
        "success": True,
        "message": "Enrichment job queued",
        "data": {
            "job_id": job_id,
            "lead_id": lead_id,
            "status": "queued",
            "estimated_completion_seconds": 15,
        },
    }


@router.get("/jobs/{job_id}")
async def get_enrichment_job_status(job_id: str) -> dict:  # type: ignore[type-arg]
    """Poll enrichment job status.

    Returns 404 if job_id is unknown (expired TTL or invalid).
    Polling interval: 2s recommended.
    """
    data = await get_job_status(job_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id!r} not found",
        )
    return data
