# Coding Standards — Jewelry AI Lead Automation Platform

**Version:** 1.0
**Status:** Approved
**Stage:** 4.2 — Design Patterns
**Created:** 2026-03-18
**Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x async, LangChain, Celery

---

## Overview

This document defines the project-specific coding standards for the Jewelry AI platform. These rules extend and specialize the generic Python standards in `best-practices_rule_set_code/CodingStandards-python.md`.

**Read the generic document first.** This document only defines what is different or more specific for this project.

---

## 1. File and Module Size Limits

| Artifact | Maximum Lines | Action When Exceeded |
|----------|--------------|----------------------|
| Any `.py` file | 800 | Extract to sub-module |
| Service class | 400 | Split by responsibility |
| Router file | 300 | Split by resource group |
| Repository class | 300 | Extract query helpers |
| LangGraph node function | 80 | Extract helpers |
| Celery task function | 100 | Delegate to service |
| Pydantic model file | 250 | Split by domain entity |

---

## 2. Naming Conventions

### General Rules

| Artifact | Convention | Example |
|----------|-----------|---------|
| Module / package | `snake_case` | `lead_ingestion_service.py` |
| Class | `PascalCase` | `LeadIngestionService` |
| Function / method | `snake_case` | `ingest_lead_file()` |
| Variable | `snake_case` | `lead_score` |
| Constant | `SCREAMING_SNAKE_CASE` | `MAX_ENRICHMENT_RETRIES = 3` |
| Pydantic model | `PascalCase` | `LeadCreateRequest` |
| Enum class | `PascalCase` | `LeadStatus` |
| Enum member | `SCREAMING_SNAKE_CASE` | `LeadStatus.NOT_ELIGIBLE` |
| ORM model | `PascalCase` + `ORM` suffix | `LeadORM` |
| Repository | `PascalCase` + `Repository` suffix | `LeadRepository` |
| Service | `PascalCase` + `Service` suffix | `EnrichmentService` |
| Celery task | `snake_case` (module-level) | `ingest_lead_file` |
| LangGraph node | `snake_case` + `_node` suffix | `match_inventory_node` |
| FastAPI router | `snake_case` + `_router` suffix | `leads_router` |

### Domain-Specific Names

These names are fixed across the entire codebase. Do not create synonyms or abbreviations.

| Concept | Canonical Name | Do NOT Use |
|---------|---------------|------------|
| Lead company prospect | `lead` | `prospect`, `customer`, `buyer_company` |
| Inventory item | `inventory` | `item`, `product`, `stock` |
| Enriched buyer contact | `contact` | `person`, `employee`, `buyer` |
| AI-generated message | `outreach_message` | `email`, `message`, `draft` |
| Audit event | `crm_activity` | `event`, `log`, `audit_log` |
| Lead scoring model output | `score` (float) + `score_tier` (str) | `rating`, `rank`, `grade` |
| Eligibility flag | `is_eligible` (bool) | `eligible`, `qualified`, `match_found` |
| Soft delete flag | `is_deleted` (bool) | `deleted`, `archived`, `removed` |

---

## 3. Class Boilerplate Standards

### 3.1 Pydantic Domain Model

```python
# src/domain/models.py
from datetime import datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class LeadStatus(str, Enum):
    INGESTED = "ingested"
    MATCHED = "matched"
    ENRICHED = "enriched"
    SCORED = "scored"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    CLOSED = "closed"


class ScoreTier(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Lead(BaseModel):
    """
    Domain model for a jewelry buyer prospect.

    This is a Pydantic v2 model — used for in-memory business logic,
    service return types, and API response serialization.
    It is NOT the SQLAlchemy ORM model (see src/db/models.py → LeadORM).

    Rules:
        - model_config = {"frozen": True} enforces immutability
        - Use model_copy(update={...}) to derive modified instances
        - Never set fields directly after construction
    """

    model_config = {"frozen": True}

    id: UUID
    company_name: str
    domain: str | None = None
    country: str | None = None
    status: LeadStatus = LeadStatus.INGESTED
    score: float | None = Field(default=None, ge=0.0, le=100.0)
    score_tier: ScoreTier | None = None
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime

    @field_validator("company_name")
    @classmethod
    def company_name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("company_name must not be blank")
        return v.strip()

    @field_validator("score")
    @classmethod
    def score_precision(cls, v: float | None) -> float | None:
        """Enforce 1 decimal place precision on scores."""
        if v is not None:
            return round(v, 1)
        return v

    @model_validator(mode="after")
    def score_tier_consistency(self) -> "Lead":
        """score_tier must be set if and only if score is set."""
        if self.score is not None and self.score_tier is None:
            raise ValueError("score_tier is required when score is set")
        if self.score is None and self.score_tier is not None:
            raise ValueError("score_tier must be None when score is None")
        return self
```

