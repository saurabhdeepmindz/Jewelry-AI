# Jewelry AI — Usecase 1: Lead Automation Platform

**Usecase:** `usecase1` — Diamond & Jewelry Wholesale Lead Automation
**Type:** Python AI Platform (FastAPI + LangChain + LangGraph + Streamlit)
**Stack:** Python 3.11+, FastAPI, LangChain, LangGraph, PostgreSQL + pgvector, Redis, Celery, n8n, Streamlit
**Purpose:** Automates the full lead lifecycle for Shivam Jewels — from raw trade directory data to enriched, scored, and AI-outreached buyer relationships, with zero manual data entry.

> **Generic operating principles are defined in:**
> **[../../best-practices_rule_set_code/CLAUDE-GENERIC.md](../../best-practices_rule_set_code/CLAUDE-GENERIC.md)**
> Read that file first. This file adds usecase1-specific context on top of it.

---

## Execution Workflow

This usecase follows the 7-stage execution workflow:

```
STAGE 0: Framework Setup      ✅ COMPLETE — this file + rules/
STAGE 1: Discovery            ⬜ docs/functional-landscape/ + docs/actors/
STAGE 2: Requirements         ⬜ docs/requirements/ideas.md + PRD.md
STAGE 3: Architecture         ⬜ docs/architecture/
STAGE 4: Design Patterns      ⬜ docs/design/
STAGE 5: Agile Planning       ⬜ agile/epics/ + agile/stories/
STAGE 6: Development          ⬜ src/
STAGE 7: Continuous Quality   ⬜ Throughout development
```

> **Full workflow details:** [../../best-practices_rule_set_code/docs/rules/](../../best-practices_rule_set_code/docs/rules/)

---

## MANDATORY: Rule Folders — Read Before Any Work

Both rule folders MUST be read before writing any code, test, migration, or artifact. These folders contain the authoritative standards that govern all development in this project.

### `../../best-practices_rule_set_code/` — Generic Engineering Rules

| File | Must Read Before |
|---|---|
| [CLAUDE-GENERIC.md](../../best-practices_rule_set_code/CLAUDE-GENERIC.md) | Starting any work in this project |
| [RULES.md](../../best-practices_rule_set_code/RULES.md) | Writing any code or making architectural decisions |
| [docs/rules/development-execution.md](../../best-practices_rule_set_code/docs/rules/development-execution.md) | Starting any increment (N.1–N.8 anatomy) |
| [docs/rules/testing-rules.md](../../best-practices_rule_set_code/docs/rules/testing-rules.md) | Writing any test (respx, factory_boy, coverage gate) |
| [docs/rules/testing-quality.md](../../best-practices_rule_set_code/docs/rules/testing-quality.md) | Writing any test (quality standards, DoD gate) |
| [docs/rules/api-contracts.md](../../best-practices_rule_set_code/docs/rules/api-contracts.md) | Designing or modifying any API endpoint |
| [docs/rules/coding-style-rules.md](../../best-practices_rule_set_code/docs/rules/coding-style-rules.md) | Writing any source code |
| [docs/rules/security-rules.md](../../best-practices_rule_set_code/docs/rules/security-rules.md) | Before any commit touching auth, secrets, or user input |
| [docs/rules/data-rules.md](../../best-practices_rule_set_code/docs/rules/data-rules.md) | Designing schema, writing migrations, or ORM models |
| [docs/rules/error-observability.md](../../best-practices_rule_set_code/docs/rules/error-observability.md) | Adding exceptions, logging, or health checks |
| [docs/rules/devops-deployment.md](../../best-practices_rule_set_code/docs/rules/devops-deployment.md) | Modifying Docker, CI/CD, Makefile, or env config |
| [docs/rules/ai-ml-rules.md](../../best-practices_rule_set_code/docs/rules/ai-ml-rules.md) | Writing LangChain, LangGraph, Celery, or ML code |
| [docs/rules/performance-caching-rules.md](../../best-practices_rule_set_code/docs/rules/performance-caching-rules.md) | Adding Redis, caching, or query optimization |
| [docs/rules/frontend-streamlit-rules.md](../../best-practices_rule_set_code/docs/rules/frontend-streamlit-rules.md) | Writing any Streamlit UI code |
| [docs/rules/workflow-rules.md](../../best-practices_rule_set_code/docs/rules/workflow-rules.md) | Writing n8n, LangGraph, or Celery workflow code |
| [docs/rules/configuration-rules.md](../../best-practices_rule_set_code/docs/rules/configuration-rules.md) | Changing settings, env vars, or Pydantic Settings |
| [docs/rules/synthetic-data-rules.md](../../best-practices_rule_set_code/docs/rules/synthetic-data-rules.md) | Creating seed scripts, factories, or demo data |
| [docs/rules/functional-landscape-rules.md](../../best-practices_rule_set_code/docs/rules/functional-landscape-rules.md) | Creating or modifying the functional landscape |
| [docs/rules/actor-roles-rules.md](../../best-practices_rule_set_code/docs/rules/actor-roles-rules.md) | Defining actors, roles, or RBAC permissions |
| [docs/rules/epic-rules.md](../../best-practices_rule_set_code/docs/rules/epic-rules.md) | Writing epics or planning features |
| [docs/rules/user-story-rules.md](../../best-practices_rule_set_code/docs/rules/user-story-rules.md) | Writing user stories or acceptance criteria |
| [docs/rules/api-design-rules.md](../../best-practices_rule_set_code/docs/rules/api-design-rules.md) | Designing REST API endpoints and response shapes |
| [docs/rules/ui-wireframe-rules.md](../../best-practices_rule_set_code/docs/rules/ui-wireframe-rules.md) | Creating UI wireframes or mockups |

