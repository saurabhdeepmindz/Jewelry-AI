"""Outreach generation and lifecycle service.

Workflow:
  1. generate_draft(session, lead_id) — validates lead is enriched+eligible, fetches
     contact and inventory matches, calls OutreachAgent, saves draft with
     status=pending_review (or immediately sends if HUMAN_REVIEW_REQUIRED=False).
  2. approve_and_send(session, message_id) — validates status=pending_review, calls
     SendGridClient, updates status=sent, records sent_at and sendgrid_message_id.
  3. reject(session, message_id, reason) — validates status=pending_review, updates
     status=rejected with rejection_reason.
  4. handle_webhook_event(session, event_type, sendgrid_message_id, timestamp) — updates
     opened_at/clicked_at/replied_at/bounced_at on the matching message.
  5. update_draft(session, message_id, data) — allows editing body/subject while
     status=draft or pending_review.
"""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    BusinessRuleException,
    ContactNotFoundException,
    LeadNotEligibleException,
    NotFoundException,
)
from src.core.logging import get_logger
from src.domain.outreach import (
    OutreachCreate,
    OutreachRead,
    OutreachStatus,
    OutreachUpdate,
)
from src.repositories.contact_repository import ContactRepository
from src.repositories.lead_repository import LeadRepository
from src.repositories.outreach_repository import OutreachRepository

logger = get_logger(__name__)

# Lead statuses that are eligible for outreach generation
_ELIGIBLE_STATUSES = {"enriched", "scored", "contacted"}


def _get_outreach_agent():  # type: ignore[return]
    """Lazy import — avoid loading LangChain at startup."""
    from src.agents.outreach_agent import run_outreach_agent
    return run_outreach_agent


def _get_sendgrid_client():  # type: ignore[return]
    """Lazy import — avoid loading SendGrid SDK at startup."""
    from src.integrations.sendgrid_client import SendGridClient
    return SendGridClient


async def generate_draft(session: AsyncSession, lead_id: UUID) -> OutreachRead:
    """Generate an AI outreach email draft for a lead.

    Parameters
    ----------
    session:
        Active async database session (caller is responsible for commit).
    lead_id:
        UUID of the lead to generate outreach for.

    Returns
    -------
    OutreachRead
        The newly created outreach message record.

    Raises
    ------
    NotFoundException
        Lead does not exist or has been soft-deleted.
    LeadNotEligibleException
        Lead status is not in (enriched, scored, contacted).
    """
    from src.core.config import get_settings
    settings = get_settings()

    lead_repo = LeadRepository(session)
    contact_repo = ContactRepository(session)
    outreach_repo = OutreachRepository(session)

    # 1. Load lead
    lead = await lead_repo.get_by_id(lead_id)
    if lead is None:
        raise NotFoundException(f"Lead {lead_id!r} not found")

    # 2. Validate lead status
    if lead.status not in _ELIGIBLE_STATUSES:
        raise LeadNotEligibleException(
            f"Lead {lead_id!r} has status={lead.status!r} — "
            f"must be one of {sorted(_ELIGIBLE_STATUSES)} to generate outreach"
        )

    # 3. Load active contact
    contact = await contact_repo.get_active_by_lead_id(lead_id)

    # 4. TODO: fetch real inventory matches when EPIC-03 is implemented
    # For now, use an empty list — outreach agent will write a general introduction
    inventory_matches: list[dict] = []

    # 5. Build context for the agent
    from src.agents.outreach_agent import OutreachContext
    ctx: OutreachContext = {
        "company_name": lead.company_name,
        "country": lead.country,
        "contact_name": contact.full_name if contact else None,
        "contact_title": contact.title if contact else None,
        "inventory_matches": inventory_matches,
        "sequence_step": 1,
    }

    # 6. Call the outreach agent
    run_outreach_agent = _get_outreach_agent()
    draft = await run_outreach_agent(ctx)

    # 7. Determine initial status
    initial_status = (
        OutreachStatus.pending_review.value
        if settings.HUMAN_REVIEW_REQUIRED
        else OutreachStatus.approved.value
    )

    # 8. Persist the draft
    create_data = OutreachCreate(
        lead_id=lead_id,
        contact_id=contact.id if contact else None,
        channel="email",
        subject=draft["subject"],
        body=draft["body"],
        sequence_step=1,
    )
    message = await outreach_repo.create(create_data)

    # Set status after creation (create always sets draft)
    message.status = initial_status
    message.updated_at = datetime.now(UTC)
    await session.flush()

    logger.info(
        "Outreach draft generated lead_id=%s message_id=%s status=%s",
        lead_id,
        message.id,
        initial_status,
    )

    # 9. If human review is NOT required, immediately send
    if not settings.HUMAN_REVIEW_REQUIRED:
        return await approve_and_send(session, message.id)

    return OutreachRead.model_validate(message)