### 3.2 SQLAlchemy ORM Model

```python
# src/db/models.py
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class LeadORM(Base):
    """
    SQLAlchemy ORM model for the `leads` table.

    Rules:
        - ORM models are NEVER used in service/API layers directly
        - Services receive LeadORM from repositories; map to Lead domain model
        - All domain tables have: id (UUID PK), is_deleted, created_at, updated_at
        - __repr__ must never include hashed_password or encrypted fields
    """

    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True)
    source = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="ingested")
    match_status = Column(String(50), nullable=False, default="pending")
    score = Column(Float, nullable=True)
    score_tier = Column(String(20), nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    contacts = relationship("ContactORM", back_populates="lead", lazy="selectin")
    outreach_messages = relationship("OutreachMessageORM", back_populates="lead")

    def __repr__(self) -> str:
        return f"<LeadORM id={self.id} company={self.company_name!r} status={self.status!r}>"
```

### 3.3 FastAPI Router

```python
# src/api/routers/leads.py
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.dependencies import get_lead_repository
from src.api.schemas import LeadResponse, PageResponse, APIResponse
from src.core.exceptions import LeadNotFoundError
from src.repositories.lead_repository import LeadRepository

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get(
    "/{lead_id}",
    response_model=APIResponse[LeadResponse],
    summary="Get a lead by ID",
    responses={
        404: {"description": "Lead not found"},
        401: {"description": "Authentication required"},
    },
)
async def get_lead(
    lead_id: UUID,
    repo: Annotated[LeadRepository, Depends(get_lead_repository)],
) -> APIResponse[LeadResponse]:
    """
    Retrieve a single lead by UUID.

    Rules:
        - Returns 404 if lead does not exist or is soft-deleted
        - Role check enforced by JWT middleware (see src/core/auth.py)
        - rep role can only access leads assigned to them (enforced in repo)
    """
    lead_orm = await repo.get_by_id(lead_id)
    if lead_orm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return APIResponse(success=True, data=LeadResponse.model_validate(lead_orm))
```

### 3.4 Service Class

```python
# src/services/lead_ingestion_service.py
from src.core.logging import get_logger
from src.domain.models import Lead
from src.repositories.lead_repository import LeadRepository
from src.repositories.crm_repository import CRMRepository
from src.services.base import BaseService

logger = get_logger(__name__)


class LeadIngestionService(BaseService):
    """
    Ingests raw lead data from CSV/API sources.

    Responsibilities:
        - Deduplicate by email domain
        - Validate required fields
        - Create Lead records
        - Emit lead_ingested CRM activity

    Rules:
        - Never re-create a lead that already exists for the same domain
        - Source field must be one of: gmt | trade_book | rapid_list | manual | api
        - Batch max size: 500 leads per file (enforced here, not in router)
    """

    VALID_SOURCES = frozenset({"gmt", "trade_book", "rapid_list", "manual", "api"})
    BATCH_MAX = 500

    def __init__(
        self,
        lead_repo: LeadRepository,
        crm_repo: CRMRepository,
    ) -> None:
        super().__init__(crm_repo=crm_repo)
        self._lead_repo = lead_repo

    def validate_input(self, input_data: dict) -> None:
        source = input_data.get("source", "")
        if source not in self.VALID_SOURCES:
            raise ValueError(f"Invalid source '{source}'. Must be one of: {self.VALID_SOURCES}")

    async def execute(self, input_data: dict) -> dict:
        rows = input_data["rows"]
        if len(rows) > self.BATCH_MAX:
            raise ValueError(f"Batch size {len(rows)} exceeds maximum {self.BATCH_MAX}")

        created_count = 0
        skipped_count = 0

        for row in rows:
            domain = row.get("domain")
            existing = await self._lead_repo.get_by_domain(domain) if domain else None
            if existing:
                skipped_count += 1
                logger.debug("Skipping duplicate domain", domain=domain)
                continue

            # Build ORM model — map from raw dict
            from src.db.models import LeadORM
            lead_orm = LeadORM(
                company_name=row["company_name"],
                domain=domain,
                country=row.get("country"),
                source=input_data["source"],
            )
            await self._lead_repo.create(lead_orm)
            created_count += 1

        logger.info("Lead ingestion complete", created=created_count, skipped=skipped_count)
        return {"created": created_count, "skipped": skipped_count}
```

---

## 4. Docstring Standard

All public classes, methods, and functions use **Google-style** docstrings.

