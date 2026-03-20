# Epic Rules — Jewelry AI Platform (Project-Specific)

> **Extends:** `ai-development-guidelines/rules/epic-rules.md` (generic epic rules)
> **Purpose:** Project-specific overrides, platform epic catalog, and Jewelry AI delivery phases.
> **Sequence:** Epics are created BEFORE any development begins. User stories are created after each Epic.

---

## Project Context

**Platform:** Jewelry AI Lead Automation — Shivam Jewels
**Stack:** FastAPI · LangChain · LangGraph · PostgreSQL + pgvector · Redis · Celery · n8n · Streamlit
**PRD Reference:** `ai-development-guidelines/PRD.md`
**Execution Plan Reference:** `ai-development-guidelines/Plan.md`

---

## Delivery Phases (Jewelry AI)

Map every epic to exactly one phase:

| Phase | Name | Description |
|---|---|---|
| **Phase 0** | Foundation | Infrastructure, Docker, config, scaffolding, CI/CD |
| **Phase 1** | POC | End-to-end demo flow: ingest → match → enrich → outreach |
| **Phase 2** | Alpha | Core features complete, internal users, CRM, dashboard |
| **Phase 3** | Beta | External users, WhatsApp channel, ML tracking, hardening |
| **Phase 4** | GA | Production scale, observability, caching, performance |

---

## Epic Anatomy — Project-Specific Additions

Use the standard anatomy from `ai-development-guidelines/rules/epic-rules.md`, plus the following project-specific guidance:

### Business Goal
Answer: **"What does Shivam Jewels gain when this epic is done?"**

Good: *"Sales reps can view AI-matched inventory suggestions for each lead without any manual SQL queries."*
Bad: *"Build a matching service."*

### Dependencies — External APIs to Call Out Explicitly

| External Dependency | Epic(s) Affected | Notes |
|---|---|---|
| Apollo.io API key | EPIC-04 | Enrichment cannot start without valid key |
| Hunter.io API key | EPIC-04 | Email verification blocked without key |
| Proxycurl API key | EPIC-04 | LinkedIn enrichment blocked without key |
| SendGrid API key | EPIC-06 | Email delivery blocked without key |
| OpenAI API key | EPIC-03, EPIC-05 | Matching embeddings and outreach generation |
| Twilio credentials | EPIC-12 | WhatsApp channel blocked without credentials |
| n8n webhook URL | EPIC-10 | Workflow triggers blocked until n8n is running |

### Definition of Done — Project-Specific DoD
In addition to the generic DoD, every Jewelry AI epic must also meet:

- [ ] All child user stories are completed and accepted
- [ ] Acceptance criteria met and verified
- [ ] `ruff check src tests` passes with zero errors
- [ ] `mypy src` passes with zero errors
- [ ] `pytest --cov=src --cov-report=term-missing` reports ≥ 80% coverage
- [ ] Alembic migration created for any schema change
- [ ] `ai-development-guidelines/docs/API_SPEC.md` updated if new endpoints added
- [ ] `ai-development-guidelines/docs/DB_SCHEMA.md` updated if schema changed
- [ ] Feature deployed to local Docker stack and smoke-tested via Streamlit or Swagger UI

---

## File Location & Naming (Jewelry AI)

- Store epic documents in: `ai-development-guidelines/epics/`
- File name pattern: `EPIC-<ID>-<slug>.md`
  - Example: `EPIC-01-platform-foundation.md`
  - Example: `EPIC-03-inventory-matching-engine.md`
- Maintain index: `ai-development-guidelines/epics/EPICS.md`

---

## Platform Epic Catalog

The following epics are derived from `ai-development-guidelines/PRD.md`. Create a detailed Epic document for each (using the anatomy above) in `ai-development-guidelines/epics/` before beginning the corresponding phase.

| Epic ID | Title | Phase | Priority | Status |
|---|---|---|---|---|
| EPIC-01 | Platform Foundation & Infrastructure | Phase 0 | Critical | Draft |
| EPIC-02 | Lead Ingestion & Deduplication | Phase 1 | Critical | Draft |
| EPIC-03 | AI Inventory Matching Engine | Phase 1 | Critical | Draft |
| EPIC-04 | Contact Enrichment Pipeline | Phase 1 | High | Draft |
| EPIC-05 | AI Outreach Generation & Review | Phase 1 | High | Draft |
| EPIC-06 | Email Delivery & Tracking | Phase 2 | High | Draft |
| EPIC-07 | CRM Activity & Audit Log | Phase 2 | Medium | Draft |
| EPIC-08 | Lead Scoring & Prioritization | Phase 2 | High | Draft |
| EPIC-09 | Streamlit Dashboard & UI | Phase 2 | Medium | Draft |
| EPIC-10 | n8n Workflow Automation | Phase 2 | Medium | Draft |
| EPIC-11 | Authentication & Role-Based Access | Phase 2 | Critical | Draft |
| EPIC-12 | WhatsApp Outreach Channel (Twilio) | Phase 3 | Medium | Draft |
| EPIC-13 | MLflow Experiment Tracking & Model Registry | Phase 3 | Low | Draft |
| EPIC-14 | Performance, Caching & Scale Hardening | Phase 4 | Medium | Draft |
| EPIC-15 | Observability, Monitoring & Alerting | Phase 4 | High | Draft |

---

## Rules Summary (Project-Specific Additions)

In addition to the non-negotiables in `ai-development-guidelines/rules/epic-rules.md`:

- **PRD-aligned:** Every epic must trace to `ai-development-guidelines/PRD.md` — no feature without a PRD reference
- **API/External flag:** If an epic depends on an external API credential, this must be listed in the Dependencies table before sprint planning
- **Phase-locked:** Epics in Phase N may not be started until all Critical epics in Phase N-1 are Done
- **Tool-specific DoD:** All epics must meet the project-specific DoD checklist above (ruff, mypy, pytest, alembic)
