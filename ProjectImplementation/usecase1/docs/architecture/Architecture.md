# Architecture — Jewelry AI Lead Automation Platform

**Version:** 1.0
**Status:** Approved
**Stage:** 3.1 — Architecture
**Created:** 2026-03-18
**Input:** PRD.md, FUNCTIONAL_LANDSCAPE.md, ACTORS.md

---

## 1. Architectural Principles

| Principle | Application |
|---|---|
| **Layer isolation** | Routers call services; services call repositories; repositories call the DB. No layer skips another. |
| **Dependency injection** | All service and repository dependencies injected via FastAPI `Depends()` — never instantiated inline. |
| **Async-first** | All I/O (DB, HTTP, Redis) is `async/await`. CPU-heavy work (ML inference) offloaded to Celery. |
| **Immutable domain models** | Pydantic models are never mutated in place; use `.model_copy(update={})` for updates. |
| **Fail fast, log context** | Exceptions raised immediately with full context; structured logs include `trace_id` on every line. |
| **Single source of truth** | Configuration via `pydantic-settings`; no magic numbers or strings inline anywhere. |
| **LLM calls in Layer 7 only** | All OpenAI/Anthropic calls originate from `src/agents/` — never from `src/services/` or below. |

---

## 2. Project Folder Structure

```
src/
│
├── main.py                          # FastAPI app factory, middleware, router registration
│
├── core/
│   ├── config.py                    # Pydantic Settings — all env vars with startup validation
│   ├── exceptions.py                # Exception hierarchy (see Section 5)
│   ├── logging.py                   # Structured JSON logger with trace_id injection
│   ├── events.py                    # In-process async EventBus for domain events
│   └── dependencies.py              # Shared FastAPI Depends() providers (DB session, auth)
│
├── db/
│   ├── session.py                   # Async SQLAlchemy engine + session factory
│   ├── base.py                      # SQLAlchemy declarative base
│   └── models/
│       ├── lead_model.py            # ORM model for leads table
│       ├── inventory_model.py       # ORM model for inventory table
│       ├── contact_model.py         # ORM model for contacts table
│       ├── match_model.py           # ORM model for lead_inventory_matches table
│       ├── outreach_model.py        # ORM model for outreach_messages table
│       ├── crm_model.py             # ORM model for crm_activity table
│       └── user_model.py            # ORM model for users, roles, api_keys tables
│
├── domain/
│   ├── lead.py                      # Lead Pydantic domain model + LeadStatus enum
│   ├── inventory.py                 # Inventory Pydantic domain model + ItemStatus enum
│   ├── contact.py                   # Contact Pydantic domain model + ContactSource enum
│   ├── outreach.py                  # OutreachMessage domain model + OutreachStatus enum
│   ├── crm.py                       # CRMActivity domain model + ActivityType enum
│   └── user.py                      # User, Role, Permission domain models
│
├── repositories/
│   ├── base_repository.py           # BaseRepository ABC with Generic[T]
│   ├── lead_repository.py           # LeadRepository — CRUD + filter by status/score/assigned_to
│   ├── inventory_repository.py      # InventoryRepository — CRUD + availability filter
│   ├── contact_repository.py        # ContactRepository — find by lead_id, email
│   ├── match_repository.py          # MatchRepository — store and query lead-inventory matches
│   ├── outreach_repository.py       # OutreachRepository — filter by status, lead_id
│   ├── crm_repository.py            # CRMRepository — append-only create; no update/delete
│   └── user_repository.py           # UserRepository — find by username, email, role
│
├── services/
│   ├── lead_ingestion_service.py    # Validate, deduplicate, persist leads; emit LeadIngestedEvent
│   ├── inventory_match_service.py   # Rule-based + embedding match; set ELIGIBLE/NOT_ELIGIBLE
│   ├── enrichment_service.py        # Orchestrate Apollo → Hunter → Proxycurl cascade
│   ├── lead_scoring_service.py      # Feature extraction + XGBoost inference; write score
│   ├── outreach_service.py          # Generate draft → review gate → send → track
│   ├── crm_service.py               # Append activity records; enforce write-once
│   └── auth_service.py              # JWT creation/validation, password hashing, login
│
├── agents/
│   ├── enrichment_agent.py          # LangChain tool-use agent for contact enrichment
│   ├── outreach_agent.py            # LangChain LLM chain for email generation
│   ├── scoring_agent.py             # XGBoost feature pipeline + inference wrapper
│   └── workflows/
│       ├── lead_pipeline.py         # LangGraph: ingest → match → enrich → score → outreach
│       └── follow_up_workflow.py    # LangGraph: Day 4 / Day 7 follow-up state machine
│
├── integrations/
│   ├── apollo_client.py             # Adapter: Apollo.io People Enrichment API
│   ├── hunter_client.py             # Adapter: Hunter.io Email Verification API
│   ├── proxycurl_client.py          # Adapter: Proxycurl LinkedIn Profile API
│   ├── sendgrid_client.py           # Adapter: SendGrid Transactional Email + Webhooks
│   ├── twilio_client.py             # Adapter: Twilio WhatsApp Conversations API
│   ├── n8n_client.py                # Adapter: n8n REST Webhook trigger
│   ├── openai_client.py             # Adapter: OpenAI Completions + Embeddings
│   └── mlflow_client.py             # Adapter: MLflow experiment logging + model registry
│
├── tasks/
│   ├── celery_app.py                # Celery app factory + queue definitions
│   ├── ingestion_tasks.py           # Celery tasks: bulk_ingest_leads
│   ├── enrichment_tasks.py          # Celery tasks: enrich_lead_task (retries 3x)
│   ├── outreach_tasks.py            # Celery tasks: generate_outreach_task, send_outreach_task
│   └── ml_tasks.py                  # Celery tasks: score_lead_task, retrain_model_task
│
├── ml/
│   ├── lead_scorer.py               # XGBoost model load, predict, feature vector builder
│   ├── feature_engineering.py       # Feature extraction from Lead + Contact + Match records
│   └── fine_tuning/
│       └── prepare_dataset.py       # Training data preparation for fine-tuned LLM
│
├── api/
│   ├── dependencies.py              # Route-level DI: get_lead_service, get_current_user, etc.
│   ├── middleware.py                 # Request logging, trace_id injection, CORS, rate limiting
│   └── routers/
│       ├── health.py                # GET /health
│       ├── auth.py                  # POST /auth/login, POST /auth/refresh
│       ├── leads.py                 # /api/v1/leads
│       ├── inventory.py             # /api/v1/inventory
│       ├── enrichment.py            # /api/v1/enrichment
│       ├── outreach.py              # /api/v1/outreach
│       ├── crm.py                   # /api/v1/crm
│       ├── analytics.py             # /api/v1/analytics
│       └── admin.py                 # /api/v1/admin
│
├── ui/
│   ├── app.py                       # Streamlit entry point — page routing
│   ├── api_client.py                # HTTP client wrapping all FastAPI calls
│   ├── auth.py                      # Streamlit login page + session token management
│   └── pages/
│       ├── dashboard.py             # Lead list + pipeline summary
│       ├── lead_detail.py           # Per-lead detail: contacts, matches, outreach, CRM log
│       ├── outreach_review.py       # Manager review queue
│       ├── analytics.py             # Pipeline funnel, outreach performance, scoring distribution
│       └── admin.py                 # User management, API keys, feature flags
│
└── scrapers/                        # Phase 8 — scheduled scraping
    ├── base_scraper.py              # BaseScraper ABC
    ├── gmt_scraper.py               # GMT trade directory scraper
    └── trade_book_scraper.py        # Jewelry Book of Trade scraper
```

