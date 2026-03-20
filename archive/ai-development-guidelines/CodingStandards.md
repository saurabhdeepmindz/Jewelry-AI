# Coding Standards — Jewelry AI Platform

## Python Version

All code targets **Python 3.11+**. Use type hints throughout.

---

## Class Boilerplate Template

Every class MUST follow this structure:

```python
"""
Module: src/services/lead_ingestion_service.py
Description: Service responsible for ingesting and validating leads
             from trade list sources into the Jewelry AI pipeline.
"""

import logging
from typing import Optional
from uuid import UUID

from src.core.exceptions import LeadValidationException, DuplicateLeadException
from src.domain.lead import Lead, LeadStatus
from src.repositories.lead_repository import LeadRepository

# Module-level logger — always use __name__ for proper hierarchy
logger = logging.getLogger(__name__)


class LeadIngestionService:
    """
    Handles ingestion of raw lead data from trade list sources.

    Responsibilities:
        - Validate incoming lead payloads against domain schema
        - Deduplicate against existing leads in the database
        - Persist valid leads and trigger downstream enrichment

    Dependencies:
        - LeadRepository: Data access for lead persistence
    """

    def __init__(self, lead_repository: LeadRepository) -> None:
        """
        Initialize LeadIngestionService with required dependencies.

        Args:
            lead_repository (LeadRepository): Repository for lead persistence operations.
        """
        # Injected dependency — never instantiate repository directly in service
        self._repository = lead_repository

    async def ingest_lead(self, raw_data: dict) -> Lead:
        """
        Validate, deduplicate, and persist a single raw lead.

        Validates the incoming dictionary against the Lead domain model,
        checks for duplicates using email and company name, and persists
        the lead if unique. Logs all outcomes for auditability.

        Args:
            raw_data (dict): Raw lead payload from trade list source.
                             Expected keys: company_name, email, phone, source.

        Returns:
            Lead: The persisted Lead domain object with assigned ID and status.

        Raises:
            LeadValidationException: If raw_data fails schema validation.
            DuplicateLeadException: If lead already exists by email or company.

        Example:
            >>> service = LeadIngestionService(repo)
            >>> lead = await service.ingest_lead({"company_name": "Diamond Co", "email": "buyer@diamond.co"})
        """
        # Validate raw payload before any processing
        validated = self._validate_payload(raw_data)

        # Check for existing lead before inserting
        existing = await self._repository.find_by_email(validated.email)
        if existing:
            logger.warning(
                "Duplicate lead detected, skipping",
                extra={"email": validated.email, "existing_id": str(existing.id)}
            )
            raise DuplicateLeadException(email=validated.email)

        # Persist and return the new lead
        persisted = await self._repository.create(validated)
        logger.info(
            "Lead ingested successfully",
            extra={"lead_id": str(persisted.id), "source": persisted.source}
        )
        return persisted

    def _validate_payload(self, raw_data: dict) -> Lead:
        """
        Validate raw dictionary against the Lead domain model.

        Uses Pydantic validation from the Lead domain model.
        This is a private method — only called internally.

        Args:
            raw_data (dict): Unvalidated input data.

        Returns:
            Lead: A validated, unset-ID Lead object.

        Raises:
            LeadValidationException: If required fields are missing or malformed.
        """
        try:
            return Lead.model_validate(raw_data)
        except Exception as exc:
            # Wrap Pydantic errors in domain-specific exception for consistent handling
            raise LeadValidationException(detail=str(exc)) from exc
```

---

## Method Documentation Standard

Every public method MUST have a docstring following this format:

```python
def method_name(self, param1: Type, param2: Type) -> ReturnType:
    """
    One-line summary of what the method does.

    Longer description if needed. Explain the algorithm, side effects,
    or important behavioral details. Keep it factual, not redundant.

    Args:
        param1 (Type): Description of param1 and its expected values.
        param2 (Type): Description of param2 and its expected values.

    Returns:
        ReturnType: Description of the return value and its structure.

    Raises:
        ExceptionType: When and why this exception is raised.

    Example:
        >>> result = obj.method_name(val1, val2)
    """
```

### Rules
- Private methods (`_method`) require a brief single-line docstring minimum.
- Dunder methods (`__init__`, `__str__`) require docstrings for non-trivial logic.
- No docstrings on one-liners that are self-evident (e.g., `return self._id`).

---

## Single-Line Comment Rules

