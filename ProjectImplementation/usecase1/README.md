# Jewelry AI — Lead Automation Platform

**Usecase 1:** Diamond & Jewelry Wholesale Lead Automation
**Stack:** Python 3.11, FastAPI, LangChain, LangGraph, PostgreSQL + pgvector, Redis, Celery, Streamlit
**Purpose:** End-to-end automation of the lead lifecycle for Shivam Jewels — from raw trade directory CSV to enriched, scored, and AI-outreached buyer relationships.

---

## Prerequisites

| Requirement | Minimum Version | Notes |
|---|---|---|
| Python | 3.11 | `python --version` |
| Docker Desktop | 4.x | With Compose V2 |
| Git Bash / WSL2 | — | Required for `make` commands on Windows |
| GNU Make | 4.x | Via Git Bash or [GnuWin32](https://gnuwin32.sourceforge.net/packages/make.htm) |
| Git | 2.x | |

> **Windows users:** All `make` commands require Git Bash or WSL2. PowerShell/CMD equivalents are listed in every section below.

---

## Quick Start (Docker — Recommended)

Run these commands **in order**. Each step must complete before the next.

### Step 1 — Clone and configure environment

```bash
# Clone the repository (if not already done)
git clone <repo-url>
cd Jewelry-AI/ProjectImplementation/usecase1

# Copy the environment template and fill in your API keys
cp .env.example .env
# Edit .env — set SECRET_KEY, OPENAI_API_KEY, APOLLO_API_KEY, HUNTER_API_KEY,
#              SENDGRID_API_KEY, SENDGRID_FROM_EMAIL at minimum
```

> **Minimum required .env values to start:**
> ```
> SECRET_KEY=your-secret-key-at-least-32-characters-long
> OPENAI_API_KEY=sk-...
> APOLLO_API_KEY=...
> HUNTER_API_KEY=...
> SENDGRID_API_KEY=SG....
> SENDGRID_FROM_EMAIL=outreach@yourdomain.com
> ```
> All other values have safe defaults for local development.

---

### Step 2 — Start all services

```bash
make up
```

**PowerShell equivalent:**
```powershell
docker compose up --build -d
```

This starts 8 services:

| Service | URL | Purpose |
|---|---|---|
| **FastAPI** | http://localhost:8000 | Main API + Swagger docs |
| **Streamlit UI** | http://localhost:8501 | Dashboard (Phase 2+) |
| **PostgreSQL** | localhost:5432 | Primary database (pgvector enabled) |
| **Redis** | localhost:6379 | Cache + Celery broker |
| **Celery Worker** | — | Background task processor |
| **n8n** | http://localhost:5678 | Workflow automation (Phase 4+) |
| **Prometheus** | http://localhost:9090 | Metrics collection |
| **Grafana** | http://localhost:3000 | Metrics dashboards (admin/admin) |
| **MLflow** | http://localhost:5001 | ML experiment tracking |

Wait ~30 seconds for all services to start, then verify:
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","service":"jewelry-ai","version":"1.0.0"}
```

---

### Step 3 — Run database migrations

```bash
make migrate
```

**PowerShell equivalent:**
```powershell
docker compose exec fastapi alembic upgrade head
```

This applies all Alembic migrations in order:
- `001_baseline` — PostgreSQL extensions (pgvector, uuid-ossp)
- `002_leads_table` — leads table with partial unique domain index

Verify migrations applied:
```bash
docker compose exec fastapi alembic current
# Should show: 002 (head)
```

---

### Step 4 — Verify the API is running

```bash
# Liveness probe
curl http://localhost:8000/health

# Readiness probe (checks DB + Redis connectivity)
curl http://localhost:8000/health/ready

# Swagger UI (interactive API documentation)
open http://localhost:8000/docs
```

---

## Running Tests

### Unit tests (no Docker required — fast, all dependencies mocked)

```bash
# Activate virtual environment first (see Local Development section below)
make test-unit
```

**PowerShell equivalent:**
```powershell
python -m pytest tests/unit/ -v
```

### Unit tests with coverage report

```bash
make test-cov
```

**PowerShell equivalent:**
```powershell
python -m pytest tests/unit/ --cov=src --cov-report=term-missing --cov-fail-under=80
```

Expected output:
```
101 passed in 0.72s
Required test coverage of 80% reached. Total coverage: 84%
```

### Integration tests (requires running Docker services)

```bash
make test-integration
```

**PowerShell equivalent:**
```powershell
docker compose exec fastapi pytest tests/integration/ -v -m integration
```

> Integration tests connect to real PostgreSQL and Redis. Run `make up` + `make migrate` first.

### All tests + full quality check (pre-PR gate)

```bash
make check
```

**PowerShell equivalent:**
```powershell
docker compose exec fastapi ruff check src tests && docker compose exec fastapi mypy src && docker compose exec fastapi pytest --cov=src --cov-fail-under=80
```

---

## Local Development (without Docker)

Use this for faster iteration — edit code locally, tests run instantly.

### Step 1 — Create and activate virtual environment

```powershell
# PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# Git Bash / WSL2
python -m venv .venv
source .venv/Scripts/activate
```

### Step 2 — Install dependencies

```bash
pip install -e ".[dev]"
```

### Step 3 — Set required environment variables

```bash
# Git Bash
export APP_ENV=testing
export SECRET_KEY="local-dev-secret-key-32-chars-ok!"
export DATABASE_URL="postgresql+asyncpg://jewelry_ai:jewelry_ai@localhost:5432/jewelry_ai_db"
export TEST_DATABASE_URL="postgresql+asyncpg://jewelry_ai:jewelry_ai@localhost:5432/jewelry_ai_test"
export REDIS_URL="redis://localhost:6379/0"
export OPENAI_API_KEY="sk-..."
export APOLLO_API_KEY="..."
export HUNTER_API_KEY="..."
export SENDGRID_API_KEY="SG...."
export SENDGRID_FROM_EMAIL="test@example.com"
```

Or copy `.env.example` to `.env` and fill it in — the app loads `.env` automatically via Pydantic Settings.

### Step 4 — Start FastAPI dev server (hot reload)

```bash
make dev
# or:
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5 — Start Celery worker (separate terminal)

```bash
make worker
# or:
celery -A src.tasks.celery_app worker --loglevel=info -Q ingestion,enrichment,outreach,ml
```

---

## API Usage — Lead Ingestion

### Upload a CSV file of leads

```bash
curl -X POST http://localhost:8000/api/v1/leads/upload \
  -F "file=@leads.csv"
```

**CSV format:**
```csv
company_name,domain,country,source
Acme Jewelers,acmejewelers.com,US,gmt
Beta Diamonds,betadiamonds.com,UK,trade_book
No Domain Corp,,IN,manual
```

**Required columns:** `company_name`
**Optional columns:** `domain`, `country`
**Valid sources:** `gmt`, `trade_book`, `rapid_list`, `manual`, `api`
**Batch limit:** 500 rows per upload

**Response (202 Accepted):**
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "accepted"
}
```

### Poll ingestion job status

```bash
curl http://localhost:8000/api/v1/leads/jobs/f47ac10b-58cc-4372-a567-0e02b2c3d479
```

**Response (completed):**
```json
{
  "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "completed",
  "created": 80,
  "skipped_duplicates": 15,
  "skipped_invalid": 5,
  "errors": 0
}
```

**Polling guidance:** Poll every 2 seconds; timeout after 5 minutes.
**Job expiry:** Results available for 24 hours.

---

## Makefile Reference

| Command | Description |
|---|---|
| `make up` | Start all Docker services |
| `make down` | Stop all Docker services |
| `make restart` | Restart all services |
| `make logs` | Tail logs from all services |
| `make migrate` | Run pending Alembic migrations |
| `make migrate-new name="..."` | Create new Alembic migration |
| `make migrate-down` | Roll back last migration |
| `make test` | Run all tests |
| `make test-unit` | Run unit tests only (no Docker needed) |
| `make test-integration` | Run integration tests (Docker required) |
| `make test-e2e` | Run end-to-end tests (full stack) |
| `make test-cov` | Run tests with coverage report |
| `make lint` | Run ruff linter |
| `make lint-fix` | Run ruff with auto-fix |
| `make type-check` | Run mypy type checker |
| `make check` | Full pre-PR gate: lint + type-check + test-cov |
| `make dev` | Start FastAPI with hot reload |
| `make ui` | Start Streamlit UI |
| `make worker` | Start Celery worker |
| `make shell` | Open shell inside FastAPI container |
| `make clean` | Remove build artifacts and caches |

---

## Project Structure

```
usecase1/
├── src/
│   ├── api/
│   │   ├── middleware.py          # TraceIDMiddleware — X-Trace-ID per request
│   │   ├── routers/
│   │   │   ├── health.py          # GET /health, GET /health/ready
│   │   │   └── leads.py           # POST /api/v1/leads/upload, GET /jobs/{id}
│   │   └── dependencies.py        # Route-level FastAPI dependencies
│   ├── core/
│   │   ├── config.py              # Pydantic Settings (fail-fast on missing vars)
│   │   ├── exceptions.py          # Exception hierarchy (8 categories, 30+ classes)
│   │   ├── logging.py             # JSON structured logging + trace_id
│   │   ├── job_store.py           # Redis-backed async job status (TTL 24h)
│   │   └── events.py              # In-process async event bus
│   ├── db/
│   │   ├── base.py                # SQLAlchemy declarative base
│   │   ├── session.py             # Async engine + session factory
│   │   └── models/
│   │       └── lead.py            # Lead ORM model
│   ├── domain/
│   │   └── lead.py                # LeadStatus, LeadSource enums; Pydantic schemas
│   ├── repositories/
│   │   └── lead_repository.py     # Lead DB operations
│   ├── services/
│   │   └── ingestion_service.py   # CSV parse, deduplicate, persist
│   ├── tasks/
│   │   ├── celery_app.py          # Celery config (4 queues)
│   │   └── ingestion.py           # ingest_lead_file Celery task
│   └── main.py                    # FastAPI app factory
├── tests/
│   ├── unit/                      # Fast tests, all dependencies mocked
│   │   ├── api/                   # Router tests
│   │   ├── core/                  # Config, exceptions, logging tests
│   │   ├── domain/                # Schema validation tests
│   │   └── services/              # Business logic tests
│   └── integration/               # Real DB + Redis (Docker required)
├── alembic/
│   └── versions/
│       ├── 001_baseline.py        # pgvector + uuid-ossp extensions
│       └── 002_leads_table.py     # leads table + partial unique index
├── pyproject.toml                 # Dependencies, ruff, mypy, pytest, coverage config
├── docker-compose.yml             # 8-service local stack
├── Dockerfile                     # Production container
├── Makefile                       # Developer shortcuts
└── .env.example                   # Environment variable template
```

---

## CI/CD Pipeline

GitHub Actions workflow: `.github/workflows/usecase1-ci.yml`

| Job | Trigger | What it does |
|---|---|---|
| `quality` | Every push/PR | ruff lint + mypy type check |
| `unit-tests` | Every push/PR | pytest unit tests + 80% coverage gate |
| `integration-tests` | Every push/PR | pytest integration tests with real PostgreSQL + Redis service containers |

All 3 jobs must pass before merging to master.

---

## Environment Variables Reference

See `.env.example` for the complete list with descriptions.

**Required (app will not start without these):**

| Variable | Example | Description |
|---|---|---|
| `SECRET_KEY` | `a-32-char-random-string` | JWT signing key |
| `DATABASE_URL` | `postgresql+asyncpg://...` | PostgreSQL connection URL |
| `OPENAI_API_KEY` | `sk-...` | OpenAI API key for LLM + embeddings |
| `APOLLO_API_KEY` | `...` | Apollo.io contact enrichment |
| `HUNTER_API_KEY` | `...` | Hunter.io email verification |
| `SENDGRID_API_KEY` | `SG....` | SendGrid email delivery |
| `SENDGRID_FROM_EMAIL` | `outreach@domain.com` | Verified sender email address |

