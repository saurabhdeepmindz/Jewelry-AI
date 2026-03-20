"""Unit tests for src/services/outreach_service.py.

TDD RED phase. All DB/API/LLM dependencies are mocked.
Patch paths must match where the names are used (module-level imports in service).
"""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.exceptions import BusinessRuleException, NotFoundException
from src.domain.outreach import OutreachRead, OutreachStatus
from src.services.outreach_service import (
    approve_and_send,
    generate_draft,
    handle_webhook_event,
    reject,
)


# ---------------------------------------------------------------------------
# Helpers — build MagicMock ORM objects
# ---------------------------------------------------------------------------

def _make_lead(
    lead_id: uuid.UUID | None = None,
    status: str = "enriched",
    company_name: str = "Pristine Diamonds Ltd",
    country: str | None = "US",
) -> MagicMock:
    lead = MagicMock()
    lead.id = lead_id or uuid.uuid4()
    lead.company_name = company_name
    lead.country = country
    lead.status = status
    lead.updated_at = datetime.now(UTC)
    return lead


def _make_contact(
    contact_id: uuid.UUID | None = None,
    lead_id: uuid.UUID | None = None,
    email: str | None = "sarah@pristine.example.com",
) -> MagicMock:
    contact = MagicMock()
    contact.id = contact_id or uuid.uuid4()
    contact.lead_id = lead_id or uuid.uuid4()
    contact.full_name = "Sarah Mitchell"
    contact.title = "Head Buyer"
    contact.email = email
    contact.email_verified = True
    contact.is_deleted = False
    contact.created_at = datetime.now(UTC)
    contact.updated_at = datetime.now(UTC)
    return contact


def _make_outreach_message(
    message_id: uuid.UUID | None = None,
    lead_id: uuid.UUID | None = None,
    contact_id: uuid.UUID | None = None,
    status: str = "pending_review",
) -> MagicMock:
    msg = MagicMock()
    msg.id = message_id or uuid.uuid4()
    msg.lead_id = lead_id or uuid.uuid4()
    msg.contact_id = contact_id or uuid.uuid4()
    msg.channel = "email"
    msg.subject = "Test Subject"
    msg.body = "<p>Test body</p>"
    msg.sequence_step = 1
    msg.status = status
    msg.rejection_reason = None
    msg.approved_by = None
    msg.approved_at = None
    msg.sendgrid_message_id = None
    msg.sent_at = None
    msg.opened_at = None
    msg.clicked_at = None
    msg.replied_at = None
    msg.bounced_at = None
    msg.is_deleted = False
    msg.created_at = datetime.now(UTC)
    msg.updated_at = datetime.now(UTC)
    return msg


def _make_outreach_read(message: MagicMock) -> OutreachRead:
    return OutreachRead(
        id=message.id,
        lead_id=message.lead_id,
        contact_id=message.contact_id,
        channel="email",
        subject=message.subject,
        body=message.body,
        sequence_step=1,
        status=OutreachStatus(message.status),
        rejection_reason=message.rejection_reason,
        approved_by=message.approved_by,
        approved_at=message.approved_at,
        sendgrid_message_id=message.sendgrid_message_id,
        sent_at=message.sent_at,
        opened_at=message.opened_at,
        clicked_at=message.clicked_at,
        replied_at=message.replied_at,
        bounced_at=message.bounced_at,
        is_deleted=False,
        created_at=message.created_at,
        updated_at=message.updated_at,
    )


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


# ---------------------------------------------------------------------------
# generate_draft tests
# ---------------------------------------------------------------------------

