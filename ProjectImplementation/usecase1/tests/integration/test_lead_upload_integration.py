"""Integration tests for lead upload pipeline — EPIC-02.

Tests the full stack: HTTP → router → Celery task dispatch → service → DB.
Requires running PostgreSQL (docker compose up postgres).
Redis is mocked (Celery always_eager + job_store patched).

Run: pytest tests/integration/test_lead_upload_integration.py -v -m integration
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.lead import Lead


def _csv_bytes(*rows: dict) -> bytes:
    if not rows:
        return b"company_name,domain,country,source\n"
    headers = list(rows[0].keys())
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(row.get(h, "")) for h in headers))
    return ("\n".join(lines) + "\n").encode()


VALID_CSV = _csv_bytes(
    {"company_name": "Pristine Diamonds", "domain": "pristine.example.com", "country": "US", "source": "gmt"},
    {"company_name": "Golden Baubles", "domain": "golden.example.com", "country": "AE", "source": "trade_book"},
)

DUPE_CSV = _csv_bytes(
    {"company_name": "Pristine Diamonds", "domain": "pristine.example.com", "country": "US", "source": "gmt"},
    {"company_name": "Pristine Diamonds", "domain": "pristine.example.com", "country": "US", "source": "gmt"},
)


@pytest.mark.integration
class TestLeadUploadEndpointIntegration:
    """POST /api/v1/leads/upload — full HTTP integration."""

    async def test_upload_returns_202_and_job_id(
        self, async_client: AsyncClient
    ) -> None:
        with patch("src.api.routers.leads.ingest_lead_file") as mock_task:
            mock_task.delay = MagicMock()
            response = await async_client.post(
                "/api/v1/leads/upload",
                files={"file": ("leads.csv", VALID_CSV, "text/csv")},
            )

        assert response.status_code == 202
        body = response.json()
        assert "job_id" in body
        uuid.UUID(body["job_id"])  # must be a valid UUID

    async def test_upload_dispatches_celery_task(
        self, async_client: AsyncClient
    ) -> None:
        with patch("src.api.routers.leads.ingest_lead_file") as mock_task:
            mock_task.delay = MagicMock()
            await async_client.post(
                "/api/v1/leads/upload",
                files={"file": ("leads.csv", VALID_CSV, "text/csv")},
            )
            mock_task.delay.assert_called_once()

    async def test_upload_missing_column_returns_422(
        self, async_client: AsyncClient
    ) -> None:
        bad_csv = b"domain,country,source\npristine.example.com,US,gmt\n"
        with patch("src.api.routers.leads.ingest_lead_file") as mock_task:
            mock_task.delay = MagicMock()
            response = await async_client.post(
                "/api/v1/leads/upload",
                files={"file": ("leads.csv", bad_csv, "text/csv")},
            )
        assert response.status_code == 422


@pytest.mark.integration
class TestIngestionServiceIntegration:
    """ingest_csv() service against a real test database."""

    async def test_persists_leads_in_database(
        self, db_session: AsyncSession
    ) -> None:
        from src.services.ingestion_service import ingest_csv

        csv = VALID_CSV.decode()
        result = await ingest_csv(db_session, csv)
        await db_session.flush()

        assert result.created == 2
        assert result.skipped_duplicates == 0

        rows = (await db_session.execute(select(Lead))).scalars().all()
        assert len(rows) == 2
        domains = {r.domain for r in rows}
        assert "pristine.example.com" in domains
        assert "golden.example.com" in domains

    async def test_skips_duplicate_domains(
        self, db_session: AsyncSession
    ) -> None:
        from src.services.ingestion_service import ingest_csv

        # First upload
        await ingest_csv(db_session, VALID_CSV.decode())
        await db_session.flush()

        # Second upload with overlapping domain
        dupe_csv = _csv_bytes(
            {"company_name": "Pristine Copy", "domain": "pristine.example.com", "country": "US", "source": "gmt"},
        ).decode()
        result = await ingest_csv(db_session, dupe_csv)

        assert result.skipped_duplicates == 1
        assert result.created == 0

    async def test_leads_have_ingested_status(
        self, db_session: AsyncSession
    ) -> None:
        from src.services.ingestion_service import ingest_csv

        await ingest_csv(db_session, VALID_CSV.decode())
        await db_session.flush()

        rows = (await db_session.execute(select(Lead))).scalars().all()
        for lead in rows:
            assert lead.status == "ingested"
