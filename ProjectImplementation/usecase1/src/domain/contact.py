"""Domain models for the Contact entity.

Pure Pydantic schemas — no SQLAlchemy dependency.
These are the canonical shapes used across services, tasks, and routers.
"""
import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EnrichmentSource(enum.StrEnum):
    apollo = "apollo"
    hunter = "hunter"
    proxycurl = "proxycurl"
    manual = "manual"


class ContactData(BaseModel):
    """Intermediate model returned by enrichment provider clients.

    Passed from ApolloClient / HunterClient → EnrichmentService.
    Not persisted directly; service maps to ContactCreate before saving.
    """

    full_name: str | None = None
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    enrichment_source: EnrichmentSource


class ContactCreate(BaseModel):
    """Input for creating a new Contact record in the database."""

    lead_id: UUID
    full_name: str | None = None
    title: str | None = None
    email: str | None = None
    email_verified: bool = False
    phone: str | None = None
    linkedin_url: str | None = None
    enrichment_source: EnrichmentSource


class ContactRead(BaseModel):
    """Read model returned from the DB — safe to serialise and return via API."""

    id: UUID
    lead_id: UUID
    full_name: str | None
    title: str | None
    email: str | None
    email_verified: bool
    phone: str | None
    linkedin_url: str | None
    enrichment_source: EnrichmentSource | None
    enriched_at: datetime | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EnrichmentJobStatus(BaseModel):
    """Status payload returned by GET /api/v1/enrichment/jobs/{job_id}."""

    job_id: str
    lead_id: str
    status: str  # queued | processing | completed | failed
    error: str | None = None
