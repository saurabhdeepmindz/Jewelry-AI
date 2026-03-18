"""Unit tests for src/domain/lead.py — Pydantic domain schemas.

TDD: Define expected shapes before implementing models.
"""
import pytest

from src.domain.lead import IngestionSummary, LeadRow, LeadSource, LeadStatus, MatchStatus


class TestLeadSource:
    def test_valid_sources_exist(self) -> None:
        assert LeadSource.gmt.value == "gmt"
        assert LeadSource.trade_book.value == "trade_book"
        assert LeadSource.rapid_list.value == "rapid_list"
        assert LeadSource.manual.value == "manual"
        assert LeadSource.api.value == "api"

    def test_invalid_source_raises(self) -> None:
        with pytest.raises(ValueError):
            LeadSource("unknown")


class TestLeadStatus:
    def test_ingested_is_initial_status(self) -> None:
        assert LeadStatus.ingested.value == "ingested"

    def test_all_statuses_present(self) -> None:
        values = {s.value for s in LeadStatus}
        assert {"ingested", "enriched", "matched", "eligible", "ineligible", "outreached", "replied", "disqualified"} <= values


class TestMatchStatus:
    def test_pending_is_initial(self) -> None:
        assert MatchStatus.pending.value == "pending"

    def test_all_match_statuses(self) -> None:
        values = {s.value for s in MatchStatus}
        assert {"pending", "matched", "no_match"} == values


class TestLeadRow:
    def test_valid_row_with_all_fields(self) -> None:
        row = LeadRow(company_name="Acme Corp", domain="acme.com", country="US", source=LeadSource.gmt)
        assert row.company_name == "Acme Corp"
        assert row.domain == "acme.com"
        assert row.source == LeadSource.gmt

    def test_domain_and_country_optional(self) -> None:
        row = LeadRow(company_name="Acme Corp", source=LeadSource.manual)
        assert row.domain is None
        assert row.country is None

    def test_source_accepts_string_value(self) -> None:
        row = LeadRow(company_name="Acme Corp", source="trade_book")  # type: ignore[arg-type]
        assert row.source == LeadSource.trade_book


class TestIngestionSummary:
    def test_defaults_to_zero_counts(self) -> None:
        summary = IngestionSummary(job_id="abc-123", status="processing")
        assert summary.created == 0
        assert summary.skipped_duplicates == 0
        assert summary.skipped_invalid == 0
        assert summary.errors == 0
        assert summary.error is None

    def test_completed_summary(self) -> None:
        summary = IngestionSummary(
            job_id="abc-123",
            status="completed",
            created=80,
            skipped_duplicates=15,
            skipped_invalid=5,
            errors=0,
        )
        assert summary.created == 80
        assert summary.status == "completed"

    def test_failed_summary_has_error_message(self) -> None:
        summary = IngestionSummary(
            job_id="abc-123",
            status="failed",
            error="Database connection failed after 3 retries",
        )
        assert summary.status == "failed"
        assert "Database" in summary.error  # type: ignore[operator]
