"""Unit tests for src/services/enrichment_service.py.

TDD RED phase. All DB/API dependencies are mocked.
Patch paths must match where the names are used (module-level imports in service).
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.exceptions import (
    EnrichmentCreditException,
    IntegrationException,
    NotFoundException,
)
from src.domain.contact import ContactData, EnrichmentSource
from src.services.enrichment_service import enrich_lead


def _make_lead(
    lead_id: uuid.UUID | None = None,
    domain: str | None = "pristinediamonds.example.com",
    status: str = "ingested",
) -> MagicMock:
    lead = MagicMock()
    lead.id = lead_id or uuid.uuid4()
    lead.domain = domain
    lead.status = status
    lead.updated_at = MagicMock()
    return lead


def _make_contact() -> MagicMock:
    contact = MagicMock()
    contact.id = uuid.uuid4()
    contact.lead_id = uuid.uuid4()
    contact.full_name = "Sarah Mitchell"
    contact.title = "Head Buyer"
    contact.email = "sarah@pristine.example.com"
    contact.email_verified = True
    contact.phone = None
    contact.linkedin_url = None
    contact.enrichment_source = "apollo"
    contact.enriched_at = MagicMock()
    contact.is_deleted = False
    contact.created_at = MagicMock()
    contact.updated_at = MagicMock()
    return contact


def _apollo_data() -> ContactData:
    return ContactData(
        full_name="Sarah Mitchell",
        title="Head Buyer",
        email="sarah@pristine.example.com",
        enrichment_source=EnrichmentSource.apollo,
    )


def _hunter_data_email() -> str:
    return "sarah@pristine.example.com"


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    return session


class TestEnrichLeadNotFound:
    @pytest.mark.asyncio
    async def test_raises_not_found_when_lead_missing(
        self, mock_session: AsyncMock
    ) -> None:
        lead_id = uuid.uuid4()

        with patch("src.services.enrichment_service.LeadRepository") as MockLeadRepo, \
             patch("src.services.enrichment_service.ContactRepository") as MockContactRepo:

            MockLeadRepo.return_value.get_by_id = AsyncMock(return_value=None)
            MockContactRepo.return_value.get_active_by_lead_id = AsyncMock(return_value=None)

            with pytest.raises(NotFoundException):
                await enrich_lead(mock_session, lead_id)


class TestEnrichLeadAlreadyEnriched:
    @pytest.mark.asyncio
    async def test_raises_when_active_contact_exists(
        self, mock_session: AsyncMock
    ) -> None:
        lead = _make_lead()

        with patch("src.services.enrichment_service.LeadRepository") as MockLeadRepo, \
             patch("src.services.enrichment_service.ContactRepository") as MockContactRepo:

            MockLeadRepo.return_value.get_by_id = AsyncMock(return_value=lead)
            MockContactRepo.return_value.get_active_by_lead_id = AsyncMock(
                return_value=_make_contact()
            )

            with pytest.raises(EnrichmentCreditException):
                await enrich_lead(mock_session, lead.id)


class TestEnrichLeadApolloSuccess:
    @pytest.mark.asyncio
    async def test_apollo_success_creates_contact_and_updates_status(
        self, mock_session: AsyncMock
    ) -> None:
        lead = _make_lead()
        created_contact = _make_contact()

        with patch("src.services.enrichment_service.LeadRepository") as MockLeadRepo, \
             patch("src.services.enrichment_service.ContactRepository") as MockContactRepo, \
             patch("src.services.enrichment_service.ApolloClient") as MockApollo, \
             patch("src.services.enrichment_service.HunterClient") as MockHunter:

            MockLeadRepo.return_value.get_by_id = AsyncMock(return_value=lead)
            MockContactRepo.return_value.get_active_by_lead_id = AsyncMock(return_value=None)
            MockContactRepo.return_value.create = AsyncMock(return_value=created_contact)

            MockApollo.return_value.enrich = AsyncMock(return_value=_apollo_data())
            MockHunter.return_value.verify_email = AsyncMock(return_value=True)

            result = await enrich_lead(mock_session, lead.id)

        assert result is not None
        assert lead.status == "enriched"
        MockContactRepo.return_value.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_email_verified_set_when_hunter_confirms(
        self, mock_session: AsyncMock
    ) -> None:
        lead = _make_lead()
        created_contact = _make_contact()

        with patch("src.services.enrichment_service.LeadRepository") as MockLeadRepo, \
             patch("src.services.enrichment_service.ContactRepository") as MockContactRepo, \
             patch("src.services.enrichment_service.ApolloClient") as MockApollo, \
             patch("src.services.enrichment_service.HunterClient") as MockHunter:

            MockLeadRepo.return_value.get_by_id = AsyncMock(return_value=lead)
            MockContactRepo.return_value.get_active_by_lead_id = AsyncMock(return_value=None)
            MockContactRepo.return_value.create = AsyncMock(return_value=created_contact)

            MockApollo.return_value.enrich = AsyncMock(return_value=_apollo_data())
            MockHunter.return_value.verify_email = AsyncMock(return_value=True)

            await enrich_lead(mock_session, lead.id)

        call_kwargs = MockContactRepo.return_value.create.call_args[0][0]
        assert call_kwargs.email_verified is True


class TestEnrichLeadApolloFallback:
    @pytest.mark.asyncio
    async def test_falls_back_to_hunter_when_apollo_returns_none(
        self, mock_session: AsyncMock
    ) -> None:
        lead = _make_lead()
        created_contact = _make_contact()

        with patch("src.services.enrichment_service.LeadRepository") as MockLeadRepo, \
             patch("src.services.enrichment_service.ContactRepository") as MockContactRepo, \
             patch("src.services.enrichment_service.ApolloClient") as MockApollo, \
             patch("src.services.enrichment_service.HunterClient") as MockHunter:

            MockLeadRepo.return_value.get_by_id = AsyncMock(return_value=lead)
            MockContactRepo.return_value.get_active_by_lead_id = AsyncMock(return_value=None)
            MockContactRepo.return_value.create = AsyncMock(return_value=created_contact)

            MockApollo.return_value.enrich = AsyncMock(return_value=None)
            MockHunter.return_value.find_email = AsyncMock(
                return_value=_hunter_data_email()
            )
            MockHunter.return_value.verify_email = AsyncMock(return_value=True)

            result = await enrich_lead(mock_session, lead.id)

        assert result is not None
        call_kwargs = MockContactRepo.return_value.create.call_args[0][0]
        assert call_kwargs.enrichment_source == EnrichmentSource.hunter

    @pytest.mark.asyncio
    async def test_raises_when_both_providers_return_nothing(
        self, mock_session: AsyncMock
    ) -> None:
        lead = _make_lead()

        with patch("src.services.enrichment_service.LeadRepository") as MockLeadRepo, \
             patch("src.services.enrichment_service.ContactRepository") as MockContactRepo, \
             patch("src.services.enrichment_service.ApolloClient") as MockApollo, \
             patch("src.services.enrichment_service.HunterClient") as MockHunter:

            MockLeadRepo.return_value.get_by_id = AsyncMock(return_value=lead)
            MockContactRepo.return_value.get_active_by_lead_id = AsyncMock(return_value=None)

            MockApollo.return_value.enrich = AsyncMock(return_value=None)
            MockHunter.return_value.find_email = AsyncMock(return_value=None)

            with pytest.raises(IntegrationException):
                await enrich_lead(mock_session, lead.id)


class TestEnrichLeadNoDomain:
    @pytest.mark.asyncio
    async def test_skips_apollo_when_no_domain(
        self, mock_session: AsyncMock
    ) -> None:
        lead = _make_lead(domain=None)

        with patch("src.services.enrichment_service.LeadRepository") as MockLeadRepo, \
             patch("src.services.enrichment_service.ContactRepository") as MockContactRepo, \
             patch("src.services.enrichment_service.ApolloClient") as MockApollo, \
             patch("src.services.enrichment_service.HunterClient"):

            MockLeadRepo.return_value.get_by_id = AsyncMock(return_value=lead)
            MockContactRepo.return_value.get_active_by_lead_id = AsyncMock(return_value=None)

            # When no domain, both Apollo and Hunter find_email should be skipped
            # → raises IntegrationException
            MockApollo.return_value.enrich = AsyncMock()

            with pytest.raises(IntegrationException):
                await enrich_lead(mock_session, lead.id)

            MockApollo.return_value.enrich.assert_not_awaited()


class TestEnrichLeadHunterVerifyFailure:
    @pytest.mark.asyncio
    async def test_hunter_verify_failure_still_creates_contact_unverified(
        self, mock_session: AsyncMock
    ) -> None:
        lead = _make_lead()
        created_contact = _make_contact()
        created_contact.email_verified = False

        with patch("src.services.enrichment_service.LeadRepository") as MockLeadRepo, \
             patch("src.services.enrichment_service.ContactRepository") as MockContactRepo, \
             patch("src.services.enrichment_service.ApolloClient") as MockApollo, \
             patch("src.services.enrichment_service.HunterClient") as MockHunter:

            MockLeadRepo.return_value.get_by_id = AsyncMock(return_value=lead)
            MockContactRepo.return_value.get_active_by_lead_id = AsyncMock(return_value=None)
            MockContactRepo.return_value.create = AsyncMock(return_value=created_contact)

            MockApollo.return_value.enrich = AsyncMock(return_value=_apollo_data())
            # Hunter throws — enrichment still completes with email_verified=False
            MockHunter.return_value.verify_email = AsyncMock(
                side_effect=IntegrationException("Hunter down")
            )

            result = await enrich_lead(mock_session, lead.id)

        assert result is not None
        call_kwargs = MockContactRepo.return_value.create.call_args[0][0]
        assert call_kwargs.email_verified is False
