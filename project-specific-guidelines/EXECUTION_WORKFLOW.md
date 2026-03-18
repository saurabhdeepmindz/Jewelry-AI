# Execution Workflow — Jewelry AI Platform

> **Purpose:** The complete, ordered sequence of steps to go from a blank repository to a production-ready platform. Every step produces a named artifact. No step may be skipped — each artifact is a prerequisite for the next stage.
>
> **Framework source:** All generic rules and templates are drawn from `best-practices_rule_set_code/`. Project-specific overrides and artifacts live in `project-specific-guidelines/`. Source code lives in `src/`.

---

## Workflow Overview

```
STAGE 0: Framework Setup      → Read best-practices; create project CLAUDE.md
STAGE 1: Discovery            → Functional Landscape + Actors
STAGE 2: Requirements         → Ideas, PRD
STAGE 3: Architecture         → Architecture, HLD, LLD, DB Schema, API Spec
STAGE 4: Design Patterns      → Design Patterns, Coding Standards
STAGE 5: Agile Planning       → Epics, User Stories
STAGE 6: Development          → Phase 0 → Phase 8 (code + tests)
STAGE 7: Continuous Quality   → Throughout all development phases
```

---

## STAGE 0 — Framework Setup

> **Goal:** Establish the project's rules, conventions, and AI assistant configuration before any discovery or code begins.
> **Input:** `best-practices_rule_set_code/` (generic framework)
> **Output:** Project-specific rules and CLAUDE.md

### Step 0.1 — Read the Generic Framework
**Action:** Review all files in `best-practices_rule_set_code/` to understand reusable rules.

| File to Read | Purpose |
|---|---|
| `best-practices_rule_set_code/CLAUDE-GENERIC.md` | Operating mode, layer architecture, agile workflow template |
| `best-practices_rule_set_code/RULES.md` | Master engineering rules |
| `best-practices_rule_set_code/ARCHITECTURE.md` | Architecture patterns |
| `best-practices_rule_set_code/docs/rules/functional-landscape-rules.md` | How to structure the Functional Landscape |
| `best-practices_rule_set_code/docs/rules/actor-roles-rules.md` | How to define actors and RBAC |
| `best-practices_rule_set_code/docs/rules/epic-rules.md` | How to write epics |
| `best-practices_rule_set_code/docs/rules/user-story-rules.md` | How to write user stories |

**Artifact:** Mental model of all generic standards — no file created yet.

---

### Step 0.2 — Create Project-Specific Rules Files
**Action:** For each generic rules file, create a project-specific override in `project-specific-guidelines/rules/` that extends (not duplicates) the generic version.

| Generic File | Project-Specific Override | Status |
|---|---|---|
| `docs/rules/functional-landscape-rules.md` | `project-specific-guidelines/rules/functional-landscape-rules.md` | ✅ Created |
| `docs/rules/actor-roles-rules.md` | `project-specific-guidelines/rules/actor-roles-rules.md` | ✅ Created |
| `docs/rules/epic-rules.md` | `project-specific-guidelines/rules/epic-rules.md` | ✅ Created |
| `docs/rules/user-story-rules.md` | `project-specific-guidelines/rules/user-story-rules.md` | ✅ Created |

**Artifact:** `project-specific-guidelines/rules/*.md` — project rules files

---

### Step 0.3 — Create the Project-Specific CLAUDE.md
**Action:** Create the root `CLAUDE.md` that references `ai-development-guidelines/CLAUDE-Generic.md` and adds all Jewelry AI-specific context.

**Must include:**
- Reference callout pointing to `CLAUDE-Generic.md`
- Project identity (name, type, stack, purpose)
- Full documentation index with links to all `project-specific-guidelines/` and `ai-development-guidelines/` files
- Domain context (business domain, user roles, entities, business rules, integrations)
- Quick commands (make / PowerShell equivalents)
- Windows developer notes
- Current phase pointer

**Artifact:** `CLAUDE.md` (root) ✅ Created

---