class TestGenerateDraft:
    @pytest.mark.asyncio
    async def test_creates_pending_review_when_human_review_required(
        self, mock_session: AsyncMock
    ) -> None:
        lead = _make_lead(status="enriched")
        contact = _make_contact(lead_id=lead.id)
        created_msg = _make_outreach_message(
            lead_id=lead.id,
            contact_id=contact.id,
            status="pending_review",
        )

        with patch("src.services.outreach_service.LeadRepository") as MockLeadRepo, \
             patch("src.services.outreach_service.ContactRepository") as MockContactRepo, \
             patch("src.services.outreach_service.OutreachRepository") as MockOutreachRepo, \
             patch("src.services.outreach_service._get_outreach_agent") as mock_get_agent, \
             patch("src.services.outreach_service.get_settings") as mock_settings:

            settings = MagicMock()
            settings.HUMAN_REVIEW_REQUIRED = True
            settings.OPENAI_API_KEY = "test-key"
            mock_settings.return_value = settings

            MockLeadRepo.return_value.get_by_id = AsyncMock(return_value=lead)
            MockContactRepo.return_value.get_active_by_lead_id = AsyncMock(return_value=contact)

            agent_fn = AsyncMock(return_value={"subject": "Test Subject", "body": "<p>Test</p>"})
            mock_get_agent.return_value = agent_fn

            created_msg.status = "pending_review"
            MockOutreachRepo.return_value.create = AsyncMock(return_value=created_msg)

            # Patch OutreachRead.model_validate to return a real OutreachRead
            with patch("src.services.outreach_service.OutreachRead") as MockOutreachRead:
                expected_read = _make_outreach_read(created_msg)
                MockOutreachRead.model_validate = MagicMock(return_value=expected_read)

                result = await generate_draft(mock_session, lead.id)

            assert result is not None
            MockOutreachRepo.return_value.create.assert_awaited_once()
            agent_fn.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_lead_missing(
        self, mock_session: AsyncMock
    ) -> None:
        lead_id = uuid.uuid4()

        with patch("src.services.outreach_service.LeadRepository") as MockLeadRepo, \
             patch("src.services.outreach_service.get_settings"):

            MockLeadRepo.return_value.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(NotFoundException):
                await generate_draft(mock_session, lead_id)

    @pytest.mark.asyncio
    async def test_raises_lead_not_eligible_when_status_not_enriched(
        self, mock_session: AsyncMock
    ) -> None:
        from src.core.exceptions import LeadNotEligibleException

        lead = _make_lead(status="ingested")

        with patch("src.services.outreach_service.LeadRepository") as MockLeadRepo, \
             patch("src.services.outreach_service.get_settings"):

            MockLeadRepo.return_value.get_by_id = AsyncMock(return_value=lead)

            with pytest.raises(LeadNotEligibleException):
                await generate_draft(mock_session, lead.id)


# ---------------------------------------------------------------------------
# approve_and_send tests
# ---------------------------------------------------------------------------

