"""Outreach API endpoints.

POST /api/v1/outreach/generate/{lead_id}     — trigger async outreach generation, return job_id
GET  /api/v1/outreach/jobs/{job_id}          — poll job status
GET  /api/v1/outreach/messages               — list messages (filterable)
GET  /api/v1/outreach/messages/{message_id} — get single message
PATCH /api/v1/outreach/messages/{message_id} — edit draft
POST /api/v1/outreach/messages/{message_id}/approve — approve and send
POST /api/v1/outreach/messages/{message_id}/reject  — reject with reason
POST /api/v1/outreach/webhook                — SendGrid webhook handler
"""
import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status

from src.core.exceptions import BusinessRuleException, NotFoundException
from src.core.job_store import get_job_status
from src.core.logging import get_logger
from src.db.session import AsyncSessionLocal
from src.domain.outreach import OutreachRead, OutreachRejectRequest, OutreachUpdate
from src.tasks.outreach import generate_outreach_task

router = APIRouter(prefix="/api/v1/outreach", tags=["outreach"])
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Async generation (Celery-backed)
# ---------------------------------------------------------------------------

@router.post("/generate/{lead_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_outreach_generation(lead_id: str) -> dict[str, Any]:
    """Queue an outreach generation job for a single lead.

    Dispatches an async Celery task; returns job_id for polling.
    Does not validate lead_id existence synchronously — the task handles 404.
    """
    job_id = str(uuid.uuid4())
    generate_outreach_task.delay(job_id=job_id, lead_id=lead_id)
    logger.info(
        "Outreach generation job dispatched job_id=%s lead_id=%s",
        job_id,
        lead_id,
    )
    return {
        "success": True,
        "message": "Outreach generation job queued",
        "data": {
            "job_id": job_id,
            "lead_id": lead_id,
            "status": "queued",
            "estimated_completion_seconds": 30,
        },
    }


@router.get("/jobs/{job_id}")
async def get_outreach_job_status(job_id: str) -> dict[str, Any]:
    """Poll outreach generation job status.

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


# ---------------------------------------------------------------------------
# Message CRUD
# ---------------------------------------------------------------------------

@router.get("/messages")
async def list_messages(
    lead_id: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """List outreach messages with optional filters.

    Query parameters:
    - lead_id: filter by lead UUID (optional)
    - status: filter by status string (optional)
    - page: page number, 1-indexed (default 1)
    - page_size: results per page (default 20, max 100)
    """
    from src.repositories.outreach_repository import OutreachRepository

    capped_page_size = min(page_size, 100)
    lead_uuid: UUID | None = None
    if lead_id:
        try:
            lead_uuid = UUID(lead_id)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="lead_id must be a valid UUID",
            )

    async with AsyncSessionLocal() as session:
        repo = OutreachRepository(session)
        messages = await repo.list_all(
            lead_id=lead_uuid,
            status=status,
            page=page,
            page_size=capped_page_size,
        )

    return {
        "success": True,
        "data": [OutreachRead.model_validate(m).model_dump(mode="json") for m in messages],
        "meta": {"page": page, "page_size": capped_page_size},
    }


@router.get("/messages/{message_id}")
async def get_message(message_id: str) -> dict[str, Any]:
    """Get a single outreach message by ID."""
    from src.repositories.outreach_repository import OutreachRepository

    try:
        msg_uuid = UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="message_id must be a valid UUID",
        )

    async with AsyncSessionLocal() as session:
        repo = OutreachRepository(session)
        message = await repo.get_by_id(msg_uuid)

    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OutreachMessage {message_id!r} not found",
        )

    return {
        "success": True,
        "data": OutreachRead.model_validate(message).model_dump(mode="json"),
    }


@router.patch("/messages/{message_id}")
async def edit_draft(message_id: str, body: OutreachUpdate) -> dict[str, Any]:
    """Edit the subject and/or body of a draft or pending_review message."""
    from src.services.outreach_service import update_draft

    try:
        msg_uuid = UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="message_id must be a valid UUID",
        )

    async with AsyncSessionLocal() as session:
        try:
            result = await update_draft(session, msg_uuid, body)
            await session.commit()
        except NotFoundException as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=exc.message,
            )
        except BusinessRuleException as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=exc.message,
            )

    return {"success": True, "data": result.model_dump(mode="json")}


# ---------------------------------------------------------------------------
# Approve / Reject
# ---------------------------------------------------------------------------

@router.post("/messages/{message_id}/approve")
async def approve_message(message_id: str) -> dict[str, Any]:
    """Approve a pending_review outreach message and send it via SendGrid."""
    from src.services.outreach_service import approve_and_send

    try:
        msg_uuid = UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="message_id must be a valid UUID",
        )

    async with AsyncSessionLocal() as session:
        try:
            result = await approve_and_send(session, msg_uuid)
            await session.commit()
        except NotFoundException as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=exc.message,
            )
        except BusinessRuleException as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=exc.message,
            )

    logger.info("Outreach approved and sent message_id=%s", message_id)
    return {"success": True, "data": result.model_dump(mode="json")}


@router.post("/messages/{message_id}/reject")
async def reject_message(
    message_id: str,
    body: OutreachRejectRequest,
) -> dict[str, Any]:
    """Reject a pending_review outreach message with a reason."""
    from src.services.outreach_service import reject

    try:
        msg_uuid = UUID(message_id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="message_id must be a valid UUID",
        )

    async with AsyncSessionLocal() as session:
        try:
            result = await reject(session, msg_uuid, body.reason)
            await session.commit()
        except NotFoundException as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=exc.message,
            )
        except BusinessRuleException as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=exc.message,
            )

    logger.info(
        "Outreach rejected message_id=%s reason=%r",
        message_id,
        body.reason,
    )
    return {"success": True, "data": result.model_dump(mode="json")}


# ---------------------------------------------------------------------------
# SendGrid webhook
# ---------------------------------------------------------------------------

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def sendgrid_webhook(request: Request) -> dict[str, Any]:
    """Handle SendGrid event webhooks.

    Accepts a JSON array of event objects from SendGrid.
    Updates message status for: open, click, delivered, bounce, spamreport.

    Note: Signature verification uses SENDGRID_WEBHOOK_SECRET when configured.
    In development, verification is skipped.
    """
    from src.services.outreach_service import handle_webhook_event

    try:
        events = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    if not isinstance(events, list):
        # SendGrid sends a JSON array; wrap a single object for compatibility
        events = [events]

    processed = 0
    async with AsyncSessionLocal() as session:
        for event in events:
            event_type: str = event.get("event", "")
            sg_msg_id: str = event.get("sg_message_id", "")
            timestamp_raw = event.get("timestamp")

            event_dt: datetime | None = None
            if timestamp_raw:
                try:
                    event_dt = datetime.fromtimestamp(float(timestamp_raw), tz=UTC)
                except (TypeError, ValueError, OSError):
                    event_dt = None

            if sg_msg_id:
                try:
                    await handle_webhook_event(
                        session,
                        event_type=event_type,
                        sendgrid_message_id=sg_msg_id,
                        timestamp=event_dt,
                    )
                    processed += 1
                except Exception as exc:
                    logger.warning(
                        "Webhook event processing failed event_type=%s sg_msg_id=%s: %s",
                        event_type,
                        sg_msg_id,
                        exc,
                    )

        await session.commit()

    logger.info("SendGrid webhook processed events=%d total=%d", processed, len(events))
    return {"success": True, "processed": processed}