## STAGE 1 — Discovery

> **Goal:** Map the complete functional scope before writing requirements. Understand what the system must do and who uses it.
> **Generic rules:** `best-practices_rule_set_code/docs/rules/functional-landscape-rules.md`, `actor-roles-rules.md`
> **Project rules:** `project-specific-guidelines/rules/functional-landscape-rules.md`, `actor-roles-rules.md`

### Step 1.1 — Create the Functional Landscape
**Action:** Identify all functional layers and their modules using the bottom-to-top structure.

**Layer sequence for Jewelry AI (bottom → top):**
1. Core Data (Lead, Inventory, Contact, Outreach, CRM Activity, User & Config)
2. Integration Services (Apollo, Hunter, Proxycurl, SendGrid, Twilio, n8n, OpenAI, MLflow)
3. Business Services (Ingestion, Matching, Enrichment, Scoring, Outreach Generation)
4. Workflows & Transactions (Lead Pipeline, Outreach Campaign, Enrichment Workflow, CRM Logging)
5. Applications & Portals (Streamlit Dashboard, Admin Panel, Manager Review UI)
6. Reporting & Analytics (Pipeline Funnel, Outreach Performance, Lead Scoring Dashboard, Audit Log)
7. AI / Intelligence (Lead Scoring Agent, Outreach Agent, Match Embedding, Support AI)

**Template:** `best-practices_rule_set_code/docs/rules/functional-landscape-rules.md` → `FUNCTIONAL_LANDSCAPE.md` template
**Artifact:** `project-specific-guidelines/docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md` ✅ Created

---

### Step 1.2 — Define Actors and Roles
**Action:** Identify all actors (human, system, external) from the Functional Landscape. Define role, responsibilities, permissions, and data scope for each.

**Jewelry AI Actors:**

| Actor | Type | Primary Layer |
|---|---|---|
| `admin` | Administrative | All layers — config and monitoring |
| `manager` | Supervisory | Applications, Reporting |
| `rep` | Primary Human | Applications (lead management, outreach) |
| `system` | System Actor | Business Services, Workflows |
| `buyer` | External (future) | Applications (self-service portal — Phase 3+) |

**Template:** `best-practices_rule_set_code/docs/rules/actor-roles-rules.md` → Actor Definition Template
**Artifacts:**
- `project-specific-guidelines/docs/actors/ACTORS.md` ✅ Created (Actor Index)
- `project-specific-guidelines/rules/actor-roles-rules.md` ✅ Created (Jewelry AI RBAC)

---

## STAGE 2 — Requirements

> **Goal:** Articulate what to build, for whom, and why — with prioritised scope.
> **Input:** Functional Landscape + Actors

### Step 2.1 — Create Ideas & Approach Document
**Action:** Document the solution concept, tech stack rationale, and POC scope.

**Must cover:** Problem statement, proposed solution, technology choices with rationale, POC vs full-product scope, key assumptions.

**Artifact:** `project-specific-guidelines/ideas.md` ✅ Created

---

### Step 2.2 — Create the PRD (Product Requirements Document)
**Action:** Write epics, user stories at a summary level, success metrics, and out-of-scope boundaries. Derive epics from Functional Landscape modules.

**Must cover:** Product goals, user personas (from Actor definitions), functional requirements mapped to epics, non-functional requirements, success criteria per phase.

**Artifact:** `ai-development-guidelines/PRD.md` ✅ Created

---

## STAGE 3 — Architecture & Design

> **Goal:** Define the technical blueprint. Every layer and component is named before code is written.
> **Input:** PRD + Functional Landscape

### Step 3.1 — Create Architecture Document
**Action:** Define the project folder structure, layer responsibilities, exception hierarchy, and logging strategy.

**Must cover:** Full `src/` tree, layer responsibilities (router / service / repository), exception class hierarchy, logging format and trace IDs, test organisation.

**Artifact:** `ai-development-guidelines/Architecture.md` ✅ Created

---