```python
async def enrich_lead(
    self,
    lead_id: str,
    domain: str,
    company_name: str,
) -> list[Contact]:
    """
    Enrich a lead's buyer contacts using the configured provider cascade.

    Checks Redis cache before calling any external API. Returns cached
    result immediately if found (TTL = 7 days). On cache miss, tries
    providers in order: Apollo → Hunter → Proxycurl.

    Args:
        lead_id: UUID string of the lead being enriched. Used for logging only.
        domain: Company email domain (e.g., "acme.com"). Cache key.
        company_name: Display name used in Apollo people search.

    Returns:
        List of Contact objects from the first successful provider.
        Returns empty list if all providers return no results.

    Raises:
        IntegrationError: If a provider call fails after all retries.
            The caller decides whether to try the next provider or abort.

    Note:
        This method NEVER raises on empty results — an empty list is a
        valid outcome (small company, no public contact data).
        Only network/auth failures raise IntegrationError.
    """
```

### Docstring Rules

| Rule | Detail |
|------|--------|
| All public API | Must have a docstring |
| Private helpers (`_method`) | Docstring required if non-obvious |
| Dunder methods (`__init__`, `__repr__`) | Docstring only if behaviour needs explanation |
| One-liner functions | May use single-line `"""Does X."""` format |
| Args section | Required if any parameter needs explanation beyond its name |
| Returns section | Required if return type alone is ambiguous |
| Raises section | Required for every exception that callers must handle |

---

## 5. Type Hints

All code must be fully type-annotated. `mypy --strict` must pass.

```python
# CORRECT: explicit types everywhere
async def find_eligible_leads(
    status: str,
    limit: int = 50,
    offset: int = 0,
) -> list[LeadORM]:
    ...

# CORRECT: use | None, not Optional[X] (Python 3.10+ union syntax)
async def get_by_domain(self, domain: str) -> LeadORM | None:
    ...

# CORRECT: TypedDict for structured dicts (especially LangGraph state)
from typing import TypedDict

class LeadPipelineState(TypedDict):
    lead_id: str
    is_eligible: bool | None
    matched_inventory_ids: list[str] | None

# WRONG: untyped
def process(data):  # ❌ no type hints
    ...

# WRONG: Any
from typing import Any
def process(data: Any) -> Any:  # ❌ use Any only as last resort
    ...
```

---

## 6. Immutability Rules

| Context | Rule |
|---------|------|
| Pydantic domain models | `model_config = {"frozen": True}` — always |
| Modifying a domain model | Use `model_copy(update={"status": LeadStatus.ENRICHED})` |
| LangGraph node return | Return new partial dict; never mutate `state` in place |
| Constants | Use `frozenset`, `tuple`, or `Final[...]` — never plain `list`/`dict` as module constants |
| Celery task arguments | Pass primitive types only (str, int, UUID as str) — never pass mutable objects |

```python
# CORRECT: derive new Lead from existing
updated_lead = lead.model_copy(update={"status": LeadStatus.ENRICHED, "updated_at": now})

# WRONG: mutate in place
lead.status = LeadStatus.ENRICHED  # ❌ frozen model will raise; also violates immutability principle
```

---

## 7. Async Rules

| Rule | Detail |
|------|--------|
| All I/O must be async | No synchronous `requests`, `psycopg2`, or `redis` calls in async functions |
| `asyncio.run()` only in Celery tasks | Never call `asyncio.run()` from within a running event loop |
| `async for` for streaming | Use async generators for large result sets from DB |
| `await asyncio.gather()` for parallel | Use `gather()` for independent concurrent operations |
| Never `time.sleep()` in async | Use `await asyncio.sleep()` |
| Celery tasks are synchronous | Tasks call `asyncio.run()` to enter the async context |

```python
# CORRECT: async DB query
leads = await lead_repo.list_by_status("enriched", limit=100)

# CORRECT: parallel async calls
results = await asyncio.gather(
    apollo_strategy.enrich(domain, company_name),
    hunter_strategy.verify_email(email),
)

# WRONG: blocking I/O in async function
import requests
response = requests.get(url)  # ❌ blocks the event loop
```

---

## 8. Error Handling

### Exception Hierarchy (project-specific)

```
BaseAppException (src/core/exceptions.py)
├── ValidationError          — invalid input data
│   ├── LeadValidationError
│   └── InventoryValidationError
├── NotFoundError            — entity not found
│   ├── LeadNotFoundError
│   ├── ContactNotFoundError
│   └── InventoryNotFoundError
├── AuthorizationError       — permission denied
│   └── InsufficientRoleError
├── IntegrationError         — external API failure
│   ├── ApolloError
│   ├── HunterError
│   ├── ProxycurlError
│   └── SendGridError
├── PipelineError            — LangGraph/Celery workflow failure
│   ├── MatchingError
│   ├── EnrichmentError
│   ├── ScoringError
│   └── OutreachGenerationError
└── ConfigurationError       — missing/invalid config at startup
```

