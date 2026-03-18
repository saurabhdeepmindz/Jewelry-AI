"""Lead ingestion service.

Parses a CSV string, validates structure and batch size, then creates
Lead records while deduplicating by domain.

Called by the Celery ingest_lead_file task.
"""
import csv
import io
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ValidationException
from src.core.logging import get_logger
from src.domain.lead import LeadRow, LeadSource
from src.repositories.lead_repository import LeadRepository

logger = get_logger(__name__)

REQUIRED_COLUMNS = {"company_name"}
VALID_SOURCES = {s.value for s in LeadSource}
MAX_BATCH_SIZE = 500


@dataclass
class IngestionResult:
    created: int = 0
    skipped_duplicates: int = 0
    skipped_invalid: int = 0
    errors: int = 0


async def ingest_csv(session: AsyncSession, csv_content: str) -> IngestionResult:
    """Parse csv_content and persist new Lead rows; returns per-category counts.

    Raises ValidationException for missing required columns or batch size exceeded.
    Invalid rows (bad source, empty company_name) are counted as skipped_invalid.
    Duplicate domains (active lead exists) are counted as skipped_duplicates.
    """
    reader = csv.DictReader(io.StringIO(csv_content))

    if not reader.fieldnames or "company_name" not in reader.fieldnames:
        raise ValidationException("Missing required column: company_name")

    rows = list(reader)

    if len(rows) > MAX_BATCH_SIZE:
        raise ValidationException(
            f"Batch size {len(rows)} exceeds maximum {MAX_BATCH_SIZE}"
        )

    repo = LeadRepository(session)
    result = IngestionResult()

    for row in rows:
        company_name = (row.get("company_name") or "").strip()
        if not company_name:
            result.skipped_invalid += 1
            continue

        source_raw = (row.get("source") or "").strip().lower()
        if source_raw not in VALID_SOURCES:
            result.skipped_invalid += 1
            continue

        domain = (row.get("domain") or "").strip() or None
        country = (row.get("country") or "").strip() or None

        # Deduplication — only for non-null domains
        if domain is not None:
            existing = await repo.get_by_domain(domain)
            if existing is not None:
                result.skipped_duplicates += 1
                continue

        lead_row = LeadRow(
            company_name=company_name,
            domain=domain,
            country=country,
            source=LeadSource(source_raw),
        )

        try:
            await repo.create(lead_row)
            result.created += 1
        except Exception as exc:
            logger.error("Failed to create lead for domain=%s: %s", domain, exc)
            result.errors += 1

    return result
