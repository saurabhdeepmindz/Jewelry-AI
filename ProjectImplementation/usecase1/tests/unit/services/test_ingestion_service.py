"""Unit tests for src/services/ingestion_service.py.

TDD: All external dependencies (DB session, repository) are mocked.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.exceptions import ValidationException
from src.services.ingestion_service import MAX_BATCH_SIZE, ingest_csv


def _make_csv(*rows: dict) -> str:
    """Build a CSV string from a list of row dicts."""
    if not rows:
        return "company_name,domain,country,source\n"
    headers = list(rows[0].keys())
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(row.get(h, "")) for h in headers))
    return "\n".join(lines) + "\n"


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def mock_repo_no_duplicate() -> MagicMock:
    """Repository that finds no existing domain — all leads are new."""
    repo = MagicMock()
    repo.get_by_domain = AsyncMock(return_value=None)
    repo.create = AsyncMock(return_value=MagicMock())
    return repo


@pytest.fixture
def mock_repo_with_duplicate() -> MagicMock:
    """Repository that always finds an existing lead — all are duplicates."""
    repo = MagicMock()
    repo.get_by_domain = AsyncMock(return_value=MagicMock())  # existing lead
    repo.create = AsyncMock(return_value=MagicMock())
    return repo


class TestCSVValidation:
    async def test_missing_company_name_column_raises(self, mock_session: AsyncMock) -> None:
        csv = "domain,country,source\nacme.com,US,gmt\n"
        with pytest.raises(ValidationException, match="Missing required column: company_name"):
            await ingest_csv(mock_session, csv)

    async def test_batch_size_limit_enforced(self, mock_session: AsyncMock) -> None:
        rows = [{"company_name": f"Co{i}", "domain": f"co{i}.com", "country": "US", "source": "gmt"}
                for i in range(MAX_BATCH_SIZE + 1)]
        csv = _make_csv(*rows)
        with pytest.raises(ValidationException, match=f"Batch size {MAX_BATCH_SIZE + 1} exceeds maximum {MAX_BATCH_SIZE}"):
            await ingest_csv(mock_session, csv)

    async def test_empty_csv_returns_zero_created(self, mock_session: AsyncMock) -> None:
        csv = "company_name,domain,country,source\n"
        with patch("src.services.ingestion_service.LeadRepository") as MockRepo:
            MockRepo.return_value.get_by_domain = AsyncMock(return_value=None)
            MockRepo.return_value.create = AsyncMock(return_value=MagicMock())
            result = await ingest_csv(mock_session, csv)
        assert result.created == 0


class TestLeadCreation:
    async def test_valid_row_creates_lead(self, mock_session: AsyncMock) -> None:
        csv = _make_csv({"company_name": "Acme Corp", "domain": "acme.com", "country": "US", "source": "gmt"})
        with patch("src.services.ingestion_service.LeadRepository") as MockRepo:
            MockRepo.return_value.get_by_domain = AsyncMock(return_value=None)
            MockRepo.return_value.create = AsyncMock(return_value=MagicMock())
            result = await ingest_csv(mock_session, csv)
        assert result.created == 1
        assert result.skipped_duplicates == 0
        assert result.skipped_invalid == 0

    async def test_multiple_valid_rows_all_created(self, mock_session: AsyncMock) -> None:
        csv = _make_csv(
            {"company_name": "Acme Corp", "domain": "acme.com", "country": "US", "source": "gmt"},
            {"company_name": "Beta Corp", "domain": "beta.com", "country": "UK", "source": "manual"},
        )
        with patch("src.services.ingestion_service.LeadRepository") as MockRepo:
            MockRepo.return_value.get_by_domain = AsyncMock(return_value=None)
            MockRepo.return_value.create = AsyncMock(return_value=MagicMock())
            result = await ingest_csv(mock_session, csv)
        assert result.created == 2

    async def test_null_domain_skips_deduplication_check(self, mock_session: AsyncMock) -> None:
        csv = _make_csv({"company_name": "No Domain Corp", "domain": "", "country": "US", "source": "manual"})
        with patch("src.services.ingestion_service.LeadRepository") as MockRepo:
            MockRepo.return_value.get_by_domain = AsyncMock(return_value=None)
            MockRepo.return_value.create = AsyncMock(return_value=MagicMock())
            result = await ingest_csv(mock_session, csv)
        # get_by_domain should NOT have been called (domain is None)
        MockRepo.return_value.get_by_domain.assert_not_called()
        assert result.created == 1


class TestDeduplication:
    async def test_duplicate_domain_skipped(self, mock_session: AsyncMock) -> None:
        csv = _make_csv({"company_name": "Acme Corp", "domain": "acme.com", "country": "US", "source": "gmt"})
        with patch("src.services.ingestion_service.LeadRepository") as MockRepo:
            MockRepo.return_value.get_by_domain = AsyncMock(return_value=MagicMock())  # existing
            MockRepo.return_value.create = AsyncMock(return_value=MagicMock())
            result = await ingest_csv(mock_session, csv)
        assert result.skipped_duplicates == 1
        assert result.created == 0
        MockRepo.return_value.create.assert_not_called()

    async def test_mixed_new_and_duplicate(self, mock_session: AsyncMock) -> None:
        csv = _make_csv(
            {"company_name": "New Corp", "domain": "new.com", "country": "US", "source": "gmt"},
            {"company_name": "Dupe Corp", "domain": "dupe.com", "country": "US", "source": "gmt"},
        )
        existing_lead = MagicMock()

        async def _get_by_domain(domain: str):
            return existing_lead if domain == "dupe.com" else None

        with patch("src.services.ingestion_service.LeadRepository") as MockRepo:
            MockRepo.return_value.get_by_domain = AsyncMock(side_effect=_get_by_domain)
            MockRepo.return_value.create = AsyncMock(return_value=MagicMock())
            result = await ingest_csv(mock_session, csv)
        assert result.created == 1
        assert result.skipped_duplicates == 1


class TestInvalidRows:
    async def test_missing_company_name_value_skipped(self, mock_session: AsyncMock) -> None:
        csv = _make_csv(
            {"company_name": "", "domain": "acme.com", "country": "US", "source": "gmt"},
        )
        with patch("src.services.ingestion_service.LeadRepository") as MockRepo:
            MockRepo.return_value.get_by_domain = AsyncMock(return_value=None)
            MockRepo.return_value.create = AsyncMock(return_value=MagicMock())
            result = await ingest_csv(mock_session, csv)
        assert result.skipped_invalid == 1
        assert result.created == 0

    async def test_invalid_source_skipped(self, mock_session: AsyncMock) -> None:
        csv = _make_csv({"company_name": "Acme Corp", "domain": "acme.com", "country": "US", "source": "UNKNOWN"})
        with patch("src.services.ingestion_service.LeadRepository") as MockRepo:
            MockRepo.return_value.get_by_domain = AsyncMock(return_value=None)
            MockRepo.return_value.create = AsyncMock(return_value=MagicMock())
            result = await ingest_csv(mock_session, csv)
        assert result.skipped_invalid == 1

    async def test_100_row_mixed_csv_correct_counts(self, mock_session: AsyncMock) -> None:
        """80 new, 15 duplicate, 5 missing company_name."""
        new_rows = [
            {"company_name": f"Co{i}", "domain": f"co{i}.com", "country": "US", "source": "gmt"}
            for i in range(80)
        ]
        dupe_rows = [
            {"company_name": f"Dupe{i}", "domain": f"dupe{i}.com", "country": "US", "source": "gmt"}
            for i in range(15)
        ]
        invalid_rows = [
            {"company_name": "", "domain": f"inv{i}.com", "country": "US", "source": "gmt"}
            for i in range(5)
        ]
        csv = _make_csv(*(new_rows + dupe_rows + invalid_rows))

        dupe_domains = {f"dupe{i}.com" for i in range(15)}

        async def _get_by_domain(domain: str):
            return MagicMock() if domain in dupe_domains else None

        with patch("src.services.ingestion_service.LeadRepository") as MockRepo:
            MockRepo.return_value.get_by_domain = AsyncMock(side_effect=_get_by_domain)
            MockRepo.return_value.create = AsyncMock(return_value=MagicMock())
            result = await ingest_csv(mock_session, csv)

        assert result.created == 80
        assert result.skipped_duplicates == 15
        assert result.skipped_invalid == 5