async def approve_and_send(session: AsyncSession, message_id: UUID) -> OutreachRead:
    """Approve a pending_review message and send it via SendGrid.

    Parameters
    ----------
    session:
        Active async database session (caller is responsible for commit).
    message_id:
        UUID of the outreach message to approve and send.

    Returns
    -------
    OutreachRead
        The updated outreach message with status=sent.

    Raises
    ------
    NotFoundException
        Message does not exist.
    BusinessRuleException
        Message is not in pending_review status.
    ContactNotFoundException
        Contact record not found for email delivery.
    """
    outreach_repo = OutreachRepository(session)
    contact_repo = ContactRepository(session)

    # 1. Load message
    message = await outreach_repo.get_by_id(message_id)
    if message is None:
        raise NotFoundException(f"OutreachMessage {message_id!r} not found")

    # 2. Validate status
    if message.status != OutreachStatus.pending_review.value:
        raise BusinessRuleException(
            f"OutreachMessage {message_id!r} has status={message.status!r} — "
            "only 'pending_review' messages can be approved and sent"
        )

    # 3. Resolve contact email
    to_email: str | None = None
    if message.contact_id:
        contact = await contact_repo.get_by_id(message.contact_id)
        if contact is None:
            raise ContactNotFoundException(
                f"Contact {message.contact_id!r} not found for outreach delivery"
            )
        to_email = contact.email

    if not to_email:
        raise BusinessRuleException(
            f"OutreachMessage {message_id!r}: contact has no email address — cannot send"
        )

    # 4. Send via SendGrid
    SendGridClient = _get_sendgrid_client()
    sg_client = SendGridClient()
    sg_message_id = await sg_client.send_email(
        to_email=to_email,
        subject=message.subject or "(No subject)",
        body_html=message.body,
    )

    # 5. Update message status
    now = datetime.now(UTC)
    updated = await outreach_repo.update_status(
        message_id,
        OutreachStatus.sent.value,
        sendgrid_message_id=sg_message_id,
        sent_at=now,
        approved_at=now,
    )

    # 6. Update lead status to "contacted"
    lead_repo = LeadRepository(session)
    lead = await lead_repo.get_by_id(message.lead_id)
    if lead is not None:
        lead.status = "contacted"
        lead.updated_at = datetime.now(UTC)
        await session.flush()

    logger.info(
        "Outreach sent message_id=%s to=%s sg_message_id=%s",
        message_id,
        to_email,
        sg_message_id,
    )

    return OutreachRead.model_validate(updated)


async def reject(
    session: AsyncSession,
    message_id: UUID,
    reason: str,
) -> OutreachRead:
    """Reject a pending_review outreach message.

    Parameters
    ----------
    session:
        Active async database session (caller is responsible for commit).
    message_id:
        UUID of the outreach message to reject.
    reason:
        Human-readable rejection reason recorded on the message.

    Returns
    -------
    OutreachRead
        The updated outreach message with status=rejected.

    Raises
    ------
    NotFoundException
        Message does not exist.
    BusinessRuleException
        Message is not in pending_review status.
    """
    outreach_repo = OutreachRepository(session)

    message = await outreach_repo.get_by_id(message_id)
    if message is None:
        raise NotFoundException(f"OutreachMessage {message_id!r} not found")

    if message.status != OutreachStatus.pending_review.value:
        raise BusinessRuleException(
            f"OutreachMessage {message_id!r} has status={message.status!r} — "
            "only 'pending_review' messages can be rejected"
        )

    updated = await outreach_repo.update_status(
        message_id,
        OutreachStatus.rejected.value,
        rejection_reason=reason,
    )

    logger.info(
        "Outreach rejected message_id=%s reason=%r",
        message_id,
        reason,
    )

    return OutreachRead.model_validate(updated)