---

## 3. Layer Responsibilities

| Layer | Location | Allowed To | NOT Allowed To |
|---|---|---|---|
| **Router** | `src/api/routers/` | Parse request, call service, return response | Contain business logic, query DB directly |
| **Service** | `src/services/` | Orchestrate business logic, call repositories, emit events | Call DB directly, make HTTP calls to external APIs |
| **Repository** | `src/repositories/` | Execute SQL queries, map ORM to domain model | Contain business logic, call external services |
| **Agent** | `src/agents/` | Call LLM/ML; orchestrate LangChain/LangGraph | Call repositories directly; handle HTTP requests |
| **Integration** | `src/integrations/` | Wrap external APIs, translate to domain model | Contain business logic; call services or repositories |
| **Task** | `src/tasks/` | Execute async background work, call services | Hold state between calls; directly access DB |
| **UI** | `src/ui/` | Call FastAPI via `api_client.py`, render data | Contain any business logic; call DB or services directly |

---

## 4. Logging Strategy

### Format
All logs are emitted as structured JSON — never plain strings in production.

```python
# src/core/logging.py
import logging
import json
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", None),
            **getattr(record, "extra", {}),
        })
```

### trace_id Injection
Every inbound HTTP request generates a `trace_id` (UUID4) in `src/api/middleware.py`. It is:
- Added to the request state: `request.state.trace_id`
- Injected into all log records via a `logging.Filter` for the request lifecycle
- Returned in every API response header: `X-Trace-ID`
- Stored on `CRMActivity.trace_id` for backend event correlation