### Step 3.2 — Create the High-Level Design (HLD)
**Action:** Draw the system component diagram, deployment diagram, and integration flow.

**Must cover:** Component diagram showing all services, data flow between components, external integration points, deployment topology (Docker Compose / production), infrastructure dependencies.

**Artifact:** `project-specific-guidelines/HLD.md` ✅ Created

---

### Step 3.3 — Create the Low-Level Design (LLD)
**Action:** Define every API endpoint, domain model, LangGraph node, Celery task, and repository method.

**Must cover:** All domain models with field types, all service method signatures, LangGraph state schemas and node sequence, Celery task definitions, repository interfaces.

**Artifact:** `project-specific-guidelines/LLD.md` ✅ Created

---

### Step 3.4 — Create the Database Schema
**Action:** Define all tables, columns, data types, constraints, indexes, enums, and migration index.

**Must cover:** All table definitions in SQL or migration format, pgvector columns and index strategy, soft-delete pattern, audit timestamps, FK relationships, enum types.

**Artifact:** `ai-development-guidelines/docs/DB_SCHEMA.md` ✅ Created

---

### Step 3.5 — Create the API Specification
**Action:** Document all endpoints with request/response shapes and status codes.

**Must cover:** All REST endpoints grouped by domain, request body schemas, response envelope format, error response shapes, authentication headers, pagination patterns.

**Artifact:** `ai-development-guidelines/docs/API_SPEC.md` ✅ Created

---

## STAGE 4 — Design Patterns & Coding Standards

> **Goal:** Lock the implementation patterns before code is written. Prevents ad-hoc decisions mid-sprint.

### Step 4.1 — Define Design Patterns
**Action:** Document the patterns in use across the platform with implementation examples.

**Must cover:** Repository pattern, Strategy pattern (enrichment providers), Factory pattern, LangGraph State Machine, Adapter pattern (integration clients), Event pattern.

**Artifact:** `project-specific-guidelines/DesignPatterns.md` ✅ Created

---

### Step 4.2 — Define Coding Standards
**Action:** Document Python-specific conventions: class boilerplate, docstring format, naming, type hints, async patterns.

**Must cover:** Class structure template, docstring format (Google style), naming conventions for all layer types, async/await rules, import organisation.

**Artifact:** `project-specific-guidelines/CodingStandards.md` ✅ Created

---

## STAGE 5 — Agile Planning

> **Goal:** Decompose the Functional Landscape and PRD into deliverable Epics and then into sprint-ready User Stories.
> **Generic rules:** `best-practices_rule_set_code/docs/rules/epic-rules.md`, `user-story-rules.md`
> **Project rules:** `project-specific-guidelines/rules/epic-rules.md`, `user-story-rules.md`

### Step 5.1 — Create the Epic Catalog
**Action:** For each Functional Landscape module group, create a fully-formed Epic document using the Epic anatomy template.

**Jewelry AI Epics (15 total):**

| Epic ID | Title | From Landscape Layer | Phase |
|---|---|---|---|
| EPIC-01 | Platform Foundation & Infrastructure | All layers (prerequisite) | Phase 0 |
| EPIC-02 | Lead Ingestion & Deduplication | Layer 3 — Business Services | Phase 1 |
| EPIC-03 | AI Inventory Matching Engine | Layer 3 + Layer 7 | Phase 1 |
| EPIC-04 | Contact Enrichment Pipeline | Layer 2 + Layer 3 | Phase 1 |
| EPIC-05 | AI Outreach Generation & Review | Layer 3 + Layer 7 | Phase 1 |
| EPIC-06 | Email Delivery & Tracking | Layer 2 (SendGrid) | Phase 2 |
| EPIC-07 | CRM Activity & Audit Log | Layer 1 + Layer 6 | Phase 2 |
| EPIC-08 | Lead Scoring & Prioritization | Layer 3 + Layer 7 | Phase 2 |
| EPIC-09 | Streamlit Dashboard & UI | Layer 5 | Phase 2 |
| EPIC-10 | n8n Workflow Automation | Layer 4 + Layer 2 | Phase 2 |
| EPIC-11 | Authentication & Role-Based Access | Layer 1 (User & Config) | Phase 2 |
| EPIC-12 | WhatsApp Outreach Channel | Layer 2 (Twilio) | Phase 3 |
| EPIC-13 | MLflow Experiment Tracking | Layer 2 (MLflow) | Phase 3 |
| EPIC-14 | Performance, Caching & Scale | All layers | Phase 4 |
| EPIC-15 | Observability, Monitoring & Alerting | Layer 6 | Phase 4 |