class TestApproveAndSend:
    @pytest.mark.asyncio
    async def test_sends_email_and_updates_status_to_sent(
        self, mock_session: AsyncMock
    ) -> None:
        contact = _make_contact()
        msg = _make_outreach_message(contact_id=contact.id, status="pending_review")
        sent_msg = _make_outreach_message(
            message_id=msg.id,
            lead_id=msg.lead_id,
            contact_id=msg.contact_id,
            status="sent",
        )
        sent_msg.sendgrid_message_id = "SG.test123"
        sent_msg.sent_at = datetime.now(UTC)

        with patch("src.services.outreach_service.OutreachRepository") as MockOutreachRepo, \
             patch("src.services.outreach_service.ContactRepository") as MockContactRepo, \
             patch("src.services.outreach_service.LeadRepository") as MockLeadRepo, \
             patch("src.services.outreach_service._get_sendgrid_client") as mock_sg_factory:

            MockOutreachRepo.return_value.get_by_id = AsyncMock(return_value=msg)
            MockContactRepo.return_value.get_by_id = AsyncMock(return_value=contact)
            MockLeadRepo.return_value.get_by_id = AsyncMock(return_value=_make_lead(lead_id=msg.lead_id))

            sg_client_instance = AsyncMock()
            sg_client_instance.send_email = AsyncMock(return_value="SG.test123")
            MockSGClass = MagicMock(return_value=sg_client_instance)
            mock_sg_factory.return_value = MockSGClass

            MockOutreachRepo.return_value.update_status = AsyncMock(return_value=sent_msg)

            with patch("src.services.outreach_service.OutreachRead") as MockOutreachRead:
                expected_read = _make_outreach_read(sent_msg)
                MockOutreachRead.model_validate = MagicMock(return_value=expected_read)

                result = await approve_and_send(mock_session, msg.id)

            sg_client_instance.send_email.assert_awaited_once()
            MockOutreachRepo.return_value.update_status.assert_awaited_once()
            assert result is not None

    @pytest.mark.asyncio
    async def test_raises_business_rule_when_status_not_pending_review(
        self, mock_session: AsyncMock
    ) -> None:
        msg = _make_outreach_message(status="sent")

        with patch("src.services.outreach_service.OutreachRepository") as MockOutreachRepo:
            MockOutreachRepo.return_value.get_by_id = AsyncMock(return_value=msg)

            with pytest.raises(BusinessRuleException):
                await approve_and_send(mock_session, msg.id)

    @pytest.mark.asyncio
    async def test_raises_business_rule_when_contact_has_no_email(
        self, mock_session: AsyncMock
    ) -> None:
        contact = _make_contact(email=None)
        msg = _make_outreach_message(contact_id=contact.id, status="pending_review")

        with patch("src.services.outreach_service.OutreachRepository") as MockOutreachRepo, \
             patch("src.services.outreach_service.ContactRepository") as MockContactRepo:

            MockOutreachRepo.return_value.get_by_id = AsyncMock(return_value=msg)
            MockContactRepo.return_value.get_by_id = AsyncMock(return_value=contact)

            with pytest.raises(BusinessRuleException):
                await approve_and_send(mock_session, msg.id)


# ---------------------------------------------------------------------------
# reject tests
# ---------------------------------------------------------------------------

