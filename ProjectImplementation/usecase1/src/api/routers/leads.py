"""Lead ingestion API endpoints.

US-006: POST /api/v1/leads/upload  — CSV upload; validates, dispatches Celery task, returns job_id
US-009: GET  /api/v1/leads/jobs/{job_id} — Poll job status from Redis
"""
import csv
import io
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, status

from src.core.exceptions import ValidationException
from src.core.job_store import get_job_status
from src.core.logging import get_logger
from src.domain.lead import IngestionSummary
from src.services.ingestion_service import MAX_BATCH_SIZE
from src.tasks.ingestion import ingest_lead_file

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])
logger = get_logger(__name__)


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_leads_csv(file: UploadFile) -> dict:  # type: ignore[type-arg]
    """Accept a CSV file of raw buyer company data.

    Validates column structure and batch size synchronously (fail-fast).
    Dispatches async Celery task for persistence.
    Returns job_id (UUID) for polling via GET /api/v1/leads/jobs/{job_id}.
    """
    content_bytes = await file.read()
    try:
        csv_content = content_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationException("CSV file must be UTF-8 encoded") from exc

    # Synchronous validation — fail before dispatching task
    reader = csv.DictReader(io.StringIO(csv_content))
    if not reader.fieldnames or "company_name" not in reader.fieldnames:
        raise ValidationException("Missing required column: company_name")

    rows = list(reader)
    if len(rows) > MAX_BATCH_SIZE:
        raise ValidationException(
            f"Batch size {len(rows)} exceeds maximum {MAX_BATCH_SIZE}"
        )

    job_id = str(uuid.uuid4())
    ingest_lead_file.delay(job_id=job_id, csv_content=csv_content)
    logger.info("Lead ingestion job dispatched job_id=%s rows=%d", job_id, len(rows))

    return {"job_id": job_id, "status": "accepted"}


@router.get("/jobs/{job_id}", response_model=IngestionSummary)
async def get_ingestion_job_status(job_id: str) -> IngestionSummary:
    """Poll ingestion job status.

    Returns 404 if job_id is unknown (expired TTL or invalid).
    Polling interval: 2s recommended; max wait: 5 minutes.
    """
    data = await get_job_status(job_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id!r} not found",
        )
    return IngestionSummary(**data)