```python
# BAD: Restates the code — adds zero value
lead_count = len(leads)  # get the count of leads

# GOOD: Explains WHY, not what
lead_count = len(leads)  # cap batch to prevent memory overflow downstream

# BAD: Vague comment
# process data
result = transform(data)

# GOOD: Domain-specific context
# Normalize carat weight to 2 decimal places per GIA standard
carat = round(raw_carat, 2)
```

---

## Naming Conventions

| Construct | Convention | Example |
|---|---|---|
| Module | `snake_case` | `lead_ingestion_service.py` |
| Class | `PascalCase` | `LeadIngestionService` |
| Function / Method | `snake_case` | `ingest_lead()` |
| Variable | `snake_case` | `lead_count` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_BATCH_SIZE = 500` |
| Private attribute | `_snake_case` | `self._repository` |
| Type alias | `PascalCase` | `LeadList = list[Lead]` |
| Pydantic model | `PascalCase` | `LeadCreateRequest` |

---

## Type Hints

All function signatures MUST be fully typed:

```python
# CORRECT
async def find_leads_by_status(self, status: LeadStatus, limit: int = 100) -> list[Lead]:
    ...

# INCORRECT — missing return type and parameter types
async def find_leads_by_status(self, status, limit=100):
    ...
```

Use `Optional[X]` (or `X | None` in Python 3.10+) for nullable values:

```python
async def find_by_email(self, email: str) -> Optional[Lead]:
    ...
```

---

## Immutability Rules

```python
# WRONG: Mutating input
def update_lead_status(lead: Lead, status: LeadStatus) -> None:
    lead.status = status  # mutates the original object

# CORRECT: Return new object
def update_lead_status(lead: Lead, status: LeadStatus) -> Lead:
    return lead.model_copy(update={"status": status})
```

All domain models use `frozen=False` Pydantic models but MUST be treated as immutable — use `.model_copy(update={})` to produce updated versions.

---

## File Size & Organization

- **Max file size**: 800 lines. Split at logical seams when approaching this.
- **Max function size**: 50 lines. Extract helper functions aggressively.
- **Max nesting depth**: 4 levels. Use early returns and guard clauses.

```python
# BAD: Deep nesting
def process(data):
    if data:
        if data.get("leads"):
            for lead in data["leads"]:
                if lead.get("email"):
                    # logic here

# GOOD: Guard clauses
def process(data):
    if not data:
        return
    leads = data.get("leads", [])
    for lead in leads:
        if not lead.get("email"):
            continue
        # logic here
```

---

## Constants & Configuration

```python
# WRONG: Magic numbers / strings inline
if carat_weight > 2.0:
    ...

# CORRECT: Named constants in core/config.py
from src.core.config import settings
if carat_weight > settings.INVENTORY_MATCH_MIN_CARAT:
    ...
```

All configurable values live in `src/core/config.py` using `pydantic-settings`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    DATABASE_URL: str
    APOLLO_API_KEY: str
    OPENAI_API_KEY: str
    INVENTORY_MATCH_MIN_CARAT: float = 0.50
    MAX_BATCH_SIZE: int = 500

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Import Order (isort standard)

```python
# 1. Standard library
import logging
from typing import Optional
from uuid import UUID

# 2. Third-party
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Internal — absolute paths only
from src.core.exceptions import LeadNotFoundException
from src.domain.lead import Lead
from src.services.lead_ingestion_service import LeadIngestionService
```

---

## Error Handling Pattern

```python
async def get_lead(self, lead_id: UUID) -> Lead:
    """
    Retrieve a lead by its unique identifier.

    Args:
        lead_id (UUID): The unique identifier of the lead.

    Returns:
        Lead: The found lead domain object.

    Raises:
        LeadNotFoundException: If no lead exists with the given ID.
    """
    lead = await self._repository.find_by_id(lead_id)
    if not lead:
        # Log before raising — include context for debugging
        logger.warning("Lead not found", extra={"lead_id": str(lead_id)})
        raise LeadNotFoundException(lead_id=lead_id)
    return lead
```

---

## Async Rules

- All I/O operations (DB, HTTP, file) MUST be `async`.
- Never use `time.sleep()` — use `await asyncio.sleep()`.
- Never block the event loop with CPU-heavy operations — offload to Celery tasks.

---

## Tooling

| Tool | Purpose | Config File |
|---|---|---|
| `ruff` | Linting + formatting | `pyproject.toml` |
| `mypy` | Static type checking | `pyproject.toml` |
| `pytest` | Testing | `pyproject.toml` |
| `isort` | Import sorting | `pyproject.toml` |
| `pre-commit` | Enforce on commit | `.pre-commit-config.yaml` |