### Log Levels

| Level | When to Use |
|---|---|
| `DEBUG` | Internal state details — only in development |
| `INFO` | Successful state transitions — lead ingested, enrichment complete, email sent |
| `WARNING` | Recoverable anomalies — duplicate detected, enrichment cache miss, retry attempt |
| `ERROR` | Unrecoverable operation failure — external API down, DB write failed |
| `CRITICAL` | Platform-level failures — DB unreachable, config missing |

### Logger Naming
```python
# Every module uses __name__ for proper hierarchy
logger = logging.getLogger(__name__)
# Results in: src.services.lead_ingestion_service, src.agents.outreach_agent, etc.
```

---

## 5. Exception Hierarchy

```
BaseAppException (RuntimeError)
│
├── ValidationException                 # 422 — input failed schema validation
│   ├── LeadValidationException
│   ├── InventoryValidationException
│   └── OutreachValidationException
│
├── NotFoundException                   # 404 — resource does not exist
│   ├── LeadNotFoundException
│   ├── InventoryNotFoundException
│   ├── ContactNotFoundException
│   └── UserNotFoundException
│
├── ConflictException                   # 409 — duplicate or state conflict
│   ├── DuplicateLeadException
│   └── OutreachAlreadySentException
│
├── AuthException                       # 401/403 — auth and permission errors
│   ├── InvalidCredentialsException
│   ├── TokenExpiredException
│   └── InsufficientPermissionsException
│
├── IntegrationException                # 502 — external API failure
│   ├── ApolloAPIException
│   ├── HunterAPIException
│   ├── ProxycurlAPIException
│   ├── SendGridAPIException
│   └── OpenAIAPIException
│
├── BusinessRuleException               # 400 — domain rule violation
│   ├── LeadNotEligibleException        # Cannot enrich NOT_ELIGIBLE lead
│   ├── OutreachPendingReviewException  # Cannot send unapproved message
│   └── EnrichmentCreditException       # Re-enrichment of already-enriched lead
│
└── InfrastructureException             # 500 — internal platform error
    ├── DatabaseException
    └── CacheException
```

### Error Handler Registration (main.py)
```python
@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "code": exc.code,
            "detail": exc.detail,
            "trace_id": request.state.trace_id,
        }
    )
```

---

## 6. Configuration Management

