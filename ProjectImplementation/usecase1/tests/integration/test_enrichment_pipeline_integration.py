"""Integration tests for the contact enrichment pipeline — EPIC-04.

Tests the full stack: HTTP → router → Celery dispatch and
service → DB with real PostgreSQL.
External HTTP calls (Apollo, Hunter) are mocked via respx.

Run: pytest tests/integration/test_enrichment_pipeline_integration.py -v -m integration
"""
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import httpx
import pytest
import respx
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.contact import Contact
from src.db.models.lead import Lead
from src.integrations.apollo_client import APOLLO_PEOPLE_MATCH_URL
from src.integrations.hunter_client import HUNTER_API_BASE


def _insert_lead(
    session: AsyncSession,
    domain: str = "pristine.example.com",
    status: str = "ingested",
) -> Lead:
    lead = Lead(
        id=uuid.uuid4(),
        company_name="Pristine Diamonds",
        domain=domain,
        country="US",
        source="gmt",
        status=status,
        match_status="pending",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.add(lead)
    return lead


@pytest.mark.integration
class TestEnrichmentEndpointIntegration:
    """POST /api/v1/enrichment/{lead_id} — HTTP integration."""

    async def test_trigger_returns_202_with_job_id(
        self, async_client: AsyncClient
    ) -> None:
        lead_id = str(uuid.uuid4())
        with patch("src.api.routers.enrichment.enrich_lead_task") as mock_task:
            mock_task.delay = MagicMock()
            response = await async_client.post(f"/api/v1/enrichment/{lead_id}")

        assert response.status_code == 202
        body = response.json()
        assert body["success"] is True
        assert "job_id" in body["data"]
        uuid.UUID(body["data"]["job_id"])

    async def test_trigger_dispatches_celery_task(
        self, async_client: AsyncClient
    ) -> None:
        lead_id = str(uuid.uuid4())
        with patch("src.api.routers.enrichment.enrich_lead_task") as mock_task:
            mock_task.delay = MagicMock()
            await async_client.post(f"/api/v1/enrichment/{lead_id}")
            mock_task.delay.assert_called_once()

    async def test_batch_trigger_returns_202(
        self, async_client: AsyncClient
    ) -> None:
        lead_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        with patch("src.api.routers.enrichment.enrich_lead_task") as mock_task:
            mock_task.delay = MagicMock()
            response = await async_client.post(
                "/api/v1/enrichment/batch",
                json={"lead_ids": lead_ids},
            )
        assert response.status_code == 202
        body = response.json()
        assert body["data"]["total"] == 2

    async def test_batch_dispatches_one_task_per_lead(
        self, async_client: AsyncClient
    ) -> None:
        lead_ids = [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]
        with patch("src.api.routers.enrichment.enrich_lead_task") as mock_task:
            mock_task.delay = MagicMock()
            await async_client.post(
                "/api/v1/enrichment/batch",
                json={"lead_ids": lead_ids},
            )
        assert mock_task.delay.call_count == 3


@pytest.mark.integration
class TestEnrichmentServiceIntegration:
    """enrich_lead() service with real DB + mocked external HTTP."""

    @respx.mock
    async def test_apollo_success_creates_contact_in_db(
        self, db_session: AsyncSession
    ) -> None:
        from src.services.enrichment_service import enrich_lead

        lead = _insert_lead(db_session)
        await db_session.flush()

        respx.post(APOLLO_PEOPLE_MATCH_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "person": {
                        "name": "Sarah Mitchell",
                        "title": "Head Buyer",
                        "email": "sarah@pristine.example.com",
                        "phone_numbers": [],
                        "linkedin_url": None,
                    }
                },
            )
        )
        respx.get(f"{HUNTER_API_BASE}/email-verifier").mock(
            return_value=httpx.Response(200, json={"data": {"result": "deliverable"}})
        )

        await enrich_lead(db_session, lead.id)
        await db_session.flush()

        # Verify DB state
        db_contact = (
            await db_session.execute(
                select(Contact).where(Contact.lead_id == lead.id)
            )
        ).scalar_one_or_none()

        assert db_contact is not None
        assert db_contact.full_name == "Sarah Mitchell"
        assert db_contact.email == "sarah@pristine.example.com"
        assert db_contact.email_verified is True
        assert db_contact.enrichment_source == "apollo"

        # Lead status updated
        db_lead = (
            await db_session.execute(select(Lead).where(Lead.id == lead.id))
        ).scalar_one()
        assert db_lead.status == "enriched"

    @respx.mock
    async def test_hunter_fallback_creates_contact_when_apollo_fails(
        self, db_session: AsyncSession
    ) -> None:
        from src.services.enrichment_service import enrich_lead

        lead = _insert_lead(db_session)
        await db_session.flush()

        respx.post(APOLLO_PEOPLE_MATCH_URL).mock(
            return_value=httpx.Response(200, json={"person": None})
        )
        respx.get(f"{HUNTER_API_BASE}/email-finder").mock(
            return_value=httpx.Response(
                200, json={"data": {"email": "generic@pristine.example.com"}}
            )
        )
        respx.get(f"{HUNTER_API_BASE}/email-verifier").mock(
            return_value=httpx.Response(200, json={"data": {"result": "deliverable"}})
        )

        await enrich_lead(db_session, lead.id)
        await db_session.flush()

        db_contact = (
            await db_session.execute(
                select(Contact).where(Contact.lead_id == lead.id)
            )
        ).scalar_one_or_none()

        assert db_contact is not None
        assert db_contact.email == "generic@pristine.example.com"
        assert db_contact.enrichment_source == "hunter"

    @respx.mock
    async def test_raises_integration_exception_when_all_providers_fail(
        self, db_session: AsyncSession
    ) -> None:
        from src.core.exceptions import IntegrationException
        from src.services.enrichment_service import enrich_lead

        lead = _insert_lead(db_session)
        await db_session.flush()

        respx.post(APOLLO_PEOPLE_MATCH_URL).mock(
            return_value=httpx.Response(200, json={"person": None})
        )
        respx.get(f"{HUNTER_API_BASE}/email-finder").mock(
            return_value=httpx.Response(404)
        )

        with pytest.raises(IntegrationException):
            await enrich_lead(db_session, lead.id)

    @respx.mock
    async def test_raises_not_found_when_lead_missing(
        self, db_session: AsyncSession
    ) -> None:
        from src.core.exceptions import NotFoundException
        from src.services.enrichment_service import enrich_lead

        with pytest.raises(NotFoundException):
            await enrich_lead(db_session, uuid.uuid4())

    @respx.mock
    async def test_raises_credit_exception_when_already_enriched(
        self, db_session: AsyncSession
    ) -> None:
        from src.core.exceptions import EnrichmentCreditException
        from src.services.enrichment_service import enrich_lead

        lead = _insert_lead(db_session)
        await db_session.flush()

        # Insert existing active contact
        existing = Contact(
            id=uuid.uuid4(),
            lead_id=lead.id,
            email="existing@example.com",
            enrichment_source="apollo",
            is_deleted=False,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(existing)
        await db_session.flush()

        with pytest.raises(EnrichmentCreditException):
            await enrich_lead(db_session, lead.id)
