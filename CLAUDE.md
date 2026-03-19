# Jewelry AI — Claude Code Project Guide

**Name:** `jewelry-ai`
**Type:** Python AI Platform (FastAPI + LangChain + LangGraph + Streamlit)
**Stack:** Python 3.11+, FastAPI, LangChain, LangGraph, PostgreSQL + pgvector, Redis, Celery, n8n, Streamlit
**Purpose:** AI-powered lead automation platform for Shivam Jewels — transforms raw trade lists into enriched, scored, and outreached buyer relationships with zero manual intervention.

> **Generic operating principles, agile workflow, layer architecture, code quality, and documentation structure patterns are defined in:**
> **[ai-development-guidelines/CLAUDE-Generic.md](ai-development-guidelines/CLAUDE-Generic.md)**
> Read that file first. This file adds Jewelry AI-specific context, links, and commands on top of it.

---

## Pre-Code Reading Order

Before writing any code, read in this order:

1. **[CLAUDE-Generic.md](ai-development-guidelines/CLAUDE-Generic.md)** — Generic operating principles, layer architecture, agile workflow
2. **[Rules.md](ai-development-guidelines/Rules.md)** — Master engineering rules (non-negotiables, architecture, quality checklist)
3. **[FUNCTIONAL_LANDSCAPE.md](project-specific-guidelines/docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md)** — Complete module inventory, 7 layers, actor–module matrix
4. **[ACTORS.md](project-specific-guidelines/docs/actors/ACTORS.md)** — Actor definitions, roles, permissions, data scoping
5. **[Architecture.md](ai-development-guidelines/Architecture.md)** — Project folder structure, logging strategy, exception hierarchy
6. **[docs/DB_SCHEMA.md](ai-development-guidelines/docs/DB_SCHEMA.md)** — Database schema, enums, migration index
7. **[docs/API_SPEC.md](ai-development-guidelines/docs/API_SPEC.md)** — API endpoints, request/response shapes
7.5. **[docs/wireframes/](project-specific-guidelines/docs/wireframes/)** — HTML wireframe mockups for all UI screens (WF-000 to WF-007)
8. **[rules/testing-rules.md](ai-development-guidelines/rules/testing-rules.md)** — TDD workflow, pytest patterns, factory_boy, coverage gate
9. **Relevant Epic** in `ai-development-guidelines/epics/` — Scope and acceptance criteria
10. **Relevant User Story** in `ai-development-guidelines/stories/` — Behaviour, ACs, DoD

---

## Documentation Index

### Start Here

| Document | Purpose | Link |
|---|---|---|
| **Ideas & Approach** | Solution concepts, tech stack rationale, POC scope | [ideas.md](ai-development-guidelines/ideas.md) |
| **PRD** | Epics, user stories, functional landscape | [PRD.md](ai-development-guidelines/PRD.md) |
| **Execution Plan** | Phase-by-phase SDLC plan with task checklists | [Plan.md](ai-development-guidelines/Plan.md) |

### Architecture & Design

| Document | Purpose | Link |
|---|---|---|
| **Architecture** | Project folder structure, logging, exception hierarchy | [Architecture.md](ai-development-guidelines/Architecture.md) |
| **HLD** | System diagram, deployment diagram, integration flow | [HLD.md](ai-development-guidelines/HLD.md) |
| **LLD** | API endpoints, domain models, LangGraph nodes, Celery tasks | [LLD.md](ai-development-guidelines/LLD.md) |
| **Design Patterns** | Repository, Strategy, Factory, LangGraph State Machine, Adapter | [DesignPatterns.md](ai-development-guidelines/DesignPatterns.md) |

### Living Specifications

| Document | Purpose | Link |
|---|---|---|
| **API Spec** | Full API endpoints with request/response examples | [docs/API_SPEC.md](ai-development-guidelines/docs/API_SPEC.md) |
| **DB Schema** | Complete schema, column types, enums, migration index | [docs/DB_SCHEMA.md](ai-development-guidelines/docs/DB_SCHEMA.md) |
| **UI Wireframes** | HTML mockups for all 7 Streamlit screens with API annotations | [docs/wireframes/](project-specific-guidelines/docs/wireframes/) |

### Discovery & Planning

> **Full workflow:** See [EXECUTION_WORKFLOW.md](project-specific-guidelines/EXECUTION_WORKFLOW.md) for the complete Stage 0–7 sequence.
> **Sequence:** Functional Landscape → Actors → PRD → Architecture → API Spec → **UI Wireframes** → Epics → User Stories → Code