All configuration lives in `src/core/config.py` using `pydantic-settings`.

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"           # development | staging | production
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str                        # Required — no default

    # Database
    DATABASE_URL: str                      # Required
    REDIS_URL: str = "redis://localhost:6379/0"

    # External APIs
    OPENAI_API_KEY: str                    # Required
    ANTHROPIC_API_KEY: str = ""           # Optional — fallback LLM
    APOLLO_API_KEY: str                    # Required for enrichment
    HUNTER_API_KEY: str                    # Required for enrichment
    PROXYCURL_API_KEY: str = ""           # Optional — high-value leads only
    SENDGRID_API_KEY: str                  # Required for email delivery
    SENDGRID_FROM_EMAIL: str               # Required
    TWILIO_ACCOUNT_SID: str = ""          # Optional — Phase 3
    TWILIO_AUTH_TOKEN: str = ""           # Optional — Phase 3
    N8N_WEBHOOK_URL: str = ""             # Optional — Phase 2

    # Feature Flags
    HUMAN_REVIEW_REQUIRED: bool = True    # Master outreach gate
    MAX_BATCH_SIZE: int = 500
    ENRICHMENT_CACHE_TTL_DAYS: int = 7
    INVENTORY_MATCH_MIN_CARAT: float = 0.50
    LEAD_SCORE_HIGH_THRESHOLD: float = 70.0
    LEAD_SCORE_LOW_THRESHOLD: float = 40.0

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

**Startup validation:** If any required field is missing, `pydantic-settings` raises `ValidationError` before the app starts — no silent misconfigurations.

---

## 7. Database Session Management

```python
# src/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,      # Drop stale connections before use
    echo=settings.APP_ENV == "development",
)

AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

async def get_async_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## 8. Celery Task Architecture

### Queue Definitions
```python
# src/tasks/celery_app.py
from celery import Celery
from src.core.config import settings

celery_app = Celery(
    "jewelry_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.task_routes = {
    "src.tasks.ingestion_tasks.*":  {"queue": "ingestion"},
    "src.tasks.enrichment_tasks.*": {"queue": "enrichment"},
    "src.tasks.outreach_tasks.*":   {"queue": "outreach"},
    "src.tasks.ml_tasks.*":         {"queue": "ml"},
}
```

### Worker Start Command
```bash
celery -A src.tasks.celery_app worker \
  --loglevel=info \
  -Q ingestion,enrichment,outreach,ml \
  --concurrency=4
```

---

## 9. Test Organisation

```
tests/
├── conftest.py                      # Shared fixtures: async DB session, mock clients, factories
├── factories/
│   ├── lead_factory.py              # Factory for Lead domain objects (uses faker)
│   ├── inventory_factory.py         # Factory for Inventory domain objects
│   └── contact_factory.py           # Factory for Contact domain objects
│
├── unit/
│   ├── services/
│   │   ├── test_lead_ingestion_service.py
│   │   ├── test_inventory_match_service.py
│   │   ├── test_enrichment_service.py
│   │   └── test_outreach_service.py
│   ├── agents/
│   │   └── test_outreach_agent.py
│   └── domain/
│       └── test_lead_validators.py
│
├── integration/
│   ├── test_leads_api.py            # Full router → service → DB integration tests
│   ├── test_enrichment_api.py
│   ├── test_outreach_api.py
│   └── test_crm_api.py
│
└── e2e/
    └── test_lead_pipeline.py        # Full end-to-end pipeline test with test DB
```

### Coverage Target
- Minimum: **80%** overall
- Services: **90%** (critical business logic)
- Repositories: **70%** (DB-backed; integration tests carry the weight)

---

## 10. Migration Strategy (Alembic)

```
alembic/
├── env.py                           # Async migration environment
├── script.py.mako                   # Migration template
└── versions/
    ├── 001_baseline.py              # Empty baseline — all tables as of Phase 0
    ├── 002_create_leads_inventory.py
    ├── 003_create_contacts_matches.py
    ├── 004_create_outreach_crm.py
    └── 005_create_users_roles.py
```

**Rules:**
- One migration per logical change — never bundle unrelated schema changes
- Never edit a migration that has been applied to any environment
- Always include `downgrade()` implementations
- Test `upgrade()` + `downgrade()` locally before PR

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-03-18 | Initial Architecture — folder structure, layer responsibilities, logging, exception hierarchy, config, Celery, test organisation, migration strategy |
