"""Unit tests for src/api/routers/leads.py.

TDD: Celery tasks and job store are mocked — no Redis or worker required.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient


def _make_csv_bytes(*rows: dict) -> bytes:
    if not rows:
        return b"company_name,domain,country,source\n"
    headers = list(rows[0].keys())
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(row.get(h, "")) for h in headers))
    return ("\n".join(lines) + "\n").encode()


class TestUploadEndpoint:
    async def test_valid_csv_returns_202_with_job_id(self, async_client: AsyncClient) -> None:
        csv_bytes = _make_csv_bytes(
            {"company_name": "Acme Corp", "domain": "acme.com", "country": "US", "source": "gmt"}
        )
        with patch("src.api.routers.leads.ingest_lead_file") as mock_task:
            mock_task.delay = MagicMock()
            response = await async_client.post(
                "/api/v1/leads/upload",
                files={"file": ("leads.csv", csv_bytes, "text/csv")},
            )
        assert response.status_code == 202
        body = response.json()
        assert "job_id" in body
        # job_id must be a valid UUID
        uuid.UUID(body["job_id"])

    async def test_celery_task_dispatched_on_upload(self, async_client: AsyncClient) -> None:
        csv_bytes = _make_csv_bytes(
            {"company_name": "Acme Corp", "domain": "acme.com", "country": "US", "source": "gmt"}
        )
        with patch("src.api.routers.leads.ingest_lead_file") as mock_task:
            mock_task.delay = MagicMock()
            await async_client.post(
                "/api/v1/leads/upload",
                files={"file": ("leads.csv", csv_bytes, "text/csv")},
            )
        mock_task.delay.assert_called_once()

    async def test_missing_company_name_column_returns_422(self, async_client: AsyncClient) -> None:
        csv_bytes = b"domain,country,source\nacme.com,US,gmt\n"
        with patch("src.api.routers.leads.ingest_lead_file") as mock_task:
            mock_task.delay = MagicMock()
            response = await async_client.post(
                "/api/v1/leads/upload",
                files={"file": ("leads.csv", csv_bytes, "text/csv")},
            )
        assert response.status_code == 422
        assert "company_name" in response.json()["error"]

    async def test_batch_size_exceeded_returns_422(self, async_client: AsyncClient) -> None:
        rows = [{"company_name": f"Co{i}", "domain": f"co{i}.com", "country": "US", "source": "gmt"}
                for i in range(501)]
        csv_bytes = _make_csv_bytes(*rows)
        with patch("src.api.routers.leads.ingest_lead_file") as mock_task:
            mock_task.delay = MagicMock()
            response = await async_client.post(
                "/api/v1/leads/upload",
                files={"file": ("leads.csv", csv_bytes, "text/csv")},
            )
        assert response.status_code == 422
        assert "501" in response.json()["error"]

    async def test_task_not_dispatched_on_validation_failure(self, async_client: AsyncClient) -> None:
        csv_bytes = b"domain,country,source\nacme.com,US,gmt\n"
        with patch("src.api.routers.leads.ingest_lead_file") as mock_task:
            mock_task.delay = MagicMock()
            await async_client.post(
                "/api/v1/leads/upload",
                files={"file": ("leads.csv", csv_bytes, "text/csv")},
            )
        mock_task.delay.assert_not_called()


class TestJobStatusEndpoint:
    async def test_processing_job_returns_200(self, async_client: AsyncClient) -> None:
        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id, "status": "processing",
            "created": 0, "skipped_duplicates": 0, "skipped_invalid": 0, "errors": 0,
        }
        with patch("src.api.routers.leads.get_job_status", AsyncMock(return_value=job_data)):
            response = await async_client.get(f"/api/v1/leads/jobs/{job_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "processing"
        assert body["job_id"] == job_id

    async def test_completed_job_has_all_counts(self, async_client: AsyncClient) -> None:
        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id, "status": "completed",
            "created": 80, "skipped_duplicates": 15, "skipped_invalid": 5, "errors": 0,
        }
        with patch("src.api.routers.leads.get_job_status", AsyncMock(return_value=job_data)):
            response = await async_client.get(f"/api/v1/leads/jobs/{job_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["created"] == 80
        assert body["skipped_duplicates"] == 15
        assert body["skipped_invalid"] == 5

    async def test_unknown_job_id_returns_404(self, async_client: AsyncClient) -> None:
        with patch("src.api.routers.leads.get_job_status", AsyncMock(return_value=None)):
            response = await async_client.get(f"/api/v1/leads/jobs/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_failed_job_has_error_message(self, async_client: AsyncClient) -> None:
        job_id = str(uuid.uuid4())
        job_data = {
            "job_id": job_id, "status": "failed",
            "created": 0, "skipped_duplicates": 0, "skipped_invalid": 0, "errors": 1,
            "error": "Database connection failed after 3 retries",
        }
        with patch("src.api.routers.leads.get_job_status", AsyncMock(return_value=job_data)):
            response = await async_client.get(f"/api/v1/leads/jobs/{job_id}")
        assert response.status_code == 200
        assert "Database" in response.json()["error"]
