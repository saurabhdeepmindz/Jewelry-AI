"""Repository for Contact ORM operations.

Encapsulates all SQLAlchemy queries for the contacts table.
Business logic lives in src/services/; this layer handles storage only.
"""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.contact import Contact
from src.domain.contact import ContactCreate


class ContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_by_lead_id(self, lead_id: UUID) -> Contact | None:
        """Return the active (non-deleted) contact for a lead, or None."""
        result = await self._session.execute(
            select(Contact).where(
                Contact.lead_id == lead_id,
                Contact.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def create(self, data: ContactCreate) -> Contact:
        """Persist a new Contact from enrichment data; flushes to populate id."""
        contact = Contact(
            lead_id=data.lead_id,
            full_name=data.full_name,
            title=data.title,
            email=data.email,
            email_verified=data.email_verified,
            phone=data.phone,
            linkedin_url=data.linkedin_url,
            enrichment_source=data.enrichment_source.value,
            enriched_at=datetime.now(UTC),
        )
        self._session.add(contact)
        await self._session.flush()
        return contact

    async def get_by_id(self, contact_id: UUID) -> Contact | None:
        """Return active contact by primary key, or None."""
        result = await self._session.execute(
            select(Contact).where(
                Contact.id == contact_id,
                Contact.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()