| Document | Layer | Purpose | Link |
|---|---|---|---|
| **Functional Landscape** | Project | 7-layer module inventory, actor–module matrix, out-of-scope | [docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md](project-specific-guidelines/docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md) |
| **Actor Index** | Project | All actors, roles, permissions, RBAC rules | [docs/actors/ACTORS.md](project-specific-guidelines/docs/actors/ACTORS.md) |
| **Landscape Rules — Jewelry AI** | Project | Layer definitions, module catalog, Jewelry AI-specific rules | [rules/functional-landscape-rules.md](project-specific-guidelines/rules/functional-landscape-rules.md) |
| **Actor Rules — Jewelry AI** | Project | Actor definitions, role permissions, data scoping | [rules/actor-roles-rules.md](project-specific-guidelines/rules/actor-roles-rules.md) |
| **Epic Rules** | Generic | Anatomy, lifecycle, sizing, INVEST | [rules/epic-rules.md](ai-development-guidelines/rules/epic-rules.md) |
| **User Story Rules** | Generic | Format, Three Cs, GWT, splitting | [rules/user-story-rules.md](ai-development-guidelines/rules/user-story-rules.md) |
| **Epic Rules — Jewelry AI** | Project | Platform catalog (EPIC-01–15), phases, API deps, DoD | [rules/epic-rules.md](project-specific-guidelines/rules/epic-rules.md) |
| **User Story Rules — Jewelry AI** | Project | Actors, toolchain DoD, AC examples, story paths | [rules/user-story-rules.md](project-specific-guidelines/rules/user-story-rules.md) |

### Standards & Rules

| Document | Purpose | Link |
|---|---|---|
| **Rules (Master)** | All rules index, architecture layers, code quality checklist | [Rules.md](ai-development-guidelines/Rules.md) |
| **Coding Standards** | Class boilerplate, docstrings, naming, type hints | [CodingStandards.md](ai-development-guidelines/CodingStandards.md) |
| Coding Style Rules | Immutability, async, file size, nesting | [rules/coding-style-rules.md](ai-development-guidelines/rules/coding-style-rules.md) |
| Security Rules | Secrets, validation, auth, rate limiting | [rules/security-rules.md](ai-development-guidelines/rules/security-rules.md) |
| Testing Rules | TDD, 80% coverage, test organization, factories | [rules/testing-rules.md](ai-development-guidelines/rules/testing-rules.md) |
| API Design Rules | REST conventions, response format, versioning | [rules/api-design-rules.md](ai-development-guidelines/rules/api-design-rules.md) |
| Data Rules | DB conventions, migrations, soft deletes, pgvector | [rules/data-rules.md](ai-development-guidelines/rules/data-rules.md) |
| Error & Observability | Exception hierarchy, structured logging, correlation IDs, health checks | [rules/error-observability.md](ai-development-guidelines/rules/error-observability.md) |
| DevOps & Deployment | Docker, CI/CD, env validation, Makefile, deployment checklist | [rules/devops-deployment.md](ai-development-guidelines/rules/devops-deployment.md) |
| AI / ML Rules | LangChain, LangGraph, LLM cost, Celery tasks, MLflow | [rules/ai-ml-rules.md](ai-development-guidelines/rules/ai-ml-rules.md) |
| Performance & Caching | Redis patterns, N+1 prevention, rate limiting, connection pooling | [rules/performance-caching-rules.md](ai-development-guidelines/rules/performance-caching-rules.md) |
| Frontend — Streamlit | Thin UI rules, APIClient, session state, caching, error handling | [rules/frontend-streamlit-rules.md](ai-development-guidelines/rules/frontend-streamlit-rules.md) |
| Workflow — n8n / LangGraph / Celery | Layer responsibilities, n8n webhook design, LangGraph state, Celery tasks | [rules/workflow-rules.md](ai-development-guidelines/rules/workflow-rules.md) |
| Configuration Management | Pydantic Settings class, feature flags, env file structure, env-specific overrides | [rules/configuration-rules.md](ai-development-guidelines/rules/configuration-rules.md) |
| Synthetic & Demo Data | Demo data rules, `.example.com` domains, seed script structure, test factories | [rules/synthetic-data-rules.md](ai-development-guidelines/rules/synthetic-data-rules.md) |
| **UI Wireframe Rules (generic)** | HTML format, WF-NNN naming, component library, API annotation pattern, DoD | [best-practices_rule_set_code/docs/rules/ui-wireframe-rules.md](best-practices_rule_set_code/docs/rules/ui-wireframe-rules.md) |
| **UI Wireframe Rules (Jewelry AI)** | 7-screen catalog, actor-screen matrix, API field bindings per screen | [rules/ui-wireframe-rules.md](project-specific-guidelines/rules/ui-wireframe-rules.md) |

### POC & Demo

| Document | Purpose | Link |
|---|---|---|
| **POC — Phase 0** | Local demo scope, 15-min demo script, setup instructions, success criteria | [docs/POC.md](ai-development-guidelines/docs/POC.md) |

---

## Domain Context

### Business Domain
Jewelry wholesale lead automation — Shivam Jewels sources diamond buyers from trade directories, matches them against live inventory, enriches their contacts, and sends personalized AI-generated outreach.

