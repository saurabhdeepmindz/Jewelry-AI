"""Unit tests for src/api/routers/outreach.py.

TDD RED phase. Celery task, job store, and service functions are mocked.
"""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.outreach import OutreachRead, OutreachStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_outreach_read(
    message_id: uuid.UUID | None = None,
    lead_id: uuid.UUID | None = None,
    status: str = "pending_review",
) -> OutreachRead:
    now = datetime.now(UTC)
    return OutreachRead(
        id=message_id or uuid.uuid4(),
        lead_id=lead_id or uuid.uuid4(),
        contact_id=uuid.uuid4(),
        channel="email",
        subject="Test Subject",
        body="<p>Test body</p>",
        sequence_step=1,
        status=OutreachStatus(status),
        rejection_reason=None,
        approved_by=None,
        approved_at=None,
        sendgrid_message_id=None,
        sent_at=None,
        opened_at=None,
        clicked_at=None,
        replied_at=None,
        bounced_at=None,
        is_deleted=False,
        created_at=now,
        updated_at=now,
    )


_VALID_UUID = "a" * 8 + "-" + "b" * 4 + "-" + "c" * 4 + "-" + "d" * 4 + "-" + "e" * 12


# ---------------------------------------------------------------------------
# POST /generate/{lead_id}
# ---------------------------------------------------------------------------

class TestTriggerOutreachGeneration:
    @pytest.mark.asyncio
    async def test_returns_202_with_job_id(self, async_client) -> None:
        with patch("src.api.routers.outreach.generate_outreach_task") as mock_task:
            mock_task.delay = MagicMock()

            response = await async_client.post(f"/api/v1/outreach/generate/{_VALID_UUID}")

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data["data"]
        assert data["data"]["lead_id"] == _VALID_UUID
        assert data["data"]["status"] == "queued"

    @pytest.mark.asyncio
    async def test_job_id_is_valid_uuid(self, async_client) -> None:
        with patch("src.api.routers.outreach.generate_outreach_task") as mock_task:
            mock_task.delay = MagicMock()

            response = await async_client.post(f"/api/v1/outreach/generate/{_VALID_UUID}")

        job_id = response.json()["data"]["job_id"]
        uuid.UUID(job_id)  # raises ValueError if not valid UUID

    @pytest.mark.asyncio
    async def test_celery_task_dispatched_with_lead_id(self, async_client) -> None:
        with patch("src.api.routers.outreach.generate_outreach_task") as mock_task:
            mock_task.delay = MagicMock()

            await async_client.post(f"/api/v1/outreach/generate/{_VALID_UUID}")

        mock_task.delay.assert_called_once()
        call_kwargs = mock_task.delay.call_args.kwargs
        assert call_kwargs["lead_id"] == _VALID_UUID


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}
# ---------------------------------------------------------------------------

class TestGetOutreachJobStatus:
    @pytest.mark.asyncio
    async def test_returns_queued_status(self, async_client) -> None:
        job_id = "test-job-abc"
        job_data = {
            "job_id": job_id,
            "lead_id": _VALID_UUID,
            "status": "queued",
        }

        with patch("src.api.routers.outreach.get_job_status") as mock_get:
            mock_get.return_value = job_data

            response = await async_client.get(f"/api/v1/outreach/jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "queued"

    @pytest.mark.asyncio
    async def test_returns_completed_status_with_message_id(self, async_client) -> None:
        job_id = "test-job-def"
        msg_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id,
            "lead_id": _VALID_UUID,
            "status": "completed",
            "message_id": msg_id,
        }

        with patch("src.api.routers.outreach.get_job_status") as mock_get:
            mock_get.return_value = job_data

            response = await async_client.get(f"/api/v1/outreach/jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["message_id"] == msg_id

    @pytest.mark.asyncio
    async def test_returns_404_for_unknown_job(self, async_client) -> None:
        with patch("src.api.routers.outreach.get_job_status") as mock_get:
            mock_get.return_value = None

            response = await async_client.get("/api/v1/outreach/jobs/nonexistent-job")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /messages
# ---------------------------------------------------------------------------

class TestListMessages:
    @pytest.mark.asyncio
    async def test_returns_list_of_messages(self, async_client) -> None:
        msg = _make_outreach_read()

        with patch("src.api.routers.outreach.AsyncSessionLocal") as MockSession, \
             patch("src.api.routers.outreach.OutreachRepository") as MockRepo:

            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=False)
            MockSession.return_value = mock_session_instance

            mock_orm_msg = MagicMock()
            MockRepo.return_value.list_all = AsyncMock(return_value=[mock_orm_msg])

            with patch("src.api.routers.outreach.OutreachRead") as MockRead:
                MockRead.model_validate = MagicMock(return_value=msg)

                response = await async_client.get("/api/v1/outreach/messages")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_messages(self, async_client) -> None:
        with patch("src.api.routers.outreach.AsyncSessionLocal") as MockSession, \
             patch("src.api.routers.outreach.OutreachRepository") as MockRepo:

            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=False)
            MockSession.return_value = mock_session_instance

            MockRepo.return_value.list_all = AsyncMock(return_value=[])

            response = await async_client.get("/api/v1/outreach/messages")

        assert response.status_code == 200
        assert response.json()["data"] == []