### `../../project-specific-guidelines/` — Jewelry AI Project Rules

| File | Must Read Before |
|---|---|
| [EXECUTION_WORKFLOW.md](../../project-specific-guidelines/EXECUTION_WORKFLOW.md) | Starting any stage or increment |
| [rules/functional-landscape-rules.md](../../project-specific-guidelines/rules/functional-landscape-rules.md) | Creating functional landscape artifacts |
| [rules/actor-roles-rules.md](../../project-specific-guidelines/rules/actor-roles-rules.md) | Defining actors or RBAC for Jewelry AI |
| [rules/epic-rules.md](../../project-specific-guidelines/rules/epic-rules.md) | Writing epics (EPIC-01 to EPIC-15) |
| [rules/user-story-rules.md](../../project-specific-guidelines/rules/user-story-rules.md) | Writing user stories for any epic |
| [rules/testing-rules.md](../../project-specific-guidelines/rules/testing-rules.md) | Writing tests — per-epic test index, respx, factory_boy |
| [docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md](../../project-specific-guidelines/docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md) | Understanding module inventory before any increment |
| [docs/actors/ACTORS.md](../../project-specific-guidelines/docs/actors/ACTORS.md) | Understanding actor permissions before any feature |

### `rules/` — Usecase1 Local Rules (Extend Project-Specific)

| File | Must Read Before |
|---|---|
| [rules/functional-landscape-rules.md](rules/functional-landscape-rules.md) | Stage 1 artifacts |
| [rules/actor-roles-rules.md](rules/actor-roles-rules.md) | Stage 1 actor definitions |
| [rules/epic-rules.md](rules/epic-rules.md) | Stage 5 epic planning |
| [rules/user-story-rules.md](rules/user-story-rules.md) | Stage 5 story writing |
| [rules/testing-rules.md](rules/testing-rules.md) | Every test file — local pytest patterns, factory_boy, mocking |

---

## Pre-Code Reading Order

Before writing any code, read in this order:

1. **[../../best-practices_rule_set_code/CLAUDE-GENERIC.md](../../best-practices_rule_set_code/CLAUDE-GENERIC.md)** — Generic operating principles
2. **[../../best-practices_rule_set_code/RULES.md](../../best-practices_rule_set_code/RULES.md)** — Master engineering rules
3. **[../../best-practices_rule_set_code/docs/rules/development-execution.md](../../best-practices_rule_set_code/docs/rules/development-execution.md)** — Increment anatomy (N.1 Domain → N.8 UI)
4. **[../../best-practices_rule_set_code/docs/rules/testing-rules.md](../../best-practices_rule_set_code/docs/rules/testing-rules.md)** — respx, factory_boy, coverage gate, DoD
5. **[../../project-specific-guidelines/EXECUTION_WORKFLOW.md](../../project-specific-guidelines/EXECUTION_WORKFLOW.md)** — Stage 0–7 sequence for Jewelry AI
6. **[../../project-specific-guidelines/rules/testing-rules.md](../../project-specific-guidelines/rules/testing-rules.md)** — Per-epic test file index, project-specific patterns
7. **[docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md](docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md)** — Module inventory, 7 layers, actor–module matrix *(Stage 1)*
8. **[docs/actors/ACTORS.md](docs/actors/ACTORS.md)** — Actor definitions, roles, permissions, data scoping *(Stage 1)*
9. **[docs/architecture/Architecture.md](docs/architecture/Architecture.md)** — Project folder structure, logging, exception hierarchy *(Stage 3)*
10. **[docs/architecture/DB_SCHEMA.md](docs/architecture/DB_SCHEMA.md)** — Database schema, enums, migration index *(Stage 3)*
11. **[docs/architecture/API_SPEC.md](docs/architecture/API_SPEC.md)** — API endpoints, request/response shapes *(Stage 3)*
12. **[rules/testing-rules.md](rules/testing-rules.md)** — Local pytest patterns, factory_boy, mocking, coverage gate *(Stage 0)*
13. **Relevant Epic** in `agile/epics/` — Scope and acceptance criteria *(Stage 5)*
14. **Relevant User Story** in `agile/stories/` — Behaviour, ACs, DoD *(Stage 5)*

---

## Folder Structure

