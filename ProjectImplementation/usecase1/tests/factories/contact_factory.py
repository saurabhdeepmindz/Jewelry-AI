"""factory_boy factories for Contact domain objects.

Used in unit and integration tests.
SQLAlchemyModelFactory variants require a session injected via:
    ContactORMFactory._meta.sqlalchemy_session = session
"""
from datetime import UTC, datetime
from uuid import uuid4

import factory

from src.db.models.contact import Contact
from src.domain.contact import ContactCreate, EnrichmentSource


class ContactCreateFactory(factory.Factory):
    """Build ContactCreate DTOs for service-layer tests (no DB required)."""

    class Meta:
        model = ContactCreate

    lead_id = factory.LazyFunction(uuid4)
    full_name = factory.Sequence(lambda n: f"Sarah Mitchell {n:04d}")
    title = factory.Iterator(["Head Buyer", "COO", "Director of Procurement", "Buyer"])
    email = factory.Sequence(lambda n: f"contact{n:04d}@pristine.example.com")
    email_verified = False
    phone = factory.Sequence(lambda n: f"+1-212-555-{n:04d}")
    linkedin_url = factory.LazyAttribute(
        lambda o: f"https://linkedin.com/in/test-{o.email.split('@')[0]}"
    )
    enrichment_source = EnrichmentSource.apollo


class ContactORMFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Build Contact ORM rows for integration tests (requires DB session)."""

    class Meta:
        model = Contact
        sqlalchemy_session = None  # must be set per-test
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid4)
    lead_id = factory.LazyFunction(uuid4)
    full_name = factory.Sequence(lambda n: f"Sarah Mitchell {n:04d}")
    title = factory.Iterator(["Head Buyer", "COO", "Director of Procurement"])
    email = factory.Sequence(lambda n: f"contact{n:04d}@pristine.example.com")
    email_verified = False
    phone = None
    linkedin_url = None
    enrichment_source = "apollo"
    enriched_at = factory.LazyFunction(lambda: datetime.now(UTC))
    is_deleted = False
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))
