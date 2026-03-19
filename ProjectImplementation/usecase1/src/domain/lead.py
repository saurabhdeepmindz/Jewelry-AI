"""Domain models for the Lead entity.

Pure Pydantic schemas — no SQLAlchemy dependency.
These are the canonical shapes used across services, tasks, and routers.
"""
import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LeadStatus(enum.StrEnum):
    ingested = "ingested"
    enriched = "enriched"
    matched = "matched"
    eligible = "eligible"
    ineligible = "ineligible"
    outreached = "outreached"
    replied = "replied"
    disqualified = "disqualified"


class MatchStatus(enum.StrEnum):
    pending = "pending"
    matched = "matched"
    no_match = "no_match"


class LeadSource(enum.StrEnum):
    gmt = "gmt"
    trade_book = "trade_book"
    rapid_list = "rapid_list"
    manual = "manual"
    api = "api"


class LeadRow(BaseModel):
    """A single parsed row from the uploaded CSV."""

    company_name: str
    domain: str | None = None
    country: str | None = None
    source: LeadSource


class IngestionSummary(BaseModel):
    """Summary returned by GET /api/v1/leads/jobs/{job_id}."""

    job_id: str
    status: str  # "processing" | "completed" | "failed"
    created: int = 0
    skipped_duplicates: int = 0
    skipped_invalid: int = 0
    errors: int = 0
    error: str | None = None


class LeadRead(BaseModel):
    """Read model returned from the DB."""

    id: UUID
    company_name: str
    domain: str | None
    country: str | None
    source: LeadSource
    status: LeadStatus
    match_status: MatchStatus
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