---

## Increment Status

| Increment | Epic(s) | User Stories | Status |
|---|---|---|---|
| **Increment 0** — Foundation | EPIC-01 | US-001–005, US-052 | ✅ Complete |
| **Increment 1** — Lead Ingestion | EPIC-02 | US-006–009 | ✅ Complete |
| **Increment 2** — Contact Enrichment | EPIC-04 | US-010–013 | ⬜ Next |
| **Increment 3** — Inventory Matching | EPIC-03 | US-014–017 | ⬜ |
| **Increment 4** — AI Outreach Generation | EPIC-05 | US-018–021 | ⬜ |
| **Increment 5** — Email Delivery & Tracking | EPIC-06 | US-022–024 | ⬜ |
| **Increment 6** — CRM Activity Log | EPIC-07 | US-025–027 | ⬜ |
| **Increment 7** — Lead Scoring | EPIC-08 | US-028–031 | ⬜ |
| **Increment 8** — Streamlit Dashboard | EPIC-09 | US-032–035 | ⬜ |
| **Increment 9** — Auth & RBAC | EPIC-11 | US-039–041 | ⬜ |
| **Increment 10** — n8n Automation | EPIC-10 | US-036–038 | ⬜ |

---

## Troubleshooting

**Port already in use:**
```bash
make down && make up
```

**Database migrations not applied:**
```bash
make migrate
# Check current revision:
docker compose exec fastapi alembic current
```

**Test environment variable errors:**
All required env vars are injected by `tests/conftest.py` — no `.env` needed for unit tests.

**`make` not found on Windows:**
Use Git Bash, or run the raw PowerShell commands listed in each section above.

**`pip install` dependency conflicts:**
The warnings about `langchain-ollama` / `langchain-qdrant` are from your global Python environment — not this project. Use a virtual environment (`python -m venv .venv`) to isolate dependencies.