### Error Handling Rules

```python
# CORRECT: raise domain exception at point of failure
if lead_orm is None:
    raise LeadNotFoundError(lead_id=str(lead_id))

# CORRECT: catch and re-wrap external errors
try:
    response = await self._client.post("/search", json=payload)
    response.raise_for_status()
except httpx.HTTPStatusError as exc:
    raise ApolloError(f"HTTP {exc.response.status_code}") from exc

# CORRECT: log with context before re-raising
logger.error(
    "Lead enrichment failed",
    lead_id=lead_id,
    domain=domain,
    error=str(exc),
    trace_id=trace_id,
)
raise EnrichmentError(lead_id=lead_id) from exc

# WRONG: bare except
try:
    result = await risky_operation()
except:  # ❌ catches BaseException including KeyboardInterrupt
    pass

# WRONG: silently swallow errors
try:
    await send_email(contact)
except Exception:  # ❌ no log, no re-raise
    pass
```

---

## 9. Logging Standards

All logging uses `structlog` via the `get_logger()` helper. No `print()` statements in production code.

```python
from src.core.logging import get_logger

logger = get_logger(__name__)

# CORRECT: structured key-value logging
logger.info(
    "Lead enriched successfully",
    lead_id=str(lead_id),
    provider=enrichment_source,
    contact_count=len(contacts),
    trace_id=trace_id,
    duration_ms=round(duration_ms, 2),
)

# WRONG: f-string message with no structure
logger.info(f"Enriched lead {lead_id} with {len(contacts)} contacts")  # ❌

# WRONG: print statement
print(f"Processing lead: {lead_id}")  # ❌ never in production code
```

### Log Level Guide

| Level | When to Use |
|-------|------------|
| `DEBUG` | Step-by-step trace, query plans, cache hits/misses |
| `INFO` | Major lifecycle events: lead ingested, enrichment complete, outreach sent |
| `WARNING` | Retries, fallback to secondary provider, rate limit approaching |
| `ERROR` | External API failure, DB error, pipeline node failure |
| `CRITICAL` | Platform unable to start (config missing, DB unreachable) |

---

## 10. API Response Format

All endpoints return the standard envelope. Never return naked domain objects.

```python
# src/api/schemas.py
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard response envelope for all API endpoints."""
    success: bool
    data: T | None = None
    error: str | None = None
    trace_id: str | None = None


class PageResponse(BaseModel, Generic[T]):
    """Paginated list response."""
    success: bool
    data: list[T]
    total: int
    page: int
    limit: int
    trace_id: str | None = None


# CORRECT: always wrap in APIResponse
return APIResponse(success=True, data=LeadResponse.model_validate(lead_orm))

# CORRECT: error response
return APIResponse(success=False, error="Lead not found", trace_id=trace_id)

# WRONG: return raw dict or domain model
return {"id": str(lead.id), "status": lead.status}  # ❌
return lead  # ❌
```

---

## 11. Configuration Rules

```python
# src/core/config.py
from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Rules:
        - All secrets use encrypted variants stored in DB (api_key_configs table)
        - Never log Settings values — treat entire object as sensitive
        - All required fields have no default — missing = startup crash
        - Feature flags are bool with explicit default
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str                          # required
    DB_POOL_SIZE: int = Field(default=10, ge=1, le=50)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=0, le=100)
    DB_ECHO: bool = False                      # True only in development

    # Redis
    REDIS_URL: str                             # required

    # Security
    JWT_SECRET_KEY: str                        # required
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FERNET_ENCRYPTION_KEY: str                 # required — for API key encryption

    # Feature flags
    HUMAN_REVIEW_REQUIRED: bool = True         # False = auto-send outreach (use with caution)
    ENRICHMENT_ENABLED: bool = True

    # AI
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)

    @field_validator("DATABASE_URL")
    @classmethod
    def database_url_must_be_async(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use asyncpg driver: postgresql+asyncpg://...")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings — loaded once at startup. Re-use everywhere."""
    return Settings()
```

### Configuration Rules

| Rule | Detail |
|------|--------|
| No hardcoded values | All values in `Settings` — never inline in code |
| No `.env` in version control | `.env` is in `.gitignore`; `.env.example` is committed |
| Startup validation | Missing required field = `ValidationError` at boot (not at runtime) |
| `get_settings()` is the only entry point | Never instantiate `Settings()` directly |
| Feature flags | Must have a safe default (e.g., `HUMAN_REVIEW_REQUIRED=True`) |