**Per-epic artifact location:** `ai-development-guidelines/epics/EPIC-<ID>-<slug>.md`
**Epic index:** `ai-development-guidelines/epics/EPICS.md`
**Status:** Epic catalog defined ✅ — individual Epic documents to be created per sprint

---

### Step 5.2 — Write User Stories per Epic
**Action:** For each epic being worked in the upcoming sprint, create all child user stories using the User Story format with 3+ GWT acceptance criteria.

**Per-story artifact location:** `ai-development-guidelines/stories/EPIC-<ID>/US-<NNN>-<slug>.md`
**Story index:** `ai-development-guidelines/stories/STORIES.md`
**Status:** Story templates defined ✅ — stories created sprint-by-sprint

**Actor labels to use** (from Step 1.2):
- `admin` — system configuration
- `manager` — approval and oversight
- `rep` — day-to-day lead management
- `system` — automated background processes
- `buyer` — future self-service portal (Phase 3+)

---

## STAGE 6 — Development

> **Gate:** Stages 0–5 must be complete before any `src/` code is written.
> **Every sprint:** Read Epic → read User Stories → write tests (RED) → write code (GREEN) → refactor → PR.

### Phase 0 — Foundation Setup (Week 1–2)

**Goal:** Working dev environment, project skeleton, CI/CD baseline.

| Step | Artifact | Rule Reference |
|---|---|---|
| 0.1 | `.gitattributes` — LF line endings | `rules/devops-deployment.md` |
| 0.2 | `pyproject.toml` — ruff, mypy, pytest, isort | `rules/coding-style-rules.md` |
| 0.3 | `docker-compose.yml` — all services | `rules/devops-deployment.md` |
| 0.4 | `Makefile` — up, migrate, test-cov, check, dev, ui, worker | `rules/devops-deployment.md` |
| 0.5 | `.env.example` — all required vars | `rules/configuration-rules.md` |
| 0.6 | `src/core/config.py` — Pydantic Settings with startup validation | `rules/configuration-rules.md` |
| 0.7 | `src/core/exceptions.py` — exception hierarchy | `rules/error-observability.md` |
| 0.8 | `src/core/logging.py` — structured logging with trace_id | `rules/error-observability.md` |
| 0.9 | `src/db/session.py` — async SQLAlchemy engine | `rules/data-rules.md` |
| 0.10 | Alembic baseline migration | `rules/data-rules.md` |
| 0.11 | Full `src/` folder scaffold (empty `__init__.py` files) | `Architecture.md` |
| 0.12 | `src/main.py` — FastAPI app + health endpoint | `rules/api-design-rules.md` |
| 0.13 | `pre-commit` hooks: ruff, mypy, pytest | `rules/devops-deployment.md` |

**Deliverable:** `docker compose up` starts all services. `GET /health` returns `{"status": "ok"}`.

---

### Phase 1 — Lead Ingestion & Inventory Matching (Week 3–4)
**Epics:** EPIC-02, EPIC-03

