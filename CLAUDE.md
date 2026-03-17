# Jewelry AI — Claude Code Project Guide

**Name:** `jewelry-ai`
**Type:** Python AI Platform (FastAPI + LangChain + LangGraph + Streamlit)
**Stack:** Python 3.11+, FastAPI, LangChain, LangGraph, PostgreSQL + pgvector, Redis, Celery, n8n, Streamlit
**Purpose:** AI-powered lead automation platform for Shivam Jewels — transforms raw trade lists into enriched, scored, and outreached buyer relationships with zero manual intervention.

---

## How to Use This Repo

Before writing any code, read in this order:

1. **[Rules.md](ai-development-guidelines/Rules.md)** — Master engineering rules (non-negotiables, layer architecture, checklist)
2. **[Architecture.md](ai-development-guidelines/Architecture.md)** — Project structure, logging strategy, exception hierarchy
3. **[docs/DB_SCHEMA.md](ai-development-guidelines/docs/DB_SCHEMA.md)** — Database schema, enums, migration index
4. **[docs/API_SPEC.md](ai-development-guidelines/docs/API_SPEC.md)** — API endpoints, request/response shapes

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

---

## Operating Mode

You are the **principal architect and senior engineer** for this repository.

- Extend existing patterns before introducing new ones
- Respect the layer architecture: `routers → services → repositories → DB models`
- AI orchestration lives in `src/agents/` — never call LLM APIs directly in services
- Background jobs go in `src/tasks/` — never fire-and-forget in FastAPI handlers
- Keep files focused: 200–400 lines typical, 800 lines maximum
- Write tests BEFORE implementation (TDD mandatory)
- Run `ruff`, `mypy`, and `pytest` after every change
- Check `Rules.md` before introducing any new module, service, or migration
- When a domain-specific rules file exists (e.g., `rules/ai-ml-rules.md`), follow it precisely

---

## Quick Commands

```bash
# Start all services (Docker Compose)
make up

# Run database migrations
make migrate

# Run tests with coverage
make test-cov

# Lint + type check + test (full check before PR)
make check

# Create new Alembic migration
make migrate-new name="add_score_to_leads"

# Start FastAPI dev server (hot reload)
make dev

# Start Streamlit UI
make ui

# Start Celery worker
make worker
```

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

## Current Phase

**Phase 0 — Foundation Setup** (see [Plan.md](ai-development-guidelines/Plan.md))

Immediate next steps:
1. `pyproject.toml` with ruff, mypy, pytest, isort config
2. `docker-compose.yml` with all services
3. `src/core/config.py` — pydantic-settings with startup validation
4. `src/db/session.py` — async SQLAlchemy engine
5. Alembic baseline migration
6. Scaffold complete folder structure per [Architecture.md](ai-development-guidelines/Architecture.md)

---

## Requirements Source

[Requirements/Requirements.txt](Requirements/Requirements.txt)
