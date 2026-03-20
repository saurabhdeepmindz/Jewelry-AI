"""Repository for OutreachMessage ORM operations.

Encapsulates all SQLAlchemy queries for the outreach_messages table.
Business logic lives in src/services/; this layer handles storage only.
"""
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.outreach import OutreachMessage
from src.domain.outreach import OutreachCreate


class OutreachRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: OutreachCreate) -> OutreachMessage:
        """Persist a new OutreachMessage; flushes to populate id."""
        message = OutreachMessage(
            lead_id=data.lead_id,
            contact_id=data.contact_id,
            channel=data.channel.value,
            subject=data.subject,
            body=data.body,
            sequence_step=data.sequence_step,
            status="draft",
        )
        self._session.add(message)
        await self._session.flush()
        return message

    async def get_by_id(self, message_id: UUID) -> OutreachMessage | None:
        """Return active (non-deleted) outreach message by primary key, or None."""
        result = await self._session.execute(
            select(OutreachMessage).where(
                OutreachMessage.id == message_id,
                OutreachMessage.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_lead(self, lead_id: UUID) -> list[OutreachMessage]:
        """Return all active outreach messages for a lead, ordered by sequence_step."""
        result = await self._session.execute(
            select(OutreachMessage)
            .where(
                OutreachMessage.lead_id == lead_id,
                OutreachMessage.is_deleted.is_(False),
            )
            .order_by(OutreachMessage.sequence_step, OutreachMessage.created_at)
        )
        return list(result.scalars().all())

    async def list_by_status(
        self,
        status: str,
        page: int = 1,
        page_size: int = 20,
    ) -> list[OutreachMessage]:
        """Return paginated active outreach messages filtered by status."""
        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(OutreachMessage)
            .where(
                OutreachMessage.status == status,
                OutreachMessage.is_deleted.is_(False),
            )
            .order_by(OutreachMessage.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        message_id: UUID,
        status: str,
        **kwargs: Any,
    ) -> OutreachMessage | None:
        """Update status and any additional fields (sent_at, opened_at, etc.).

        Returns the updated message, or None if not found.
        """
        message = await self.get_by_id(message_id)
        if message is None:
            return None

        message.status = status
        message.updated_at = datetime.now(UTC)

        for field, value in kwargs.items():
            if hasattr(message, field):
                setattr(message, field, value)

        await self._session.flush()
        return message

    async def soft_delete(self, message_id: UUID) -> bool:
        """Soft-delete an outreach message. Returns True if found and deleted."""
        message = await self.get_by_id(message_id)
        if message is None:
            return False

        message.is_deleted = True
        message.updated_at = datetime.now(UTC)
        await self._session.flush()
        return True

    async def get_by_sendgrid_message_id(
        self, sendgrid_message_id: str
    ) -> OutreachMessage | None:
        """Return active outreach message by SendGrid message ID, or None."""
        result = await self._session.execute(
            select(OutreachMessage).where(
                OutreachMessage.sendgrid_message_id == sendgrid_message_id,
                OutreachMessage.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        lead_id: UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[OutreachMessage]:
        """Return paginated active outreach messages with optional filters."""
        offset = (page - 1) * page_size
        query = select(OutreachMessage).where(
            OutreachMessage.is_deleted.is_(False)
        )

        if lead_id is not None:
            query = query.where(OutreachMessage.lead_id == lead_id)

        if status is not None:
            query = query.where(OutreachMessage.status == status)

        query = query.order_by(OutreachMessage.created_at.desc()).offset(offset).limit(page_size)

        result = await self._session.execute(query)
        return list(result.scalars().all())