async def handle_webhook_event(
    session: AsyncSession,
    event_type: str,
    sendgrid_message_id: str,
    timestamp: datetime | None = None,
) -> OutreachRead | None:
    """Update outreach message status based on a SendGrid webhook event.

    Parameters
    ----------
    session:
        Active async database session (caller is responsible for commit).
    event_type:
        SendGrid event type: "open", "click", "delivered", "bounce",
        "spamreport", etc.
    sendgrid_message_id:
        The X-Message-Id from the original send response.
    timestamp:
        Event timestamp (defaults to UTC now if not provided).

    Returns
    -------
    OutreachRead | None
        The updated message, or None if not found by sendgrid_message_id.
    """
    outreach_repo = OutreachRepository(session)
    event_ts = timestamp or datetime.now(UTC)

    message = await outreach_repo.get_by_sendgrid_message_id(sendgrid_message_id)
    if message is None:
        logger.warning(
            "Webhook event=%s for unknown sendgrid_message_id=%s",
            event_type,
            sendgrid_message_id,
        )
        return None

    kwargs: dict = {}
    new_status: str | None = None

    if event_type == "open":
        kwargs["opened_at"] = event_ts
        new_status = OutreachStatus.opened.value
    elif event_type == "click":
        kwargs["clicked_at"] = event_ts
        new_status = OutreachStatus.clicked.value
    elif event_type == "delivered":
        # No status change — delivery is implicitly confirmed by sent status
        logger.debug(
            "Webhook 'delivered' received for message_id=%s — no status update needed",
            message.id,
        )
        return OutreachRead.model_validate(message)
    elif event_type in ("bounce", "blocked"):
        kwargs["bounced_at"] = event_ts
        new_status = OutreachStatus.bounced.value
    elif event_type == "spamreport":
        new_status = OutreachStatus.bounced.value
    else:
        logger.info(
            "Webhook unhandled event_type=%s for message_id=%s",
            event_type,
            message.id,
        )
        return OutreachRead.model_validate(message)

    if new_status is not None:
        updated = await outreach_repo.update_status(message.id, new_status, **kwargs)
        logger.info(
            "Webhook event=%s processed message_id=%s new_status=%s",
            event_type,
            message.id,
            new_status,
        )
        return OutreachRead.model_validate(updated)

    return OutreachRead.model_validate(message)


async def update_draft(
    session: AsyncSession,
    message_id: UUID,
    data: OutreachUpdate,
) -> OutreachRead:
    """Edit body and/or subject of a draft or pending_review message.

    Parameters
    ----------
    session:
        Active async database session (caller is responsible for commit).
    message_id:
        UUID of the outreach message to edit.
    data:
        OutreachUpdate with optional subject and body fields.

    Returns
    -------
    OutreachRead
        The updated outreach message.

    Raises
    ------
    NotFoundException
        Message does not exist.
    BusinessRuleException
        Message cannot be edited in its current status (only draft/pending_review allowed).
    """
    outreach_repo = OutreachRepository(session)

    message = await outreach_repo.get_by_id(message_id)
    if message is None:
        raise NotFoundException(f"OutreachMessage {message_id!r} not found")

    editable_statuses = {OutreachStatus.draft.value, OutreachStatus.pending_review.value}
    if message.status not in editable_statuses:
        raise BusinessRuleException(
            f"OutreachMessage {message_id!r} has status={message.status!r} — "
            "only 'draft' or 'pending_review' messages can be edited"
        )

    if data.subject is not None:
        message.subject = data.subject
    if data.body is not None:
        message.body = data.body

    message.updated_at = datetime.now(UTC)
    await session.flush()

    logger.info("Outreach draft updated message_id=%s", message_id)

    return OutreachRead.model_validate(message)
