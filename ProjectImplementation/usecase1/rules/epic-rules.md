# Epic Rules — Usecase 1: Jewelry AI Lead Automation

> **Extends:** `best-practices_rule_set_code/docs/rules/epic-rules.md` (generic rules)
> **Purpose:** Defines the 15-epic catalog for the Jewelry AI platform, delivery phases, external API dependencies, and project Definition of Done.
> **Artifact to produce:** Individual Epic files in `agile/epics/EPIC-<ID>-<slug>.md`

---

## Epic Catalog

| Epic ID | Title | Functional Layer(s) | Delivery Phase |
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

---

## Delivery Phases

| Phase | Epics | Goal | Weeks |
|---|---|---|---|
| Phase 0 | EPIC-01 | Working dev environment, project skeleton, CI/CD baseline | 1–2 |
| Phase 1 | EPIC-02, EPIC-03, EPIC-04, EPIC-05 | Core pipeline: ingest → match → enrich → AI outreach draft | 3–8 |
| Phase 2 | EPIC-06, EPIC-07, EPIC-08, EPIC-09, EPIC-10, EPIC-11 | Full automation + dashboard + auth | 9–14 |
| Phase 3 | EPIC-12, EPIC-13 | WhatsApp + ML experiment tracking | 15–18 |
| Phase 4 | EPIC-14, EPIC-15 | Production hardening + observability | 19–22 |

---

## External API Dependencies per Epic

| Epic | Required External APIs | Notes |
|---|---|---|
| EPIC-03 | OpenAI Embeddings API | pgvector semantic matching |
| EPIC-04 | Apollo.io, Hunter.io, Proxycurl | Enrichment cascade; all require API keys |
| EPIC-05 | OpenAI GPT-4o or Anthropic Claude | Outreach generation; fallback supported |
| EPIC-06 | SendGrid API v3 | Email send + open/click/bounce webhooks |
| EPIC-10 | n8n (self-hosted) | Multi-step sequence trigger |
| EPIC-12 | Twilio Conversations API | WhatsApp outreach channel |
| EPIC-13 | MLflow (self-hosted) | Experiment runs, model registry |

> **Rule:** No epic that depends on an external API may be marked Done until the API integration is tested end-to-end (not just mocked) in at least the staging environment.

---

## Epic Anatomy (required per Epic file)

Every Epic document in `agile/epics/` MUST contain:

```markdown
# EPIC-<ID>: <Title>

**Status:** Draft | Ready | In Progress | Done
**Phase:** Phase <N>
**Layer(s):** Layer <N> — <Name>
**Priority:** Critical | High | Medium | Low
**Estimated Size:** XL | L | M | S | XS

## Problem Statement
<Why this epic exists — business problem being solved>

## Goal
<What success looks like at epic completion — measurable outcome>

## Scope (In)
- <Feature or capability included>

## Scope (Out)
- <Explicitly excluded — prevents scope creep>

## Acceptance Criteria
- [ ] AC1: <Given/When/Then or clear measurable criterion>
- [ ] AC2:
- [ ] AC3:

## User Stories
- US-<NNN>: <story title> — `agile/stories/EPIC-<ID>/US-<NNN>-<slug>.md`

## External API Dependencies
| API | Purpose | Credential Required |
|---|---|---|

## Definition of Done
- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] Alembic migrations applied cleanly
- [ ] API endpoints documented and tested via Postman/OpenAPI
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
```

---

## Project Definition of Done (All Epics)

In addition to the generic DoD from `best-practices_rule_set_code/docs/rules/epic-rules.md`:

| Gate | Tool | Standard |
|---|---|---|
| Linting | `ruff check src tests` | Zero errors |
| Type checking | `mypy src` | Zero errors |
| Unit tests | `pytest tests/unit/` | RED → GREEN, all pass |
| Integration tests | `pytest tests/integration/` | All pass |
| Coverage | `pytest --cov=src` | ≥ 80% |
| DB migrations | `alembic upgrade head` | Applies cleanly with no errors |
| Security | Manual checklist | No secrets in code, all inputs validated |
| API contract | OpenAPI docs | All endpoints documented |
| PR review | Git | Squash-merge to `master` |

---

## Epic File Naming Convention

```
agile/epics/EPIC-01-platform-foundation.md
agile/epics/EPIC-02-lead-ingestion.md
agile/epics/EPIC-03-inventory-matching.md
agile/epics/EPIC-04-contact-enrichment.md
agile/epics/EPIC-05-outreach-generation.md
agile/epics/EPIC-06-email-delivery.md
agile/epics/EPIC-07-crm-activity-log.md
agile/epics/EPIC-08-lead-scoring.md
agile/epics/EPIC-09-streamlit-dashboard.md
agile/epics/EPIC-10-workflow-automation.md
agile/epics/EPIC-11-auth-rbac.md
agile/epics/EPIC-12-whatsapp-outreach.md
agile/epics/EPIC-13-mlflow-tracking.md
agile/epics/EPIC-14-performance-caching.md
agile/epics/EPIC-15-observability.md
```