### User Roles
| Role | Description | Key Permissions |
|---|---|---|
| `admin` | System administrator | Full platform access, config management |
| `manager` | Sales manager | View all leads, approve outreach, configure rules |
| `rep` | Sales representative | View assigned leads, manage own outreach |

### Core Domain Entities
| Entity | Description | Key Relations |
|---|---|---|
| `Lead` | A jewelry buyer prospect (company) | Has contacts, matches, outreach messages |
| `Inventory` | A diamond/jewelry item in Shivam's stock | Matched to leads |
| `Contact` | Enriched buyer contact at a lead company | Belongs to lead |
| `OutreachMessage` | AI-generated email or WhatsApp message | Belongs to lead + contact |
| `CRMActivity` | Immutable audit event log entry | Belongs to lead |

### Key Business Rules
- A lead is only eligible for outreach if it matches at least one available inventory item
- Outreach requires human review before sending (configurable via `HUMAN_REVIEW_REQUIRED`)
- Enrichment API credits are finite — cache all results; never re-enrich an already enriched lead
- CRM activity is append-only and immutable — never update or delete `crm_activity` rows
- Diamond carat weights follow GIA grading standards — always 2 decimal places

### External Integrations
| Service | Purpose | Library |
|---|---|---|
| Apollo.io | Contact enrichment (email, phone, title) | `httpx` async client |
| Hunter.io | Email deliverability verification | `httpx` async client |
| Proxycurl | LinkedIn profile enrichment | `httpx` async client |
| SendGrid | Transactional + campaign email | `sendgrid` SDK |
| Twilio | WhatsApp outreach (Phase 2) | `twilio` SDK |
| n8n | Workflow automation for email sequences | REST webhook trigger |
| OpenAI | Outreach generation, embeddings | `langchain_openai` |
| Anthropic | Fallback LLM, reasoning agents | `langchain_anthropic` |
| MLflow | ML experiment tracking and model registry | `mlflow` |

---

## Quick Commands

> **Windows users:** `make` requires Git Bash, WSL2, or [GnuWin32 make](https://gnuwin32.sourceforge.net/packages/make.htm).
> All commands below show the `make` shortcut **and** the raw equivalent for PowerShell/CMD.

### Using `make` (Git Bash / WSL2 — recommended)

```bash
make up            # Start all services
make migrate       # Run Alembic migrations
make test-cov      # Run tests with coverage report
make check         # Lint + type check + test (full pre-PR check)
make dev           # Start FastAPI dev server (hot reload)
make ui            # Start Streamlit UI
make worker        # Start Celery worker
make migrate-new name="add_score_to_leads"   # Create new migration
```

### Raw Commands (PowerShell / CMD — no make required)

```powershell
# Start all services
docker compose up --build -d

# Run Alembic migrations
docker compose exec fastapi alembic upgrade head

# Run tests with coverage
docker compose exec fastapi pytest --cov=src --cov-report=term-missing

# Lint (ruff)
docker compose exec fastapi ruff check src tests

# Type check (mypy)
docker compose exec fastapi mypy src

# Start FastAPI dev server (outside Docker, local venv)
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Start Streamlit UI (outside Docker, local venv)
streamlit run src/ui/app.py

# Start Celery worker (outside Docker, local venv)
celery -A src.tasks.celery_app worker --loglevel=info -Q ingestion,enrichment,outreach,ml

# Create new Alembic migration
alembic revision --autogenerate -m "add_score_to_leads"
```

### Windows Virtual Environment

```powershell
# Create venv
python -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (CMD)
.\.venv\Scripts\activate.bat

# Install dependencies
pip install -e ".[dev]"
```

---

## Windows Developer Notes

This project is **fully supported on Windows** via Docker Desktop + Git Bash. See [rules/devops-deployment.md](ai-development-guidelines/rules/devops-deployment.md) → *Windows Developer Setup* section for:
- Shell recommendation (Git Bash vs WSL2 vs PowerShell)
- `make` ↔ PowerShell command equivalents
- Virtual environment activation on Windows
- Line ending setup (`.gitattributes` — required first step)
- `pathlib.Path` rule (no hardcoded `/` or `\` separators)
- Cross-platform URL-open pattern (`webbrowser.open()`)

---

## Current Phase

**Phase 0 — Foundation Setup** (see [Plan.md](ai-development-guidelines/Plan.md))

Immediate next steps:
1. `.gitattributes` — line ending enforcement (Windows compatibility)
2. `pyproject.toml` with ruff, mypy, pytest, isort config
3. `docker-compose.yml` with all services
4. `src/core/config.py` — pydantic-settings with startup validation
5. `src/db/session.py` — async SQLAlchemy engine
6. Alembic baseline migration
7. Scaffold complete folder structure per [Architecture.md](ai-development-guidelines/Architecture.md)

---

## Requirements Source

[Requirements/Requirements.txt](Requirements/Requirements.txt)
