# Guidelines Compliance Checklist — Shivam Jewels AI (SJ)

**Purpose:** Confirms which generic and stack-specific rules from `best-practices_rule_set_code/` are applied in this project, where project-specific overrides exist, and which are not applicable.

**How to use:**
- When a new generic rule file is added to `best-practices_rule_set_code/`, add a row here and set status to ❌ until reviewed.
- When a rule is adopted, update status to ✅ and link the SJ override file (if one was created).
- Review this checklist at the start of each increment to confirm compliance.

**Legend:**
| Symbol | Meaning |
|---|---|
| ✅ | Applied — rule is actively followed in this project |
| ✅ (override) | Applied via project-specific override file |
| ⬛ | Not applicable — wrong tech stack for this project |
| ⚠️ | Partially applied — some sections followed, some not |
| ❌ | Not yet reviewed / applied |

---

## Generic Rules (`-generic` suffix)

| Rule File | Status | SJ Override File | Notes |
|---|---|---|---|
| `RULES-generic.md` | ✅ | — | Followed directly; all non-negotiables enforced |
| `DesignPatterns-generic.md` | ✅ (override) | `DesignPatterns-sj.md` | Extended with Jewelry AI concrete examples (LeadIngestionService, ApolloEnrichmentStrategy, LangGraph pipeline) |
| `CLAUDE-generic.md` | ✅ | — | Agile workflow, documentation structure, layer architecture, testing philosophy applied directly |
| `actor-roles-rules-generic.md` | ✅ (override) | `rules/actor-roles-rules-sj.md` | SJ override defines admin/manager/rep roles and RBAC |
| `api-contracts-generic.md` | ✅ (override) | `rules/api-design-rules-sj.md` | REST conventions, response envelope, versioning applied |
| `development-execution-generic.md` | ✅ (override) | `EXECUTION_WORKFLOW-sj.md` | Full Stage 0–7 SDLC workflow defined |
| `epic-rules-generic.md` | ✅ (override) | `rules/epic-rules-sj.md` | SJ override adds 15-epic catalog, delivery phases, API dependency map |
| `frontend-streamlit-generic.md` | ✅ (override) | `rules/ui-wireframe-rules-sj.md` | Thin UI client pattern, APIClient singleton, session state rules applied |
| `functional-landscape-rules-generic.md` | ✅ (override) | `rules/functional-landscape-rules-sj.md` | 7-layer module inventory completed for SJ |
| `testing-rules-generic.md` | ✅ (override) | `rules/testing-rules-sj.md` | SJ override adds Celery task testing, LangGraph testing, respx HTTP mocking, factory_boy factories |
| `testing-quality-generic.md` | ✅ | — | 80% coverage gate, mock rules followed directly |
| `ui-wireframe-rules-generic.md` | ✅ (override) | `rules/ui-wireframe-rules-sj.md` | 7-screen HTML wireframe catalog (WF-000 to WF-007) completed |
| `user-story-rules-generic.md` | ✅ (override) | `rules/user-story-rules-sj.md` | SJ override adds Jewelry AI actors, toolchain DoD, AC examples |

---

## Python Stack Rules (`-python` suffix)

| Rule File | Status | SJ Override File | Notes |
|---|---|---|---|
| `CLAUDE-python.md` | ✅ | — | Python operating principles applied directly |
| `CodingStandards-python.md` | ✅ (override) | `CodingStandards-sj.md` | SJ override adds Jewelry AI class boilerplate, domain naming, enums |
| `coding-style-rules-generic.md` | ✅ | — | Immutability, async patterns, file size limits followed directly |
| `configuration-rules-python.md` | ✅ | — | Pydantic Settings class, env hierarchy, startup validation applied |
| `data-rules-python.md` | ✅ | — | SQLAlchemy async, Alembic migrations, soft deletes, pgvector conventions applied |
| `devops-deployment-python.md` | ✅ | — | Docker Compose, Makefile, CI pipeline, Windows dev setup applied |
| `error-observability-python.md` | ✅ | — | FastAPI exception hierarchy, structured logging, correlation IDs applied |
| `performance-caching-rules-python.md` | ✅ | — | Redis caching, async patterns, N+1 prevention, connection pooling applied |
| `security-python.md` | ✅ | — | FastAPI/Pydantic validation, secrets management, rate limiting applied |
| `ai-ml-rules-sj.md` *(project only)* | ✅ | `rules/ai-ml-rules-sj.md` | LangChain, LangGraph, Celery task rules specific to SJ; no generic equivalent yet |
| `workflow-rules-sj.md` *(project only)* | ✅ | `rules/workflow-rules-sj.md` | n8n, LangGraph, Celery orchestration rules specific to SJ; no generic equivalent yet |
| `synthetic-data-rules-sj.md` *(project only)* | ✅ | `rules/synthetic-data-rules-sj.md` | Demo company names, seed data conventions specific to SJ |

---

## NestJS Stack Rules (`-nestjs` suffix) — Not Applicable to This Project

| Rule File | Status | Notes |
|---|---|---|
| `CLAUDE-nestjs.md` | ⬛ | NestJS/TypeScript project template — Python project uses CLAUDE-python.md |
| `ARCHITECTURE-nestjs.md` | ⬛ | NestJS monorepo structure — Python uses Architecture-sj.md |
| `architecture-nestjs.md` | ⬛ | NestJS controller/service/module architecture |
| `backend-nestjs.md` | ⬛ | NestJS-specific backend patterns |
| `database-nestjs.md` | ⬛ | Knex/Objection.js ORM — Python uses SQLAlchemy/asyncpg |
| `devops-deployment-nestjs.md` | ⬛ | Node.js/PM2 deployment — Python uses uvicorn/Docker |
| `error-observability-nestjs.md` | ⬛ | NestJS exception filters — Python uses FastAPI exception hierarchy |
| `security-nestjs.md` | ⬛ | NestJS guards/decorators — Python uses FastAPI dependencies |

---

## Skills Coverage

| Skill File | Status | SJ Override | Notes |
|---|---|---|---|
| `SKILLS-generic.md` (G-001 to G-009) | ✅ | `SKILLS-sj.md` | SJ-001 extends G-001; SJ domain skills extend G-002/G-005 |
| `SKILLS-python.md` (P-001 to P-007) | ✅ | `SKILLS-sj.md` | Alembic, Celery, respx, factory_boy patterns all applied |

---

## Increment Coverage Tracker

Track which increments have been delivered and confirm rules were followed throughout.

| Increment | Feature | Status | Rules Verified |
|---|---|---|---|
| Increment 0 | Project skeleton, config, health endpoints, CI | ✅ Complete | devops, configuration, error-observability |
| Increment 1 | Lead ingestion — CSV upload, deduplication, Celery task, job polling | ✅ Complete | testing-rules-sj, data-rules, api-contracts |
| Increment 2 | Contact enrichment — Apollo/Hunter clients, service, Celery task, router | ✅ Complete | testing-rules-sj, error-observability, security |
| Increment 3 | Streamlit UI — WF-007 CSV upload, WF-003 lead detail view | ✅ Complete | frontend-streamlit-generic, ui-wireframe-rules-sj |
| Increment 4 | Inventory matching | ❌ Pending | — |
| Increment 5 | AI outreach generation | ❌ Pending | — |
| Increment 6 | Human review queue | ❌ Pending | — |
| Increment 7 | Analytics & reporting | ❌ Pending | — |

---

*Last updated: 2026-03-20*
*Maintained by: Update at the start of each increment and when new generic rules are added to `best-practices_rule_set_code/`.*
