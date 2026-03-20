# Jewelry AI — Claude Code Project Guide

**Name:** `jewelry-ai`
**Type:** Python AI Platform (FastAPI + LangChain + LangGraph + Streamlit)
**Stack:** Python 3.11+, FastAPI, LangChain, LangGraph, PostgreSQL + pgvector, Redis, Celery, n8n, Streamlit
**Purpose:** AI-powered lead automation platform for Shivam Jewels — transforms raw trade lists into enriched, scored, and outreached buyer relationships with zero manual intervention.

> **Generic operating principles, agile workflow, layer architecture, code quality, and documentation structure patterns are defined in:**
> **[best-practices_rule_set_code/CLAUDE-generic.md](best-practices_rule_set_code/CLAUDE-generic.md)**
> Read that file first. This file adds Jewelry AI-specific context, links, and commands on top of it.

---

## MANDATORY: Rule Folders — Read Before Any Work

**Before writing any code, creating any artifact, or starting any increment, ALL relevant files in BOTH folders MUST be read and followed:**

### 1. Generic & Stack Rules — `best-practices_rule_set_code/`

This folder contains reusable engineering standards. Files are suffixed by type:
- `-generic` = stack-agnostic, applies to all projects
- `-python` = Python/FastAPI/SQLAlchemy stack (this project's stack)
- `-nestjs` = NestJS/TypeScript stack (not applicable here — see `GUIDELINES_COMPLIANCE-sj.md`)

| File | Must Read Before |
|---|---|
| `CLAUDE-generic.md` | Starting any project session |
| `RULES-generic.md` | Writing any code |
| `CodingStandards-python.md` | Writing any Python class or function |
| `DesignPatterns-generic.md` | Selecting implementation patterns |
| `docs/rules/development-execution-generic.md` | **Starting any increment** — increment anatomy, layer build order, gates |
| `docs/rules/testing-rules-generic.md` | **Writing any test** — respx, factory_boy, TDD workflow, coverage gate |
| `docs/rules/testing-quality-generic.md` | Writing any test — coverage thresholds, mocking rules |
| `docs/rules/api-contracts-generic.md` | Writing any router or endpoint |
| `docs/rules/data-rules-python.md` | Writing any migration, repository, or ORM model |
| `docs/rules/error-observability-python.md` | Writing exception handling or logging |
| `docs/rules/security-python.md` | Writing any endpoint that handles auth or user data |
| `docs/rules/devops-deployment-python.md` | Writing Dockerfiles, CI pipelines, Makefiles |
| `docs/rules/configuration-rules-python.md` | Writing any config, settings, or env handling |
| `docs/rules/performance-caching-rules-python.md` | Writing Redis, caching, or async patterns |
| `docs/rules/coding-style-rules-generic.md` | Writing any function or class |
| `docs/rules/functional-landscape-rules-generic.md` | Running Stage 1 Discovery |
| `docs/rules/actor-roles-rules-generic.md` | Defining actors or RBAC |
| `docs/rules/epic-rules-generic.md` | Writing Epics |
| `docs/rules/user-story-rules-generic.md` | Writing User Stories |
| `docs/rules/ui-wireframe-rules-generic.md` | Creating HTML wireframes (Stage 3.6) |
| `docs/rules/frontend-streamlit-generic.md` | Writing Streamlit UI pages |

### 2. Project-Specific Guidelines — `project-specific-guidelines/`

This folder contains Jewelry AI-specific decisions, overrides, and artifacts that extend the generic framework for this project. All files are suffixed `-sj`.

| File | Must Read Before |
|---|---|
| `EXECUTION_WORKFLOW-sj.md` | Starting any stage or increment |
| `GUIDELINES_COMPLIANCE-sj.md` | Starting any session — confirms which rules apply and which SJ overrides exist |
| `SKILLS-sj.md` | Executing any repeatable workflow — increment, enrichment, UI screen, LangGraph agent |
| `CodingStandards-sj.md` | Writing any Python code for this project |
| `DesignPatterns-sj.md` | Implementing services, repositories, or agents |
| `Architecture-sj.md` | Making any architectural decision or folder structure choice |
| `HLD-sj.md` | Making any system-level design decision |
| `LLD-sj.md` | Implementing any service, task, or router |
| `Plan-sj.md` | Planning or prioritising any work |
| `rules/functional-landscape-rules-sj.md` | Running Stage 1 Discovery |
| `rules/actor-roles-rules-sj.md` | Defining RBAC or access control |
| `rules/epic-rules-sj.md` | Writing or scoping Epics |
| `rules/user-story-rules-sj.md` | Writing User Stories |
| `rules/testing-rules-sj.md` | **Writing any test** — project-specific patterns, respx, factory_boy, Celery task testing |
| `rules/ai-ml-rules-sj.md` | Writing LangChain agents, LangGraph workflows, or LLM calls |
| `rules/workflow-rules-sj.md` | Writing n8n webhooks, LangGraph state, or Celery tasks |
| `rules/ui-wireframe-rules-sj.md` | Creating HTML wireframes |
| `docs/functional-landscape/FUNCTIONAL_LANDSCAPE-sj.md` | Understanding system scope |
| `docs/actors/ACTORS-sj.md` | Implementing any role-based logic |
| `docs/wireframes/` | Implementing any Streamlit UI screen |

> **Rule:** If a project-specific (`-sj`) file exists for a topic, it takes precedence over the generic version. Both must be read — the generic provides the base, the project-specific provides the override.

---

## Pre-Code Reading Order

Before writing any code, read in this order:

1. **[CLAUDE-generic.md](best-practices_rule_set_code/CLAUDE-generic.md)** — Generic operating principles, layer architecture, agile workflow
2. **[RULES-generic.md](best-practices_rule_set_code/RULES-generic.md)** — Master engineering rules (non-negotiables, architecture, quality checklist)
3. **[FUNCTIONAL_LANDSCAPE-sj.md](project-specific-guidelines/docs/functional-landscape/FUNCTIONAL_LANDSCAPE-sj.md)** — Complete module inventory, 7 layers, actor–module matrix
4. **[ACTORS-sj.md](project-specific-guidelines/docs/actors/ACTORS-sj.md)** — Actor definitions, roles, permissions, data scoping
5. **[Architecture-sj.md](project-specific-guidelines/Architecture-sj.md)** — Project folder structure, logging strategy, exception hierarchy
6. **[DB_SCHEMA-sj.md](project-specific-guidelines/docs/DB_SCHEMA-sj.md)** — Database schema, enums, migration index
7. **[API_SPEC-sj.md](project-specific-guidelines/docs/API_SPEC-sj.md)** — API endpoints, request/response shapes
7.5. **[docs/wireframes/](project-specific-guidelines/docs/wireframes/)** — HTML wireframe mockups for all UI screens (WF-000 to WF-007)
8. **[testing-rules-generic.md](best-practices_rule_set_code/docs/rules/testing-rules-generic.md)** + **[testing-rules-sj.md](project-specific-guidelines/rules/testing-rules-sj.md)** — TDD workflow, pytest patterns, factory_boy, Celery task testing
9. **Relevant Epic** in `project-specific-guidelines/docs/epics/` — Scope and acceptance criteria
10. **Relevant User Story** in `project-specific-guidelines/docs/stories/` — Behaviour, ACs, DoD

---

## Documentation Index

### Start Here

| Document | Purpose | Link |
|---|---|---|
| **Ideas & Approach** | Solution concepts, tech stack rationale, POC scope | [ideas-sj.md](project-specific-guidelines/ideas-sj.md) |
| **PRD** | Epics, user stories, functional landscape | [PRD-sj.md](project-specific-guidelines/PRD-sj.md) |
| **Execution Plan** | Phase-by-phase SDLC plan with task checklists | [Plan-sj.md](project-specific-guidelines/Plan-sj.md) |
| **Guidelines Compliance** | Which generic rules apply, which have SJ overrides | [GUIDELINES_COMPLIANCE-sj.md](project-specific-guidelines/GUIDELINES_COMPLIANCE-sj.md) |
| **Skills — Generic** | Reusable workflow playbooks (any stack) | [SKILLS-generic.md](best-practices_rule_set_code/SKILLS-generic.md) |
| **Skills — Python** | Python/FastAPI/Celery workflow playbooks | [SKILLS-python.md](best-practices_rule_set_code/skills/SKILLS-python.md) |
| **Skills — Jewelry AI** | SJ-specific workflows + overrides | [SKILLS-sj.md](project-specific-guidelines/SKILLS-sj.md) |

### Architecture & Design

| Document | Purpose | Link |
|---|---|---|
| **Architecture** | Project folder structure, logging, exception hierarchy | [Architecture-sj.md](project-specific-guidelines/Architecture-sj.md) |
| **HLD** | System diagram, deployment diagram, integration flow | [HLD-sj.md](project-specific-guidelines/HLD-sj.md) |
| **LLD** | API endpoints, domain models, LangGraph nodes, Celery tasks | [LLD-sj.md](project-specific-guidelines/LLD-sj.md) |
| **Design Patterns** | Repository, Strategy, Factory, LangGraph State Machine, Adapter | [DesignPatterns-sj.md](project-specific-guidelines/DesignPatterns-sj.md) |

### Living Specifications

| Document | Purpose | Link |
|---|---|---|
| **API Spec** | Full API endpoints with request/response examples | [API_SPEC-sj.md](project-specific-guidelines/docs/API_SPEC-sj.md) |
| **DB Schema** | Complete schema, column types, enums, migration index | [DB_SCHEMA-sj.md](project-specific-guidelines/docs/DB_SCHEMA-sj.md) |
| **UI Wireframes** | HTML mockups for all 7 Streamlit screens with API annotations | [docs/wireframes/](project-specific-guidelines/docs/wireframes/) |

### Discovery & Planning

> **Full workflow:** See [EXECUTION_WORKFLOW-sj.md](project-specific-guidelines/EXECUTION_WORKFLOW-sj.md) for the complete Stage 0–7 sequence.
> **Sequence:** Functional Landscape → Actors → PRD → Architecture → API Spec → **UI Wireframes** → Epics → User Stories → Code

| Document | Layer | Purpose | Link |
|---|---|---|---|
| **Functional Landscape** | Project | 7-layer module inventory, actor–module matrix, out-of-scope | [FUNCTIONAL_LANDSCAPE-sj.md](project-specific-guidelines/docs/functional-landscape/FUNCTIONAL_LANDSCAPE-sj.md) |
| **Actor Index** | Project | All actors, roles, permissions, RBAC rules | [ACTORS-sj.md](project-specific-guidelines/docs/actors/ACTORS-sj.md) |
| **Landscape Rules — Jewelry AI** | Project | Layer definitions, module catalog, Jewelry AI-specific rules | [functional-landscape-rules-sj.md](project-specific-guidelines/rules/functional-landscape-rules-sj.md) |
| **Actor Rules — Jewelry AI** | Project | Actor definitions, role permissions, data scoping | [actor-roles-rules-sj.md](project-specific-guidelines/rules/actor-roles-rules-sj.md) |
| **Epic Rules** | Generic | Anatomy, lifecycle, sizing, INVEST | [epic-rules-generic.md](best-practices_rule_set_code/docs/rules/epic-rules-generic.md) |
| **User Story Rules** | Generic | Format, Three Cs, GWT, splitting | [user-story-rules-generic.md](best-practices_rule_set_code/docs/rules/user-story-rules-generic.md) |
| **Epic Rules — Jewelry AI** | Project | Platform catalog (EPIC-01–15), phases, API deps, DoD | [epic-rules-sj.md](project-specific-guidelines/rules/epic-rules-sj.md) |
| **User Story Rules — Jewelry AI** | Project | Actors, toolchain DoD, AC examples, story paths | [user-story-rules-sj.md](project-specific-guidelines/rules/user-story-rules-sj.md) |

### Standards & Rules

| Document | Purpose | Link |
|---|---|---|
| **Rules (Master)** | All rules index, architecture layers, code quality checklist | [RULES-generic.md](best-practices_rule_set_code/RULES-generic.md) |
| **Coding Standards** | Class boilerplate, docstrings, naming, type hints | [CodingStandards-sj.md](project-specific-guidelines/CodingStandards-sj.md) |
| Coding Style Rules | Immutability, async, file size, nesting | [coding-style-rules-generic.md](best-practices_rule_set_code/docs/rules/coding-style-rules-generic.md) |
| Security Rules | Secrets, validation, auth, rate limiting | [security-python.md](best-practices_rule_set_code/docs/rules/security-python.md) |
| Testing Rules (generic) | TDD, 80% coverage, test organisation, factories | [testing-rules-generic.md](best-practices_rule_set_code/docs/rules/testing-rules-generic.md) |
| Testing Rules (SJ) | Project test stack, Celery/LangGraph patterns, factories | [testing-rules-sj.md](project-specific-guidelines/rules/testing-rules-sj.md) |
| API Design Rules | REST conventions, response format, versioning | [api-design-rules-sj.md](project-specific-guidelines/rules/api-design-rules-sj.md) |
| Data Rules | DB conventions, migrations, soft deletes, pgvector | [data-rules-python.md](best-practices_rule_set_code/docs/rules/data-rules-python.md) |
| Error & Observability | Exception hierarchy, structured logging, correlation IDs, health checks | [error-observability-python.md](best-practices_rule_set_code/docs/rules/error-observability-python.md) |
| DevOps & Deployment | Docker, CI/CD, env validation, Makefile, deployment checklist | [devops-deployment-python.md](best-practices_rule_set_code/docs/rules/devops-deployment-python.md) |
| AI / ML Rules | LangChain, LangGraph, LLM cost, Celery tasks, MLflow | [ai-ml-rules-sj.md](project-specific-guidelines/rules/ai-ml-rules-sj.md) |
| Performance & Caching | Redis patterns, N+1 prevention, rate limiting, connection pooling | [performance-caching-rules-python.md](best-practices_rule_set_code/docs/rules/performance-caching-rules-python.md) |
| Frontend — Streamlit | Thin UI rules, APIClient, session state, caching, error handling | [frontend-streamlit-generic.md](best-practices_rule_set_code/docs/rules/frontend-streamlit-generic.md) |
| Workflow — n8n / LangGraph / Celery | Layer responsibilities, n8n webhook design, LangGraph state, Celery tasks | [workflow-rules-sj.md](project-specific-guidelines/rules/workflow-rules-sj.md) |
| Configuration Management | Pydantic Settings class, feature flags, env file structure, env-specific overrides | [configuration-rules-python.md](best-practices_rule_set_code/docs/rules/configuration-rules-python.md) |
| Synthetic & Demo Data | Demo data rules, `.example.com` domains, seed script structure, test factories | [synthetic-data-rules-sj.md](project-specific-guidelines/rules/synthetic-data-rules-sj.md) |
| **UI Wireframe Rules (generic)** | HTML format, WF-NNN naming, component library, API annotation pattern, DoD | [ui-wireframe-rules-generic.md](best-practices_rule_set_code/docs/rules/ui-wireframe-rules-generic.md) |
| **UI Wireframe Rules (Jewelry AI)** | 7-screen catalog, actor-screen matrix, API field bindings per screen | [ui-wireframe-rules-sj.md](project-specific-guidelines/rules/ui-wireframe-rules-sj.md) |

### POC & Demo

| Document | Purpose | Link |
|---|---|---|
| **POC — Phase 0** | Local demo scope, 15-min demo script, setup instructions, success criteria | [POC-sj.md](project-specific-guidelines/docs/POC-sj.md) |

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

This project is **fully supported on Windows** via Docker Desktop + Git Bash. See [devops-deployment-python.md](best-practices_rule_set_code/docs/rules/devops-deployment-python.md) → *Windows Developer Setup* section for:
- Shell recommendation (Git Bash vs WSL2 vs PowerShell)
- `make` ↔ PowerShell command equivalents
- Virtual environment activation on Windows
- Line ending setup (`.gitattributes` — required first step)
- `pathlib.Path` rule (no hardcoded `/` or `\` separators)
- Cross-platform URL-open pattern (`webbrowser.open()`)

---

## Current Phase

**Phase 0 — Foundation Setup** (see [Plan-sj.md](project-specific-guidelines/Plan-sj.md))

Immediate next steps:
1. `.gitattributes` — line ending enforcement (Windows compatibility)
2. `pyproject.toml` with ruff, mypy, pytest, isort config
3. `docker-compose.yml` with all services
4. `src/core/config.py` — pydantic-settings with startup validation
5. `src/db/session.py` — async SQLAlchemy engine
6. Alembic baseline migration
7. Scaffold complete folder structure per [Architecture-sj.md](project-specific-guidelines/Architecture-sj.md)

---

## Requirements Source

[Requirements/Requirements.txt](Requirements/Requirements.txt)