# ---------------------------------------------------------------------------
# POST /messages/{message_id}/approve
# ---------------------------------------------------------------------------

class TestApproveMessage:
    @pytest.mark.asyncio
    async def test_approve_returns_200_with_sent_message(self, async_client) -> None:
        message_id = str(uuid.uuid4())
        sent_msg = _make_outreach_read(
            message_id=uuid.UUID(message_id),
            status="sent",
        )

        with patch("src.api.routers.outreach.AsyncSessionLocal") as MockSession, \
             patch("src.api.routers.outreach.approve_and_send") as mock_approve:

            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=False)
            mock_session_instance.commit = AsyncMock()
            MockSession.return_value = mock_session_instance

            mock_approve.return_value = sent_msg

            response = await async_client.post(
                f"/api/v1/outreach/messages/{message_id}/approve"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_approve_returns_400_for_wrong_status(self, async_client) -> None:
        from src.core.exceptions import BusinessRuleException

        message_id = str(uuid.uuid4())

        with patch("src.api.routers.outreach.AsyncSessionLocal") as MockSession, \
             patch("src.api.routers.outreach.approve_and_send") as mock_approve:

            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=False)
            mock_session_instance.commit = AsyncMock()
            MockSession.return_value = mock_session_instance

            mock_approve.side_effect = BusinessRuleException("Message is not pending review")

            response = await async_client.post(
                f"/api/v1/outreach/messages/{message_id}/approve"
            )

        assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /messages/{message_id}/reject
# ---------------------------------------------------------------------------

class TestRejectMessage:
    @pytest.mark.asyncio
    async def test_reject_returns_200_with_rejected_message(self, async_client) -> None:
        message_id = str(uuid.uuid4())
        rejected_msg = _make_outreach_read(
            message_id=uuid.UUID(message_id),
            status="rejected",
        )

        with patch("src.api.routers.outreach.AsyncSessionLocal") as MockSession, \
             patch("src.api.routers.outreach.reject") as mock_reject:

            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=False)
            mock_session_instance.commit = AsyncMock()
            MockSession.return_value = mock_session_instance

            mock_reject.return_value = rejected_msg

            response = await async_client.post(
                f"/api/v1/outreach/messages/{message_id}/reject",
                json={"reason": "Tone needs adjustment"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_reject_returns_400_for_already_sent(self, async_client) -> None:
        from src.core.exceptions import BusinessRuleException

        message_id = str(uuid.uuid4())

        with patch("src.api.routers.outreach.AsyncSessionLocal") as MockSession, \
             patch("src.api.routers.outreach.reject") as mock_reject:

            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=False)
            mock_session_instance.commit = AsyncMock()
            MockSession.return_value = mock_session_instance

            mock_reject.side_effect = BusinessRuleException("Message is not pending review")

            response = await async_client.post(
                f"/api/v1/outreach/messages/{message_id}/reject",
                json={"reason": "Some reason"},
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_reject_returns_404_when_message_not_found(self, async_client) -> None:
        from src.core.exceptions import NotFoundException

        message_id = str(uuid.uuid4())

        with patch("src.api.routers.outreach.AsyncSessionLocal") as MockSession, \
             patch("src.api.routers.outreach.reject") as mock_reject:

            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=False)
            mock_session_instance.commit = AsyncMock()
            MockSession.return_value = mock_session_instance

            mock_reject.side_effect = NotFoundException("OutreachMessage not found")

            response = await async_client.post(
                f"/api/v1/outreach/messages/{message_id}/reject",
                json={"reason": "Some reason"},
            )

        assert response.status_code == 404