class TestReject:
    @pytest.mark.asyncio
    async def test_updates_status_to_rejected_with_reason(
        self, mock_session: AsyncMock
    ) -> None:
        msg = _make_outreach_message(status="pending_review")
        rejected_msg = _make_outreach_message(
            message_id=msg.id,
            lead_id=msg.lead_id,
            contact_id=msg.contact_id,
            status="rejected",
        )
        rejected_msg.rejection_reason = "Tone is too aggressive"

        with patch("src.services.outreach_service.OutreachRepository") as MockOutreachRepo:
            MockOutreachRepo.return_value.get_by_id = AsyncMock(return_value=msg)
            MockOutreachRepo.return_value.update_status = AsyncMock(return_value=rejected_msg)

            with patch("src.services.outreach_service.OutreachRead") as MockOutreachRead:
                expected_read = _make_outreach_read(rejected_msg)
                MockOutreachRead.model_validate = MagicMock(return_value=expected_read)

                result = await reject(mock_session, msg.id, "Tone is too aggressive")

            MockOutreachRepo.return_value.update_status.assert_awaited_once_with(
                msg.id,
                OutreachStatus.rejected.value,
                rejection_reason="Tone is too aggressive",
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_raises_business_rule_when_status_not_pending_review(
        self, mock_session: AsyncMock
    ) -> None:
        msg = _make_outreach_message(status="sent")

        with patch("src.services.outreach_service.OutreachRepository") as MockOutreachRepo:
            MockOutreachRepo.return_value.get_by_id = AsyncMock(return_value=msg)

            with pytest.raises(BusinessRuleException):
                await reject(mock_session, msg.id, "Some reason")

    @pytest.mark.asyncio
    async def test_raises_not_found_when_message_missing(
        self, mock_session: AsyncMock
    ) -> None:
        with patch("src.services.outreach_service.OutreachRepository") as MockOutreachRepo:
            MockOutreachRepo.return_value.get_by_id = AsyncMock(return_value=None)

            with pytest.raises(NotFoundException):
                await reject(mock_session, uuid.uuid4(), "reason")


# ---------------------------------------------------------------------------
# handle_webhook_event tests
# ---------------------------------------------------------------------------

class TestHandleWebhookEvent:
    @pytest.mark.asyncio
    async def test_open_event_updates_opened_at_and_status(
        self, mock_session: AsyncMock
    ) -> None:
        msg = _make_outreach_message(status="sent")
        msg.sendgrid_message_id = "SG.abc123"
        opened_msg = _make_outreach_message(
            message_id=msg.id,
            lead_id=msg.lead_id,
            contact_id=msg.contact_id,
            status="opened",
        )
        event_ts = datetime.now(UTC)
        opened_msg.opened_at = event_ts

        with patch("src.services.outreach_service.OutreachRepository") as MockOutreachRepo:
            MockOutreachRepo.return_value.get_by_sendgrid_message_id = AsyncMock(return_value=msg)
            MockOutreachRepo.return_value.update_status = AsyncMock(return_value=opened_msg)

            with patch("src.services.outreach_service.OutreachRead") as MockOutreachRead:
                expected_read = _make_outreach_read(opened_msg)
                MockOutreachRead.model_validate = MagicMock(return_value=expected_read)

                result = await handle_webhook_event(
                    mock_session,
                    event_type="open",
                    sendgrid_message_id="SG.abc123",
                    timestamp=event_ts,
                )

            MockOutreachRepo.return_value.update_status.assert_awaited_once_with(
                msg.id,
                OutreachStatus.opened.value,
                opened_at=event_ts,
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_bounce_event_updates_bounced_at_and_status(
        self, mock_session: AsyncMock
    ) -> None:
        msg = _make_outreach_message(status="sent")
        msg.sendgrid_message_id = "SG.bounce123"
        bounced_msg = _make_outreach_message(
            message_id=msg.id,
            lead_id=msg.lead_id,
            contact_id=msg.contact_id,
            status="bounced",
        )
        event_ts = datetime.now(UTC)
        bounced_msg.bounced_at = event_ts

        with patch("src.services.outreach_service.OutreachRepository") as MockOutreachRepo:
            MockOutreachRepo.return_value.get_by_sendgrid_message_id = AsyncMock(return_value=msg)
            MockOutreachRepo.return_value.update_status = AsyncMock(return_value=bounced_msg)

            with patch("src.services.outreach_service.OutreachRead") as MockOutreachRead:
                expected_read = _make_outreach_read(bounced_msg)
                MockOutreachRead.model_validate = MagicMock(return_value=expected_read)

                result = await handle_webhook_event(
                    mock_session,
                    event_type="bounce",
                    sendgrid_message_id="SG.bounce123",
                    timestamp=event_ts,
                )

            MockOutreachRepo.return_value.update_status.assert_awaited_once_with(
                msg.id,
                OutreachStatus.bounced.value,
                bounced_at=event_ts,
            )
            assert result is not None

    @pytest.mark.asyncio
    async def test_unknown_sendgrid_id_returns_none(
        self, mock_session: AsyncMock
    ) -> None:
        with patch("src.services.outreach_service.OutreachRepository") as MockOutreachRepo:
            MockOutreachRepo.return_value.get_by_sendgrid_message_id = AsyncMock(return_value=None)

            result = await handle_webhook_event(
                mock_session,
                event_type="open",
                sendgrid_message_id="SG.unknown",
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_delivered_event_makes_no_status_change(
        self, mock_session: AsyncMock
    ) -> None:
        msg = _make_outreach_message(status="sent")
        msg.sendgrid_message_id = "SG.delivered123"

        with patch("src.services.outreach_service.OutreachRepository") as MockOutreachRepo:
            MockOutreachRepo.return_value.get_by_sendgrid_message_id = AsyncMock(return_value=msg)
            MockOutreachRepo.return_value.update_status = AsyncMock()

            with patch("src.services.outreach_service.OutreachRead") as MockOutreachRead:
                expected_read = _make_outreach_read(msg)
                MockOutreachRead.model_validate = MagicMock(return_value=expected_read)

                await handle_webhook_event(
                    mock_session,
                    event_type="delivered",
                    sendgrid_message_id="SG.delivered123",
                )

            # update_status should NOT have been called for delivered
            MockOutreachRepo.return_value.update_status.assert_not_awaited()