```
ProjectImplementation/usecase1/
│
├── CLAUDE.md                              ← You are here (Stage 0)
│
├── rules/                                 ← Stage 0: Project-specific rules
│   ├── functional-landscape-rules.md      ← Extends best-practices generic
│   ├── actor-roles-rules.md               ← Extends best-practices generic
│   ├── epic-rules.md                      ← Extends best-practices generic
│   ├── user-story-rules.md                ← Extends best-practices generic
│   └── testing-rules.md                   ← Extends best-practices generic (pytest, factory_boy, per-epic test index)
│
├── docs/                                  ← Stage 1–4 artifacts
│   ├── functional-landscape/
│   │   └── FUNCTIONAL_LANDSCAPE.md        ← Stage 1.1
│   ├── actors/
│   │   └── ACTORS.md                      ← Stage 1.2
│   ├── requirements/
│   │   ├── ideas.md                       ← Stage 2.1
│   │   └── PRD.md                         ← Stage 2.2
│   ├── architecture/
│   │   ├── Architecture.md                ← Stage 3.1
│   │   ├── HLD.md                         ← Stage 3.2
│   │   ├── LLD.md                         ← Stage 3.3
│   │   ├── DB_SCHEMA.md                   ← Stage 3.4
│   │   └── API_SPEC.md                    ← Stage 3.5
│   └── design/
│       ├── DesignPatterns.md              ← Stage 4.1
│       └── CodingStandards.md             ← Stage 4.2
│
├── agile/                                 ← Stage 5 artifacts
│   ├── epics/                             ← EPIC-01.md … EPIC-15.md
│   └── stories/                           ← EPIC-01/US-001.md …
│
└── src/                                   ← Stage 6: Source code
    ├── core/
    ├── db/
    ├── domain/
    ├── repositories/
    ├── services/
    ├── agents/
    ├── integrations/
    ├── tasks/
    ├── ml/
    ├── api/
    └── ui/
```

---

## Business Context (from Requirements)

### As-Is Process (Manual)
1. Collect raw company/buyer data from: GMTs, Jewelry Book of Trade, Hill Lists, Rapid Lists
2. Import and check if lead matches current diamond inventory (RBC, specific carat ranges)
3. If inventory match found → lead marked 'Eligible'
4. Manually search LinkedIn for key contacts (name, designation, email, phone)
5. Find physical/mailing address for postal outreach
6. Initiate outreach via email campaigns and/or phone calls
7. Manually log all contact details, outreach activity, and responses into CRM

### To-Be Process (Automated — this platform)
- Scheduled scraping from GMTs, Trade directories, Rapid APIs
- Auto inventory-match engine → Eligible / Not Eligible flag
- Contact enrichment via Apollo.io / Hunter.io / LinkedIn API
- Automated email + WhatsApp outreach sequences
- Auto-logging of all leads and responses to CRM
- Lead scoring based on match quality and past engagement

### After Automation
- 1 lead processed in minutes (vs hours manually)
- Standardized, enriched data every time
- Outreach within hours of lead identification
- CRM always up-to-date, zero manual entry

---

## Domain Entities

| Entity | Description | Key Relations |
|---|---|---|
| `Lead` | A jewelry buyer prospect (company) | Has contacts, matches, outreach messages |
| `Inventory` | A diamond/jewelry item in Shivam's stock | Matched to leads |
| `Contact` | Enriched buyer contact at a lead company | Belongs to lead |
| `OutreachMessage` | AI-generated email or WhatsApp message | Belongs to lead + contact |
| `CRMActivity` | Immutable audit event log entry | Belongs to lead |

---

## User Roles

| Role | Description | Key Permissions |
|---|---|---|
| `admin` | System administrator | Full platform access, config management |
| `manager` | Sales manager | View all leads, approve outreach, configure rules |
| `rep` | Sales representative | View assigned leads, manage own outreach |
| `system` | Automated processes | Pipeline execution, enrichment, CRM logging |

---

## Key Business Rules

- A lead is only eligible for outreach if it matches at least one available inventory item
- Outreach requires human review before sending (configurable via `HUMAN_REVIEW_REQUIRED`)
- Enrichment API credits are finite — cache all results; never re-enrich an already-enriched lead
- CRM activity is append-only and immutable — never update or delete `crm_activity` rows
- Diamond carat weights follow GIA grading standards — always 2 decimal places

---

## External Integrations

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

## Stage 0 Rules Index

| Rule File | Extends | Purpose |
|---|---|---|
| [rules/functional-landscape-rules.md](rules/functional-landscape-rules.md) | `best-practices_rule_set_code/docs/rules/functional-landscape-rules.md` | 7-layer module catalog, actor–module matrix |
| [rules/actor-roles-rules.md](rules/actor-roles-rules.md) | `best-practices_rule_set_code/docs/rules/actor-roles-rules.md` | 5 actors, RBAC, data scoping rules |
| [rules/epic-rules.md](rules/epic-rules.md) | `best-practices_rule_set_code/docs/rules/epic-rules.md` | 15-epic catalog, phases, DoD |
| [rules/user-story-rules.md](rules/user-story-rules.md) | `best-practices_rule_set_code/docs/rules/user-story-rules.md` | Actor labels, toolchain DoD, AC examples |
| [rules/testing-rules.md](rules/testing-rules.md) | `best-practices_rule_set_code/docs/rules/testing-rules.md` | pytest patterns, factory_boy, mocking, 80% coverage gate, per-epic test file index |
