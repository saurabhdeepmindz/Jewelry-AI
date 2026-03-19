"""Unit tests for src/domain/contact.py.

TDD RED phase — run before implementation exists.
"""
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain.contact import (
    ContactCreate,
    ContactData,
    ContactRead,
    EnrichmentJobStatus,
    EnrichmentSource,
)


class TestEnrichmentSource:
    def test_has_apollo(self) -> None:
        assert EnrichmentSource.apollo.value == "apollo"

    def test_has_hunter(self) -> None:
        assert EnrichmentSource.hunter.value == "hunter"

    def test_has_proxycurl(self) -> None:
        assert EnrichmentSource.proxycurl.value == "proxycurl"

    def test_has_manual(self) -> None:
        assert EnrichmentSource.manual.value == "manual"

    def test_invalid_source_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContactCreate(
                lead_id=uuid4(),
                enrichment_source="linkedin",  # not a valid value
            )


class TestContactData:
    def test_all_fields_optional_except_source(self) -> None:
        data = ContactData(enrichment_source=EnrichmentSource.apollo)
        assert data.full_name is None
        assert data.title is None
        assert data.email is None
        assert data.phone is None
        assert data.linkedin_url is None

    def test_full_contact_data(self) -> None:
        data = ContactData(
            full_name="Sarah Mitchell",
            title="Head Buyer",
            email="s.mitchell@example.com",
            phone="+1-212-555-0101",
            linkedin_url="https://linkedin.com/in/sarahmitchell",
            enrichment_source=EnrichmentSource.apollo,
        )
        assert data.full_name == "Sarah Mitchell"
        assert data.enrichment_source == EnrichmentSource.apollo


class TestContactCreate:
    def test_requires_lead_id(self) -> None:
        with pytest.raises(ValidationError):
            ContactCreate(enrichment_source=EnrichmentSource.apollo)  # type: ignore[call-arg]

    def test_requires_enrichment_source(self) -> None:
        with pytest.raises(ValidationError):
            ContactCreate(lead_id=uuid4())  # type: ignore[call-arg]

    def test_email_verified_defaults_false(self) -> None:
        c = ContactCreate(lead_id=uuid4(), enrichment_source=EnrichmentSource.apollo)
        assert c.email_verified is False

    def test_all_optional_fields_default_none(self) -> None:
        c = ContactCreate(lead_id=uuid4(), enrichment_source=EnrichmentSource.hunter)
        assert c.full_name is None
        assert c.email is None
        assert c.phone is None
        assert c.linkedin_url is None


class TestContactRead:
    def test_from_attributes_enabled(self) -> None:
        # model_config must have from_attributes=True for ORM use
        assert ContactRead.model_config.get("from_attributes") is True


class TestEnrichmentJobStatus:
    def test_defaults(self) -> None:
        status = EnrichmentJobStatus(
            job_id="job-123",
            lead_id="lead-456",
            status="queued",
        )
        assert status.error is None

    def test_failed_status_with_error(self) -> None:
        status = EnrichmentJobStatus(
            job_id="job-123",
            lead_id="lead-456",
            status="failed",
            error="Apollo.io timed out",
        )
        assert status.error == "Apollo.io timed out"
