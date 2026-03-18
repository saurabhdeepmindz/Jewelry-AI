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

## Pre-Code Reading Order

Before writing any code, read in this order:

1. **[../../best-practices_rule_set_code/CLAUDE-GENERIC.md](../../best-practices_rule_set_code/CLAUDE-GENERIC.md)** — Generic operating principles
2. **[../../best-practices_rule_set_code/RULES.md](../../best-practices_rule_set_code/RULES.md)** — Master engineering rules
3. **[docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md](docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md)** — Module inventory, 7 layers, actor–module matrix *(Stage 1)*
4. **[docs/actors/ACTORS.md](docs/actors/ACTORS.md)** — Actor definitions, roles, permissions, data scoping *(Stage 1)*
5. **[docs/architecture/Architecture.md](docs/architecture/Architecture.md)** — Project folder structure, logging, exception hierarchy *(Stage 3)*
6. **[docs/architecture/DB_SCHEMA.md](docs/architecture/DB_SCHEMA.md)** — Database schema, enums, migration index *(Stage 3)*
7. **[docs/architecture/API_SPEC.md](docs/architecture/API_SPEC.md)** — API endpoints, request/response shapes *(Stage 3)*
8. **[rules/testing-rules.md](rules/testing-rules.md)** — Unit/integration test patterns, factory_boy, mocking, coverage gate *(Stage 0)*
9. **Relevant Epic** in `agile/epics/` — Scope and acceptance criteria *(Stage 5)*
10. **Relevant User Story** in `agile/stories/` — Behaviour, ACs, DoD *(Stage 5)*

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
