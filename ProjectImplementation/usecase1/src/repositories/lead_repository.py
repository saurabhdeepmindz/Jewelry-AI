"""Repository for Lead ORM operations.

Encapsulates all SQLAlchemy queries for the leads table.
Business logic lives in src/services/; this layer handles storage only.
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.lead import Lead
from src.domain.lead import LeadRow, LeadStatus, MatchStatus


class LeadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_domain(self, domain: str) -> Lead | None:
        """Return the active (non-deleted) lead matching domain, or None."""
        result = await self._session.execute(
            select(Lead).where(Lead.domain == domain, Lead.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def create(self, row: LeadRow) -> Lead:
        """Persist a new Lead from a parsed CSV row; flushes to populate id."""
        lead = Lead(
            company_name=row.company_name,
            domain=row.domain,
            country=row.country,
            source=row.source.value,
            status=LeadStatus.ingested.value,
            match_status=MatchStatus.pending.value,
        )
        self._session.add(lead)
        await self._session.flush()
        return lead

    async def get_by_id(self, lead_id: UUID) -> Lead | None:
        """Return active lead by primary key, or None."""
        result = await self._session.execute(
            select(Lead).where(Lead.id == lead_id, Lead.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()