| Step | Artifact |
|---|---|
| 1.1 | `src/domain/lead.py` — Lead Pydantic domain model |
| 1.2 | `src/domain/inventory.py` — Inventory Pydantic domain model |
| 1.3 | `src/db/models/lead_model.py`, `inventory_model.py`, `match_model.py` |
| 1.4 | Alembic migration: `create_leads_inventory_matches` |
| 1.5 | `src/repositories/lead_repository.py`, `inventory_repository.py` |
| 1.6 | `src/services/lead_ingestion_service.py` — validate, deduplicate, persist |
| 1.7 | `src/services/inventory_match_service.py` — rule-based matching |
| 1.8 | `src/api/routers/leads.py`, `inventory.py` |
| 1.9 | `src/ui/pages/leads.py`, `inventory.py` — Streamlit |
| 1.10 | Unit + integration tests for all above (80%+ coverage) |

**Deliverable:** CSV upload → leads matched to inventory → Eligible/Not Eligible in Streamlit.

---

### Phase 2 — Contact Enrichment (Week 5–6)
**Epic:** EPIC-04

| Step | Artifact |
|---|---|
| 2.1 | `src/domain/contact.py` |
| 2.2 | `src/integrations/apollo_client.py`, `hunter_client.py`, `proxycurl_client.py` |
| 2.3 | `src/agents/enrichment_agent.py` — LangChain tool-use agent |
| 2.4 | `src/services/enrichment_service.py` — Strategy pattern |
| 2.5 | `src/tasks/enrichment_tasks.py` — Celery async task |
| 2.6 | `src/api/routers/enrichment.py` |
| 2.7 | Alembic migration: `create_contacts` |

**Deliverable:** "Enrich" click → contact name, email, phone populated automatically.

---

### Phase 3 — AI Outreach Generation (Week 7–8)
**Epic:** EPIC-05, EPIC-06

| Step | Artifact |
|---|---|
| 3.1 | `src/domain/outreach.py` |
| 3.2 | `src/integrations/sendgrid_client.py` |
| 3.3 | `src/agents/outreach_agent.py` — LangChain LLM chain |
| 3.4 | `src/services/outreach_service.py` |
| 3.5 | `src/tasks/outreach_tasks.py` — Celery outreach sequence |
| 3.6 | `src/api/routers/outreach.py` |
| 3.7 | `src/ui/pages/outreach.py` — draft review + send |
| 3.8 | SendGrid webhook handler for opens/clicks/replies |

**Deliverable:** Eligible lead → enriched → AI email drafted → reviewed → sent → opens tracked.

---

### Phase 4 — LangGraph Workflow Automation (Week 9–10)
**Epic:** EPIC-10

| Step | Artifact |
|---|---|
| 4.1 | `src/agents/workflows/lead_pipeline.py` — Full LangGraph pipeline |
| 4.2 | `src/agents/workflows/follow_up_workflow.py` — Follow-up state machine |
| 4.3 | `src/core/events.py` — Event bus |
| 4.4 | `src/integrations/n8n_client.py` |
| 4.5 | n8n: 3-step email sequence workflow |
| 4.6 | CRM auto-logging via event handlers (EPIC-07) |
| 4.7 | Auth + RBAC implementation (EPIC-11) |

**Deliverable:** CSV upload → zero clicks → full pipeline auto-runs.

---

### Phase 5 — Lead Scoring ML (Week 11–12)
**Epic:** EPIC-08, EPIC-13

| Step | Artifact |
|---|---|
| 5.1 | `src/ml/lead_scorer.py` — XGBoost model |
| 5.2 | `src/ml/fine_tuning/prepare_dataset.py` |
| 5.3 | MLflow experiment tracking integration |
| 5.4 | Score integration into lead pipeline (post-enrichment) |
| 5.5 | `src/ui/pages/analytics.py` — scoring distribution chart (EPIC-09) |

**Deliverable:** Each lead has a 0–100 score; leads sorted by score in outreach queue.

---

### Phase 6 — Analytics Dashboard & POC Polish (Week 13–14)
**Epic:** EPIC-09, EPIC-15

| Step | Artifact |
|---|---|
| 6.1 | Pipeline funnel chart (Streamlit + Plotly) |
| 6.2 | Outreach performance dashboard |
| 6.3 | Lead source quality comparison |
| 6.4 | End-to-end integration tests |
| 6.5 | Security review (secrets audit, input validation) |
| 6.6 | API docs + README + deployment guide |

