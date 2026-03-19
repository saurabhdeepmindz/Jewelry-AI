"""Unit tests for src/tasks/enrichment.py.

Tests the async _run() coroutine directly — no Celery broker needed.
All DB, Redis, and service dependencies are mocked.

Patch strategy: inline imports inside _run() are resolved at call time from
their original source modules, so we patch at the source:
  - src.core.job_store.set_job_status
  - src.db.session.AsyncSessionLocal
  - src.services.enrichment_service.enrich_lead
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tasks.enrichment import _run

_SET = "src.core.job_store.set_job_status"
_SESSION = "src.db.session.AsyncSessionLocal"
_ENRICH = "src.services.enrichment_service.enrich_lead"


def _make_task_mock() -> MagicMock:
    task = MagicMock()
    task.request = MagicMock()
    task.request.retries = 0
    task.MaxRetriesExceededError = Exception
    return task


def _mock_session() -> MagicMock:
    session_cls = MagicMock()
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    session_cls.return_value = session
    return session_cls


def _make_contact_result(source: str | None = "apollo") -> MagicMock:
    contact = MagicMock()
    contact.id = uuid.uuid4()
    if source is None:
        contact.enrichment_source = None
    else:
        contact.enrichment_source = MagicMock()
        contact.enrichment_source.value = source
    return contact


class TestEnrichmentTaskRun:
    @pytest.mark.asyncio
    async def test_returns_completed_with_contact_id(self) -> None:
        job_id = str(uuid.uuid4())
        lead_id = str(uuid.uuid4())
        task = _make_task_mock()
        contact = _make_contact_result("apollo")

        with patch(_SET, new_callable=AsyncMock), \
             patch(_SESSION, _mock_session()), \
             patch(_ENRICH, new_callable=AsyncMock) as mock_enrich:

            mock_enrich.return_value = contact
            result = await _run(task, job_id, lead_id)

        assert result["status"] == "completed"
        assert result["job_id"] == job_id
        assert result["lead_id"] == lead_id
        assert result["contact_id"] == str(contact.id)
        assert result["enrichment_source"] == "apollo"

    @pytest.mark.asyncio
    async def test_sets_processing_status_before_enrichment(self) -> None:
        job_id = str(uuid.uuid4())
        lead_id = str(uuid.uuid4())
        task = _make_task_mock()
        set_calls: list = []

        async def capture_status(jid: str, data: dict) -> None:
            set_calls.append(data["status"])

        with patch(_SET, side_effect=capture_status), \
             patch(_SESSION, _mock_session()), \
             patch(_ENRICH, new_callable=AsyncMock) as mock_enrich:

            mock_enrich.return_value = _make_contact_result()
            await _run(task, job_id, lead_id)

        assert set_calls[0] == "processing"
        assert set_calls[-1] == "completed"

    @pytest.mark.asyncio
    async def test_returns_failed_when_max_retries_exceeded(self) -> None:
        job_id = str(uuid.uuid4())
        lead_id = str(uuid.uuid4())
        task = _make_task_mock()

        def retry_raiser(**kwargs):  # type: ignore[no-untyped-def]
            raise task.MaxRetriesExceededError("max retries exceeded")

        task.retry = MagicMock(side_effect=retry_raiser)

        with patch(_SET, new_callable=AsyncMock), \
             patch(_SESSION, _mock_session()), \
             patch(_ENRICH, new_callable=AsyncMock) as mock_enrich:

            mock_enrich.side_effect = RuntimeError("Service unavailable")
            result = await _run(task, job_id, lead_id)

        assert result["status"] == "failed"
        assert result["job_id"] == job_id
        assert result["lead_id"] == lead_id
        assert "Service unavailable" in result["error"]

    @pytest.mark.asyncio
    async def test_enrichment_source_is_none_when_contact_source_none(self) -> None:
        job_id = str(uuid.uuid4())
        lead_id = str(uuid.uuid4())
        task = _make_task_mock()
        contact = _make_contact_result(source=None)

        with patch(_SET, new_callable=AsyncMock), \
             patch(_SESSION, _mock_session()), \
             patch(_ENRICH, new_callable=AsyncMock) as mock_enrich:

            mock_enrich.return_value = contact
            result = await _run(task, job_id, lead_id)

        assert result["enrichment_source"] is None