---

## 12. Database Access Rules

| Rule | Detail |
|------|--------|
| All queries via repository | No raw SQL in service or router |
| Soft deletes only | `is_deleted = True`; hard `DELETE` is forbidden on domain tables |
| `is_deleted = false` on all reads | Every `SELECT` must filter soft-deleted records |
| `crm_activity` is append-only | No `UPDATE`, no `soft_delete()` on `CRMRepository` |
| Timestamps are `TIMESTAMPTZ` | All datetime storage includes timezone |
| UUIDs for all PKs | Never use integer sequences |
| Parameterized queries only | Never use string interpolation in SQL |
| Migration naming | `NNN_verb_noun.py` — e.g., `008_add_whatsapp_to_outreach.py` |

---

## 13. Testing Standards

```
tests/
├── unit/
│   ├── services/           — service logic with mocked repositories
│   ├── repositories/       — repository queries against test DB
│   ├── agents/             — LangGraph node logic with mocked services
│   └── integrations/       — adapter mapping with mocked httpx
├── integration/
│   ├── api/                — FastAPI TestClient against real test DB
│   └── tasks/              — Celery tasks with real Redis
├── e2e/
│   └── flows/              — Full lead lifecycle (ingest → score → outreach draft)
└── factories/
    ├── lead_factory.py     — LeadORM factory_boy factories
    └── contact_factory.py
```

### Test Rules

| Rule | Detail |
|------|--------|
| Coverage target | 80% overall; 100% on `src/domain/`, `src/core/` |
| No magic values | Use `factory_boy` factories for test data |
| No shared state | Each test is fully isolated; use `pytest` fixtures |
| Async tests | Use `pytest-asyncio` with `asyncio_mode = "auto"` |
| Integration tests | Use a real PostgreSQL test DB (Docker Compose `test` profile) |
| No mocking the DB in integration | Mock only external HTTP; real DB always |
| AAA pattern | Arrange / Act / Assert with blank lines between sections |

```python
# CORRECT: test with factory, AAA pattern
import pytest
from tests.factories.lead_factory import LeadORMFactory

@pytest.mark.asyncio
async def test_enrich_lead_caches_result(enrichment_service, redis_cache):
    # Arrange
    lead_orm = LeadORMFactory.build(domain="acme.com")

    # Act
    contacts = await enrichment_service.enrich_lead(
        lead_id=str(lead_orm.id),
        domain="acme.com",
        company_name="Acme Corp",
    )
    cached_raw = await redis_cache.get("enrichment:acme.com")

    # Assert
    assert len(contacts) > 0
    assert cached_raw is not None
```

---

## 14. Diamond Domain Rules (Industry-Specific)

| Rule | Detail |
|------|--------|
| Carat weight precision | Always 2 decimal places: `DECIMAL(6,2)` in DB; `round(value, 2)` in code |
| Color grade | Stored as string: `D`, `E`, `F`, `G`, `H`, `I`, `J` — validated against GIA scale |
| Clarity grade | Stored as string: `IF`, `VVS1`, `VVS2`, `VS1`, `VS2`, `SI1`, `SI2` |
| Cut grade | `Excellent`, `Very Good`, `Good`, `Fair` |
| Certification | `GIA`, `IGI`, `HRD`, `AGS` — no other values accepted |
| Price precision | `DECIMAL(12,2)` — always USD, always 2 decimal places |
| Inventory match prerequisite | A lead with `is_eligible=False` must NEVER receive outreach — enforce in service |

---

## 15. Code Quality Checklist

Before submitting any code for review:

- [ ] All public functions/methods have type hints and docstrings
- [ ] No `print()` statements — use `logger.*` instead
- [ ] No hardcoded strings — use constants or config
- [ ] No mutable module-level state
- [ ] All Pydantic models are `frozen=True`
- [ ] All DB queries filter `is_deleted = false`
- [ ] No hard `DELETE` on domain tables
- [ ] `crm_activity` — append only (no update, no delete)
- [ ] Secrets come from `Settings`; never inline
- [ ] All external API calls wrapped in `try/except` with `IntegrationError` re-raise
- [ ] Logs use structured key=value format (no f-strings in message body)
- [ ] `ruff check src tests` passes with zero warnings
- [ ] `mypy src` passes with zero errors
- [ ] `pytest --cov=src` shows ≥ 80% coverage

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-03-18 | Initial standards — 15 sections covering naming, boilerplate, types, immutability, error handling, logging, DB rules, diamond domain |