**Deliverable:** Complete POC demo-ready with analytics.

---

### Phase 7 — Fine-Tuned Jewelry LLM (Week 15–18)

| Step | Artifact |
|---|---|
| 7.1 | Fine-tuning dataset curation (jewelry trade emails) |
| 7.2 | JSONL training data preparation |
| 7.3 | Fine-tune via OpenAI API or Unsloth |
| 7.4 | MLflow evaluation and A/B test |
| 7.5 | Deploy fine-tuned model to outreach agent |

---

### Phase 8 — Live Scraping & Production Hardening (Week 19–22)
**Epic:** EPIC-14

| Step | Artifact |
|---|---|
| 8.1 | `src/scrapers/gmt_scraper.py`, `trade_book_scraper.py` |
| 8.2 | Celery Beat scheduled scraping |
| 8.3 | WhatsApp outreach via Twilio (EPIC-12) |
| 8.4 | Performance hardening — Redis caching, pgvector optimisation (EPIC-14) |
| 8.5 | Observability: Prometheus metrics, alert rules (EPIC-15) |
| 8.6 | Production Docker hardening |

---

## STAGE 7 — Continuous Quality Gates

Applied throughout all development phases:

| Gate | When | Tool | Standard |
|---|---|---|---|
| Linting | Every file save / pre-commit | `ruff check src tests` | Zero errors |
| Type check | Every file save / pre-commit | `mypy src` | Zero errors |
| Unit tests | After every method written | `pytest tests/unit/` | RED → GREEN |
| Integration tests | After every endpoint added | `pytest tests/integration/` | All pass |
| Coverage | Before every PR | `pytest --cov=src` | ≥80% |
| Security scan | Before every PR | Manual checklist | No secrets, validated inputs |
| Epic DoD | Before closing an epic | Checklist in epic file | All criteria met |
| Story DoD | Before closing a story | Checklist in story file | All ACs confirmed |

---

## Document Inventory

Complete index of all artifacts and their locations:

| Artifact | Location | Status |
|---|---|---|
| Generic framework rules | `best-practices_rule_set_code/` | ✅ |
| Generic CLAUDE template | `best-practices_rule_set_code/CLAUDE-GENERIC.md` | ✅ |
| Generic operating principles | `ai-development-guidelines/CLAUDE-Generic.md` | ✅ |
| **Project CLAUDE.md** | `CLAUDE.md` (root) | ✅ |
| **Functional Landscape** | `project-specific-guidelines/docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md` | ✅ |
| **Actor Index** | `project-specific-guidelines/docs/actors/ACTORS.md` | ✅ |
| Ideas & Approach | `project-specific-guidelines/ideas.md` | ✅ |
| PRD | `ai-development-guidelines/PRD.md` | ✅ |
| Architecture | `ai-development-guidelines/Architecture.md` | ✅ |
| HLD | `project-specific-guidelines/HLD.md` | ✅ |
| LLD | `project-specific-guidelines/LLD.md` | ✅ |
| DB Schema | `ai-development-guidelines/docs/DB_SCHEMA.md` | ✅ |
| API Spec | `ai-development-guidelines/docs/API_SPEC.md` | ✅ |
| Design Patterns | `project-specific-guidelines/DesignPatterns.md` | ✅ |
| Coding Standards | `project-specific-guidelines/CodingStandards.md` | ✅ |
| Epic catalog (summary) | `project-specific-guidelines/rules/epic-rules.md` | ✅ |
| Epic documents (individual) | `ai-development-guidelines/epics/EPIC-<ID>-*.md` | ⬜ Per sprint |
| User story documents | `ai-development-guidelines/stories/EPIC-<ID>/US-*.md` | ⬜ Per sprint |
| Execution Workflow | `project-specific-guidelines/EXECUTION_WORKFLOW.md` | ✅ |
| Development Plan | `project-specific-guidelines/Plan.md` | ✅ |
