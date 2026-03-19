"""Unit tests for src/api/routers/enrichment.py.

TDD RED phase. Celery task and job store are mocked.
"""
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest


class TestTriggerEnrichment:
    @pytest.mark.asyncio
    async def test_returns_202_with_job_id(self, async_client) -> None:
        with patch("src.api.routers.enrichment.enrich_lead_task") as mock_task:
            mock_task.delay = MagicMock()
            lead_id = "a" * 8 + "-" + "b" * 4 + "-" + "c" * 4 + "-" + "d" * 4 + "-" + "e" * 12

            response = await async_client.post(f"/api/v1/enrichment/{lead_id}")

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data["data"]
        assert data["data"]["lead_id"] == lead_id
        assert data["data"]["status"] == "queued"

    @pytest.mark.asyncio
    async def test_job_id_is_valid_uuid(self, async_client) -> None:
        with patch("src.api.routers.enrichment.enrich_lead_task") as mock_task:
            mock_task.delay = MagicMock()
            lead_id = "a" * 8 + "-" + "b" * 4 + "-" + "c" * 4 + "-" + "d" * 4 + "-" + "e" * 12

            response = await async_client.post(f"/api/v1/enrichment/{lead_id}")

        job_id = response.json()["data"]["job_id"]
        UUID(job_id)  # raises ValueError if not valid UUID

    @pytest.mark.asyncio
    async def test_celery_task_dispatched_with_lead_id(self, async_client) -> None:
        with patch("src.api.routers.enrichment.enrich_lead_task") as mock_task:
            mock_task.delay = MagicMock()
            lead_id = "a" * 8 + "-" + "b" * 4 + "-" + "c" * 4 + "-" + "d" * 4 + "-" + "e" * 12

            await async_client.post(f"/api/v1/enrichment/{lead_id}")

        mock_task.delay.assert_called_once()
        call_kwargs = mock_task.delay.call_args.kwargs
        assert call_kwargs["lead_id"] == lead_id


class TestGetEnrichmentJobStatus:
    @pytest.mark.asyncio
    async def test_returns_queued_status(self, async_client) -> None:
        job_id = "test-job-123"
        job_data = {
            "job_id": job_id,
            "lead_id": "lead-456",
            "status": "queued",
        }

        with patch("src.api.routers.enrichment.get_job_status") as mock_get:
            mock_get.return_value = job_data

            response = await async_client.get(f"/api/v1/enrichment/jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "queued"

    @pytest.mark.asyncio
    async def test_returns_completed_status(self, async_client) -> None:
        job_id = "test-job-456"
        job_data = {
            "job_id": job_id,
            "lead_id": "lead-789",
            "status": "completed",
        }

        with patch("src.api.routers.enrichment.get_job_status") as mock_get:
            mock_get.return_value = job_data

            response = await async_client.get(f"/api/v1/enrichment/jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    @pytest.mark.asyncio
    async def test_returns_404_for_unknown_job(self, async_client) -> None:
        with patch("src.api.routers.enrichment.get_job_status") as mock_get:
            mock_get.return_value = None

            response = await async_client.get("/api/v1/enrichment/jobs/nonexistent-job")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_failed_status_with_error(self, async_client) -> None:
        job_id = "failed-job-123"
        job_data = {
            "job_id": job_id,
            "lead_id": "lead-999",
            "status": "failed",
            "error": "All enrichment providers failed",
        }

        with patch("src.api.routers.enrichment.get_job_status") as mock_get:
            mock_get.return_value = job_data

            response = await async_client.get(f"/api/v1/enrichment/jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["status"] == "failed"
        assert response.json()["error"] == "All enrichment providers failed"


class TestBatchEnrichment:
    @pytest.mark.asyncio
    async def test_batch_returns_202_with_job_id(self, async_client) -> None:
        lead_ids = [
            "a" * 8 + "-" + "b" * 4 + "-" + "c" * 4 + "-" + "d" * 4 + "-" + "e" * 12,
            "f" * 8 + "-" + "1" * 4 + "-" + "2" * 4 + "-" + "3" * 4 + "-" + "4" * 12,
        ]

        with patch("src.api.routers.enrichment.enrich_lead_task") as mock_task:
            mock_task.delay = MagicMock()

            response = await async_client.post(
                "/api/v1/enrichment/batch",
                json={"lead_ids": lead_ids},
            )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data["data"]
        assert data["data"]["total"] == len(lead_ids)
