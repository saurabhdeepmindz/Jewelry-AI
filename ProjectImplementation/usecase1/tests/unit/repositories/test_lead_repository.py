"""Unit tests for src/repositories/lead_repository.py.

DB session is fully mocked — no real database connection required.
Tests verify query construction and data mapping logic.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.lead import LeadRow, LeadSource, LeadStatus, MatchStatus
from src.repositories.lead_repository import LeadRepository


def _make_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


def _make_lead_orm(domain: str = "pristine.example.com") -> MagicMock:
    lead = MagicMock()
    lead.id = uuid.uuid4()
    lead.company_name = "Pristine Diamonds"
    lead.domain = domain
    lead.status = "ingested"
    lead.is_deleted = False
    return lead


def _make_row() -> LeadRow:
    return LeadRow(
        company_name="Pristine Diamonds",
        domain="pristine.example.com",
        country="US",
        source=LeadSource.gmt,
    )


class TestLeadRepositoryGetByDomain:
    @pytest.mark.asyncio
    async def test_returns_lead_when_found(self) -> None:
        session = _make_session()
        lead = _make_lead_orm()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = lead
        session.execute = AsyncMock(return_value=mock_result)

        repo = LeadRepository(session)
        result = await repo.get_by_domain("pristine.example.com")

        assert result is lead
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        session = _make_session()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        repo = LeadRepository(session)
        result = await repo.get_by_domain("unknown.example.com")

        assert result is None


class TestLeadRepositoryCreate:
    @pytest.mark.asyncio
    async def test_creates_and_flushes_lead(self) -> None:
        session = _make_session()
        session.flush = AsyncMock()

        # After add+flush the ORM object is "returned" by identity
        added_objects: list = []
        session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        repo = LeadRepository(session)
        row = _make_row()
        result = await repo.create(row)

        session.add.assert_called_once()
        session.flush.assert_awaited_once()

        # The returned object IS the newly constructed Lead ORM
        assert result is added_objects[0]
        assert result.company_name == "Pristine Diamonds"
        assert result.domain == "pristine.example.com"
        assert result.status == LeadStatus.ingested.value
        assert result.match_status == MatchStatus.pending.value

    @pytest.mark.asyncio
    async def test_sets_source_from_row(self) -> None:
        session = _make_session()
        added_objects: list = []
        session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        repo = LeadRepository(session)
        row = _make_row()
        await repo.create(row)

        created = added_objects[0]
        assert created.source == LeadSource.gmt.value


class TestLeadRepositoryGetById:
    @pytest.mark.asyncio
    async def test_returns_lead_when_found(self) -> None:
        session = _make_session()
        lead = _make_lead_orm()
        lead_id = lead.id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = lead
        session.execute = AsyncMock(return_value=mock_result)

        repo = LeadRepository(session)
        result = await repo.get_by_id(lead_id)

        assert result is lead

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        session = _make_session()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        repo = LeadRepository(session)
        result = await repo.get_by_id(uuid.uuid4())

        assert result is None
