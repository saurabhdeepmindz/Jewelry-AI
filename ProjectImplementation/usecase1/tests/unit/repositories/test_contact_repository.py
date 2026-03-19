"""Unit tests for src/repositories/contact_repository.py.

DB session is fully mocked — no real database connection required.
Tests verify query construction and data mapping logic.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.contact import ContactCreate, EnrichmentSource
from src.repositories.contact_repository import ContactRepository


def _make_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


def _make_contact_orm() -> MagicMock:
    contact = MagicMock()
    contact.id = uuid.uuid4()
    contact.lead_id = uuid.uuid4()
    contact.full_name = "Sarah Mitchell"
    contact.title = "Head Buyer"
    contact.email = "sarah@pristine.example.com"
    contact.email_verified = True
    contact.phone = None
    contact.linkedin_url = None
    contact.enrichment_source = "apollo"
    contact.is_deleted = False
    return contact


def _make_contact_create(lead_id: uuid.UUID | None = None) -> ContactCreate:
    return ContactCreate(
        lead_id=lead_id or uuid.uuid4(),
        full_name="Sarah Mitchell",
        title="Head Buyer",
        email="sarah@pristine.example.com",
        email_verified=True,
        phone=None,
        linkedin_url=None,
        enrichment_source=EnrichmentSource.apollo,
    )


class TestContactRepositoryGetActiveByLeadId:
    @pytest.mark.asyncio
    async def test_returns_contact_when_active_contact_exists(self) -> None:
        session = _make_session()
        contact = _make_contact_orm()
        lead_id = contact.lead_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = contact
        session.execute = AsyncMock(return_value=mock_result)

        repo = ContactRepository(session)
        result = await repo.get_active_by_lead_id(lead_id)

        assert result is contact
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_returns_none_when_no_active_contact(self) -> None:
        session = _make_session()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        repo = ContactRepository(session)
        result = await repo.get_active_by_lead_id(uuid.uuid4())

        assert result is None


class TestContactRepositoryCreate:
    @pytest.mark.asyncio
    async def test_creates_and_flushes_contact(self) -> None:
        session = _make_session()
        added_objects: list = []
        session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        repo = ContactRepository(session)
        data = _make_contact_create()
        result = await repo.create(data)

        session.add.assert_called_once()
        session.flush.assert_awaited_once()

        assert result is added_objects[0]
        assert result.lead_id == data.lead_id
        assert result.full_name == "Sarah Mitchell"
        assert result.email == "sarah@pristine.example.com"
        assert result.email_verified is True
        assert result.enrichment_source == "apollo"

    @pytest.mark.asyncio
    async def test_enrichment_source_stored_as_string_value(self) -> None:
        session = _make_session()
        added_objects: list = []
        session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        repo = ContactRepository(session)
        data = ContactCreate(
            lead_id=uuid.uuid4(),
            email="h@example.com",
            enrichment_source=EnrichmentSource.hunter,
        )
        await repo.create(data)

        assert added_objects[0].enrichment_source == "hunter"

    @pytest.mark.asyncio
    async def test_enriched_at_is_set_on_create(self) -> None:
        session = _make_session()
        added_objects: list = []
        session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))

        repo = ContactRepository(session)
        data = _make_contact_create()
        await repo.create(data)

        assert added_objects[0].enriched_at is not None


class TestContactRepositoryGetById:
    @pytest.mark.asyncio
    async def test_returns_contact_when_found(self) -> None:
        session = _make_session()
        contact = _make_contact_orm()
        contact_id = contact.id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = contact
        session.execute = AsyncMock(return_value=mock_result)

        repo = ContactRepository(session)
        result = await repo.get_by_id(contact_id)

        assert result is contact

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self) -> None:
        session = _make_session()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        repo = ContactRepository(session)
        result = await repo.get_by_id(uuid.uuid4())

        assert result is None
