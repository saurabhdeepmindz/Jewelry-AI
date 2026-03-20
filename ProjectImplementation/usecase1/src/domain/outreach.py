"""Domain models for the OutreachMessage entity.

Pure Pydantic schemas — no SQLAlchemy dependency.
These are the canonical shapes used across services, tasks, and routers.
"""
import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OutreachChannel(enum.StrEnum):
    email = "email"
    whatsapp = "whatsapp"
    linkedin = "linkedin"


class OutreachStatus(enum.StrEnum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    sent = "sent"
    opened = "opened"
    clicked = "clicked"
    replied = "replied"
    bounced = "bounced"
    rejected = "rejected"


class OutreachCreate(BaseModel):
    lead_id: UUID
    contact_id: UUID | None = None
    channel: OutreachChannel = OutreachChannel.email
    subject: str | None = None
    body: str
    sequence_step: int = Field(default=1, ge=1, le=10)


class OutreachRead(BaseModel):
    id: UUID
    lead_id: UUID
    contact_id: UUID | None
    channel: OutreachChannel
    subject: str | None
    body: str
    sequence_step: int
    status: OutreachStatus
    rejection_reason: str | None
    approved_by: UUID | None
    approved_at: datetime | None
    sendgrid_message_id: str | None
    sent_at: datetime | None
    opened_at: datetime | None
    clicked_at: datetime | None
    replied_at: datetime | None
    bounced_at: datetime | None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OutreachUpdate(BaseModel):
    subject: str | None = None
    body: str | None = None


class OutreachRejectRequest(BaseModel):
    reason: str


class OutreachListItem(BaseModel):
    id: UUID
    lead_id: UUID
    contact_id: UUID | None
    channel: OutreachChannel
    subject: str | None
    sequence_step: int
    status: OutreachStatus
    sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
