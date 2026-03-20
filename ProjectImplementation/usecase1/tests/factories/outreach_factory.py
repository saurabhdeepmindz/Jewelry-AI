"""factory_boy factories for OutreachMessage test fixtures.

Used in unit and integration tests.
SQLAlchemyModelFactory variants require a session injected via:
    OutreachMessageORMFactory._meta.sqlalchemy_session = session
"""
from datetime import UTC, datetime
from uuid import uuid4

import factory

from src.db.models.outreach import OutreachMessage
from src.domain.outreach import OutreachCreate, OutreachChannel


class OutreachCreateFactory(factory.Factory):
    """Build OutreachCreate DTOs for service-layer tests (no DB required)."""

    class Meta:
        model = OutreachCreate

    lead_id = factory.LazyFunction(uuid4)
    contact_id = factory.LazyFunction(uuid4)
    channel = OutreachChannel.email
    subject = factory.Sequence(lambda n: f"Test Subject {n:04d}")
    body = factory.Sequence(lambda n: f"<p>Test email body {n:04d}</p>")
    sequence_step = 1


class OutreachMessageORMFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Build OutreachMessage ORM rows for integration tests (requires DB session)."""

    class Meta:
        model = OutreachMessage
        sqlalchemy_session = None  # must be set per-test: OutreachMessageORMFactory._meta.sqlalchemy_session = session
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(uuid4)
    lead_id = factory.LazyFunction(uuid4)
    contact_id = factory.LazyFunction(uuid4)
    channel = "email"
    subject = factory.Sequence(lambda n: f"Test Subject {n:04d}")
    body = factory.Sequence(lambda n: f"<p>Test email body {n:04d}</p>")
    sequence_step = 1
    status = "draft"
    rejection_reason = None
    approved_by = None
    approved_at = None
    sendgrid_message_id = None
    sent_at = None
    opened_at = None
    clicked_at = None
    replied_at = None
    bounced_at = None
    is_deleted = False
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))
    updated_at = factory.LazyFunction(lambda: datetime.now(UTC))
