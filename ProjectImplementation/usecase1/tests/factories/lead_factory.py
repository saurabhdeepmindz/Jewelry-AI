"""factory_boy factories for Lead domain objects.

Used in unit and integration tests.
Never import real DB sessions here — factories are pure data builders.

SQLAlchemyModelFactory variants require a session injected via:
    LeadFactory._meta.sqlalchemy_session = session
"""
from datetime import UTC, datetime
from uuid import uuid4

import factory

from src.db.models.lead import Lead
from src.domain.lead import LeadCreate


class LeadCreateFactory(factory.Factory):
    """Build LeadCreate DTOs for service-layer tests (no DB required)."""

    class Meta:
        model = LeadCreate

    company_name = factory.Sequence(lambda n: f"Pristine Jewelers {n:04d}")
    domain = factory.LazyAttribute(
        lambda o: f"{o.company_name.replace(' ', '').lower()}.example.com"
    )
    country = factory.Iterator(["US", "AE", "IN", "UK", "SG"])
    source = "CSV_UPLOAD"


class LeadORMFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Build Lead ORM rows for integration tests (requires DB session)."""

    class Meta:
        model = Lead
        sqlalchemy_session = None  # must be set per-test: LeadORMFactory._meta.sqlalchemy_session = session
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid4)
    company_name = factory.Sequence(lambda n: f"Pristine Jewelers {n:04d}")
    domain = factory.LazyAttribute(
        lambda o: f"{o.company_name.replace(' ', '').lower()}.example.com"
    )
    country = factory.Iterator(["US", "AE", "IN", "UK", "SG"])
    source = "CSV_UPLOAD"
    status = "ingested"
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))
