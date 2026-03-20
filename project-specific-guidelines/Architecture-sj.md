# Architecture — Jewelry AI Platform

## Project Structure

```
Jewelry-AI/
├── CLAUDE.md                          # Project entry point for Claude Code
├── Requirements/
│   └── Requirements.txt
├── ai-development-guidelines/         # All documentation
│   ├── ideas.md
│   ├── Architecture.md
│   ├── Rules.md
│   ├── CodingStandards.md
│   ├── DesignPatterns.md
│   ├── PRD.md
│   ├── HLD.md
│   ├── LLD.md
│   ├── Plan.md
│   └── rules/
│       ├── coding-style-rules.md
│       ├── security-rules.md
│       ├── testing-rules.md
│       ├── api-design-rules.md
│       └── data-rules.md
├── src/
│   ├── api/                           # FastAPI application
│   │   ├── __init__.py
│   │   ├── main.py                    # App entrypoint
│   │   ├── dependencies.py            # Dependency injection
│   │   ├── middleware/
│   │   │   ├── logging_middleware.py
│   │   │   ├── auth_middleware.py
│   │   │   └── rate_limit_middleware.py
│   │   └── routers/
│   │       ├── leads.py
│   │       ├── inventory.py
│   │       ├── outreach.py
│   │       ├── enrichment.py
│   │       └── crm.py
│   ├── core/                          # Core config, logging, exceptions
│   │   ├── __init__.py
│   │   ├── config.py                  # Settings via pydantic-settings
│   │   ├── logging.py                 # Logging configuration
│   │   ├── exceptions.py              # Custom exception hierarchy
│   │   └── security.py               # Auth utilities
│   ├── domain/                        # Domain models (pure Python)
│   │   ├── __init__.py
│   │   ├── lead.py
│   │   ├── inventory.py
│   │   ├── contact.py
│   │   ├── outreach.py
│   │   └── scoring.py
│   ├── services/                      # Business logic layer
│   │   ├── __init__.py
│   │   ├── lead_ingestion_service.py
│   │   ├── inventory_match_service.py
│   │   ├── enrichment_service.py
│   │   ├── outreach_service.py
│   │   ├── crm_service.py
│   │   └── scoring_service.py
│   ├── agents/                        # LangChain / LangGraph agents
│   │   ├── __init__.py
│   │   ├── enrichment_agent.py        # Multi-tool contact enrichment
│   │   ├── outreach_agent.py          # Personalized message generation
│   │   ├── scoring_agent.py           # Lead scoring reasoning
│   │   └── workflows/
│   │       ├── lead_pipeline.py       # LangGraph full pipeline
│   │       └── follow_up_workflow.py  # LangGraph follow-up state machine
│   ├── repositories/                  # Data access layer
│   │   ├── __init__.py
│   │   ├── base_repository.py
│   │   ├── lead_repository.py
│   │   ├── inventory_repository.py
│   │   ├── contact_repository.py
│   │   ├── outreach_repository.py
│   │   └── crm_repository.py
│   ├── integrations/                  # Third-party API clients
│   │   ├── __init__.py
│   │   ├── apollo_client.py
│   │   ├── hunter_client.py
│   │   ├── linkedin_client.py
│   │   ├── sendgrid_client.py
│   │   ├── twilio_client.py
│   │   └── n8n_client.py
│   ├── scrapers/                      # Lead source scrapers
│   │   ├── __init__.py
│   │   ├── base_scraper.py
│   │   ├── gmt_scraper.py
│   │   ├── trade_book_scraper.py
│   │   └── rapid_list_scraper.py
│   ├── ml/                            # ML models and training
│   │   ├── __init__.py
│   │   ├── lead_scorer.py
│   │   ├── inventory_matcher.py
│   │   ├── fine_tuning/
│   │   │   ├── prepare_dataset.py
│   │   │   └── fine_tune_runner.py
│   │   └── experiments/               # MLflow experiment configs
│   ├── db/                            # Database layer
│   │   ├── __init__.py
│   │   ├── session.py                 # SQLAlchemy async session
│   │   ├── base.py                    # Declarative base
│   │   └── migrations/                # Alembic migrations
│   │       └── versions/
│   ├── tasks/                         # Celery background tasks
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── ingestion_tasks.py
│   │   ├── enrichment_tasks.py
│   │   └── outreach_tasks.py
│   └── ui/                            # Streamlit frontend
│       ├── __init__.py
│       ├── app.py                     # Streamlit entry point
│       ├── pages/
│       │   ├── dashboard.py
│       │   ├── leads.py
│       │   ├── inventory.py
│       │   ├── outreach.py
│       │   └── analytics.py
│       └── components/
│           ├── lead_table.py
│           ├── match_status_badge.py
│           └── outreach_timeline.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── infra/
│   ├── docker-compose.yml
│   ├── docker-compose.dev.yml
│   └── nginx/
├── scripts/
│   ├── seed_inventory.py
│   └── run_migrations.sh
├── .env.example
├── pyproject.toml
├── alembic.ini
└── Makefile
```

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI                              │
│  Dashboard | Leads | Inventory | Outreach | Analytics            │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP (REST)
┌─────────────────────▼───────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│  /leads  /inventory  /enrichment  /outreach  /crm               │
│                   Middleware: Auth | Rate Limit | Logging        │
└──────┬──────────────┬────────────────┬────────────────┬─────────┘
       │              │                │                │
┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│  SERVICES   │ │  AGENTS    │ │ REPOSITORIES│ │    TASKS    │
│  Business   │ │ LangChain  │ │   Data      │ │  Celery     │
│  Logic      │ │ LangGraph  │ │   Access    │ │  Workers    │
└──────┬──────┘ └─────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │              │                │                │
┌──────▼──────────────▼────────────────▼────────────────▼────────┐
│                      POSTGRESQL + pgvector                       │
│  leads | inventory | contacts | outreach_log | crm_activity     │
└─────────────────────────────────────────────────────────────────┘
       │              │                │
┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼──────┐
│  EXTERNAL   │ │    LLM     │ │    n8n      │
│  APIS       │ │  OpenAI /  │ │  Workflow   │
│ Apollo.io   │ │  Anthropic │ │  Engine     │
│ Hunter.io   │ │            │ │  Email/WA   │
│ LinkedIn    │ └────────────┘ └─────────────┘
└─────────────┘
```

---

## Logging Strategy

### Logging Levels

| Level | When to Use |
|---|---|
| `DEBUG` | Internal state, variable values during dev |
| `INFO` | Normal operations: request received, lead processed |
| `WARNING` | Recoverable issues: API rate limit hit, retry attempt |
| `ERROR` | Failures that affect a single request/operation |
| `CRITICAL` | System-wide failures: DB down, LLM unreachable |

### Logging Configuration (`src/core/logging.py`)

```python
import logging
import sys
from pythonjsonlogger import jsonlogger

def configure_logging(log_level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
```

### Structured Log Fields

Every log entry MUST include:
- `timestamp` — ISO 8601
- `service` — module name
- `level` — log level
- `message` — human-readable description
- `trace_id` — request correlation ID (injected by middleware)
- `lead_id` / `job_id` — entity context where applicable

### Logger Usage Pattern

```python
import logging

logger = logging.getLogger(__name__)

# Contextual logging with extra fields
logger.info(
    "Lead matched to inventory",
    extra={"lead_id": lead.id, "match_score": 0.92, "trace_id": ctx.trace_id}
)
```

### Log Destinations (Local POC)
- **Console** — stdout (captured by Docker)
- **File** — `logs/app.log` (rotating, 10MB max, 5 backups)
- **Future** — ELK Stack / Datadog for production

---

## Exception Handling Strategy

### Custom Exception Hierarchy (`src/core/exceptions.py`)

```
JewelryAIException (base)
├── DomainException
│   ├── LeadNotFoundException
│   ├── InventoryMatchException
│   └── DuplicateLeadException
├── IntegrationException
│   ├── ApolloAPIException
│   ├── HunterAPIException
│   ├── LinkedInAPIException
│   └── LLMProviderException
├── InfrastructureException
│   ├── DatabaseException
│   ├── CacheException
│   └── TaskQueueException
└── ValidationException
    ├── LeadValidationException
    └── InventoryValidationException
```

### Exception Handling Rules

1. **Never swallow exceptions silently** — always log with context before re-raising or returning error response.
2. **Domain exceptions** — caught at service layer, converted to HTTP errors at router layer.
3. **Integration exceptions** — wrapped with retry logic (tenacity); after max retries, raise `IntegrationException`.
4. **FastAPI global handler** — `@app.exception_handler` catches all unhandled exceptions, returns structured JSON error.
5. **LangGraph agents** — error nodes defined for each failure mode; agents log error and return graceful fallback state.

### FastAPI Global Exception Handler

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(JewelryAIException)
async def jewelry_ai_exception_handler(request: Request, exc: JewelryAIException):
    logger.error(
        "Application exception",
        extra={"error_type": type(exc).__name__, "detail": str(exc), "path": request.url.path}
    )
    return JSONResponse(
        status_code=exc.http_status,
        content={"success": False, "error": exc.user_message, "code": exc.error_code}
    )
```

### Retry Strategy (Integrations)

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
async def call_apollo_api(payload: dict) -> dict:
    ...
```

---

## Database Strategy

- **ORM**: SQLAlchemy 2.x with async engine (`asyncpg`)
- **Migrations**: Alembic (auto-generated, reviewed before apply)
- **Connection Pooling**: `asyncpg` pool, min=5, max=20
- **Soft Deletes**: All entities use `is_deleted` flag; hard deletes forbidden without explicit approval
- **Audit Columns**: `created_at`, `updated_at`, `created_by` on all tables

---

## Security Architecture

- **API Keys**: Stored in `.env`, loaded via `pydantic-settings`; never committed to git
- **Authentication**: JWT-based (FastAPI + python-jose)
- **Rate Limiting**: `slowapi` middleware per endpoint
- **CORS**: Restricted to known origins in production
- **Secrets Rotation**: Instructions in `ai-development-guidelines/rules/security-rules.md`
