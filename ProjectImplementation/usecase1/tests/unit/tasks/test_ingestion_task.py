"""Unit tests for src/tasks/ingestion.py.

Tests the async _run() coroutine directly — no Celery broker needed.
All DB, Redis, and service dependencies are mocked.

Patch strategy: inline imports inside _run() are resolved at call time from
their original source modules, so we patch at the source:
  - src.core.job_store.set_job_status
  - src.db.session.AsyncSessionLocal
  - src.services.ingestion_service.ingest_csv
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.tasks.ingestion import _run

_SET = "src.core.job_store.set_job_status"
_SESSION = "src.db.session.AsyncSessionLocal"
_INGEST = "src.services.ingestion_service.ingest_csv"


def _make_ingestion_result(
    created: int = 3,
    skipped_duplicates: int = 1,
    skipped_invalid: int = 0,
    errors: int = 0,
) -> MagicMock:
    result = MagicMock()
    result.created = created
    result.skipped_duplicates = skipped_duplicates
    result.skipped_invalid = skipped_invalid
    result.errors = errors
    return result


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


CSV_CONTENT = """company_name,domain,country,source
Pristine Diamonds,pristine.example.com,US,gmt
Golden Baubles,golden.example.com,AE,trade_book
"""


class TestIngestionTaskRun:
    @pytest.mark.asyncio
    async def test_returns_completed_status_on_success(self) -> None:
        job_id = str(uuid.uuid4())
        task = _make_task_mock()
        ingestion_result = _make_ingestion_result(created=2)

        with patch(_SET, new_callable=AsyncMock), \
             patch(_SESSION, _mock_session()), \
             patch(_INGEST, new_callable=AsyncMock) as mock_ingest:

            mock_ingest.return_value = ingestion_result
            result = await _run(task, job_id, CSV_CONTENT)

        assert result["status"] == "completed"
        assert result["job_id"] == job_id
        assert result["created"] == 2

    @pytest.mark.asyncio
    async def test_sets_processing_status_before_work(self) -> None:
        job_id = str(uuid.uuid4())
        task = _make_task_mock()
        set_calls: list = []

        async def capture_status(jid: str, data: dict) -> None:
            set_calls.append(data["status"])

        with patch(_SET, side_effect=capture_status), \
             patch(_SESSION, _mock_session()), \
             patch(_INGEST, new_callable=AsyncMock) as mock_ingest:

            mock_ingest.return_value = _make_ingestion_result()
            await _run(task, job_id, CSV_CONTENT)

        assert set_calls[0] == "processing"
        assert set_calls[-1] == "completed"

    @pytest.mark.asyncio
    async def test_returns_failed_status_when_max_retries_exceeded(self) -> None:
        job_id = str(uuid.uuid4())
        task = _make_task_mock()

        def retry_raiser(**kwargs):  # type: ignore[no-untyped-def]
            raise task.MaxRetriesExceededError("max retries exceeded")

        task.retry = MagicMock(side_effect=retry_raiser)

        with patch(_SET, new_callable=AsyncMock), \
             patch(_SESSION, _mock_session()), \
             patch(_INGEST, new_callable=AsyncMock) as mock_ingest:

            mock_ingest.side_effect = RuntimeError("DB exploded")
            result = await _run(task, job_id, CSV_CONTENT)

        assert result["status"] == "failed"
        assert result["job_id"] == job_id
        assert "DB exploded" in result["error"]

    @pytest.mark.asyncio
    async def test_result_includes_all_counts(self) -> None:
        job_id = str(uuid.uuid4())
        task = _make_task_mock()
        ingestion_result = _make_ingestion_result(
            created=5, skipped_duplicates=2, skipped_invalid=1, errors=0
        )

        with patch(_SET, new_callable=AsyncMock), \
             patch(_SESSION, _mock_session()), \
             patch(_INGEST, new_callable=AsyncMock) as mock_ingest:

            mock_ingest.return_value = ingestion_result
            result = await _run(task, job_id, CSV_CONTENT)

        assert result["created"] == 5
        assert result["skipped_duplicates"] == 2
        assert result["skipped_invalid"] == 1
        assert result["errors"] == 0
