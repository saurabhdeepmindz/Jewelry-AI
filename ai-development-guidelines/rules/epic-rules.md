# Epic Rules — Jewelry AI Platform

> **Source:** Atlassian Agile — Epics (https://www.atlassian.com/agile/project-management/epics)
> **Sequence:** Epics are created BEFORE any development begins. User stories are created after each Epic.

---

## What Is an Epic?

An **Epic** is a large body of work that can be broken down into smaller, deliverable user stories. Epics represent a significant chunk of business value that typically spans multiple sprints and may cross team boundaries.

- An epic is NOT a project — it is a scoped initiative within a project
- An epic is NOT a sprint — it spans multiple sprints
- An epic IS the parent of user stories — stories are the children that deliver the epic

**Rule:** Every feature, module, or initiative in the Jewelry AI platform MUST be represented as an Epic before any user stories or code are written.

---

## Epic Anatomy

Every epic in this project must have the following structure:

```markdown
## EPIC-<ID>: <Title>

**Status:** Draft | Active | In Progress | Done | Cancelled
**Owner:** <role or team member>
**Priority:** Critical | High | Medium | Low
**Phase:** Phase 0 — Foundation | Phase 1 — POC | Phase 2 — Alpha | Phase 3 — Beta | Phase 4 — GA
**Sprint Target:** <sprint range, e.g., Sprint 1–3>
**Created:** YYYY-MM-DD
**Updated:** YYYY-MM-DD

### Business Goal
<One paragraph. What business problem does this solve for Shivam Jewels? Tie to PRD epics.>

### Business Value
<Quantified or qualified value: e.g., "Reduces manual lead processing from 4h/day to zero", "Enables outreach to 500+ buyers per week">

### Scope (In / Out)

| In Scope | Out of Scope |
|---|---|
| <What this epic covers> | <What is explicitly excluded> |

### Acceptance Criteria
- [ ] <Criterion 1 — measurable, testable>
- [ ] <Criterion 2>
- [ ] ...

### User Stories (Children)
| Story ID | Title | Status |
|---|---|---|
| US-<ID> | <Title> | Draft |

### Dependencies
| Depends On | Type | Notes |
|---|---|---|
| EPIC-<ID> | Blocking | Must complete before this epic starts |
| External API: Apollo.io | Integration | Enrichment cannot proceed without Apollo key |

### Definition of Done
- [ ] All child user stories are completed and accepted
- [ ] Acceptance criteria above are all met and verified
- [ ] Code reviewed, tests passing at 80%+ coverage
- [ ] API spec and DB schema updated if applicable
- [ ] Documentation updated in `ai-development-guidelines/`
- [ ] Feature deployed to staging and smoke-tested
```

---

## How to Write a Good Epic

### 1. Tie to the PRD
Every epic must map to an epic or feature area in `ai-development-guidelines/PRD.md`. Reference the PRD epic ID in the title or body. Do not invent features that are not in the PRD without stakeholder sign-off.

### 2. Define the Business Goal First
Before writing acceptance criteria or stories, answer: **"What does Shivam Jewels gain when this epic is done?"**

Good: *"Sales reps can view AI-matched inventory suggestions for each lead without any manual SQL queries."*
Bad: *"Build a matching service."*

### 3. Write Measurable Acceptance Criteria
Acceptance criteria must be testable by a human or automated test. Use the format:
- **Given** `<context>` **When** `<action>` **Then** `<observable result>`
- Or a checkbox checklist with clear pass/fail conditions

### 4. Define Scope Boundaries (In / Out)
Explicitly document what is OUT of scope. This prevents scope creep and gives the team permission to defer related-but-separate work to a future epic.

### 5. Set the Phase and Priority
Map every epic to a delivery phase from `ai-development-guidelines/Plan.md`:
- **Phase 0** — Foundation (infra, config, scaffolding)
- **Phase 1** — POC (end-to-end demo flow)
- **Phase 2** — Alpha (core features, internal users)
- **Phase 3** — Beta (external users, hardening)
- **Phase 4** — GA (production, scale)

### 6. Identify Dependencies Early
Block all child stories on dependency resolution. If an epic depends on an external API key (Apollo, Hunter, SendGrid), flag it as a blocker before sprint planning.

---

## Epic Sizing Guidelines

| Size | Description | Story Count | Sprint Span |
|---|---|---|---|
| XS | Thin slice, low complexity | 1–3 stories | 1 sprint |
| S | Small initiative, single domain | 3–6 stories | 1–2 sprints |
| M | Cross-domain, moderate complexity | 5–10 stories | 2–3 sprints |
| L | Platform capability, multiple services | 8–15 stories | 3–5 sprints |
| XL | Major platform initiative | 15+ stories | 5+ sprints — SPLIT this epic |

**Rule:** If an epic has more than 15 user stories or spans more than 5 sprints, split it into two or more child epics with a parent theme.

---

## Jewelry AI Platform Epics

The following epics are defined from `ai-development-guidelines/PRD.md`. Create detailed Epic documents (using the anatomy above) in `ai-development-guidelines/epics/` before starting any phase.

| Epic ID | Title | Phase | Priority |
|---|---|---|---|
| EPIC-01 | Platform Foundation & Infrastructure | Phase 0 | Critical |
| EPIC-02 | Lead Ingestion & Deduplication | Phase 1 | Critical |
| EPIC-03 | AI Inventory Matching Engine | Phase 1 | Critical |
| EPIC-04 | Contact Enrichment Pipeline | Phase 1 | High |
| EPIC-05 | AI Outreach Generation & Review | Phase 1 | High |
| EPIC-06 | Email Delivery & Tracking | Phase 2 | High |
| EPIC-07 | CRM Activity & Audit Log | Phase 2 | Medium |
| EPIC-08 | Lead Scoring & Prioritization | Phase 2 | High |
| EPIC-09 | Streamlit Dashboard & UI | Phase 2 | Medium |
| EPIC-10 | n8n Workflow Automation | Phase 2 | Medium |
| EPIC-11 | Authentication & Role-Based Access | Phase 2 | Critical |
| EPIC-12 | WhatsApp Outreach Channel (Twilio) | Phase 3 | Medium |
| EPIC-13 | MLflow Experiment Tracking & Model Registry | Phase 3 | Low |
| EPIC-14 | Performance, Caching & Scale Hardening | Phase 4 | Medium |
| EPIC-15 | Observability, Monitoring & Alerting | Phase 4 | High |

---

## Epic Lifecycle States

```
Draft → Refined → Active → In Progress → Done
                              ↓
                          Cancelled (if de-prioritised)
```

| State | Meaning | Gate to Next |
|---|---|---|
| **Draft** | Epic identified, not yet fully defined | Epic anatomy complete |
| **Refined** | Acceptance criteria written, stories created | Sprint planning picks it up |
| **Active** | Sprint work has started on child stories | N/A |
| **In Progress** | At least one story is in development | N/A |
| **Done** | All stories done, DoD met, accepted by owner | Owner sign-off |
| **Cancelled** | De-scoped; record rationale in the document | — |

---

## File Location & Naming

- Store epic documents in: `ai-development-guidelines/epics/`
- File name pattern: `EPIC-<ID>-<slug>.md`
  - Example: `EPIC-01-platform-foundation.md`
  - Example: `EPIC-03-inventory-matching-engine.md`
- One file per epic — do not combine multiple epics in one file

---

## Rules Summary (Non-Negotiable)

- **Epic-first:** No user story, no task, no code may be written without a parent epic
- **PRD-aligned:** Every epic must trace to a PRD requirement or stakeholder-approved scope change
- **Scoped:** Every epic has explicit In/Out of scope boundaries
- **Measurable:** Every epic has at least three testable acceptance criteria
- **Phased:** Every epic is assigned to exactly one delivery phase
- **Documented:** Epic file created in `ai-development-guidelines/epics/` before first sprint
- **Linked:** Every child user story references its parent epic ID (`EPIC-<ID>`)
- **Closed-loop:** Epic is not marked Done until all child stories are Done and DoD is verified
