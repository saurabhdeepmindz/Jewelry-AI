# User Story Rules — Jewelry AI Platform (Project-Specific)

> **Extends:** `ai-development-guidelines/rules/user-story-rules.md` (generic user story rules)
> **Purpose:** Project-specific actor definitions, DoD toolchain, AC examples, and story conventions for the Jewelry AI platform.
> **Sequence:** User stories are created AFTER each Epic is defined. Every story MUST link to a parent Epic.

---

## Project Context

**Platform:** Jewelry AI Lead Automation — Shivam Jewels
**Stack:** FastAPI · LangChain · LangGraph · PostgreSQL + pgvector · Redis · Celery · n8n · Streamlit
**Epic Rules:** `project-specific-guidelines/rules/epic-rules.md`
**Story Storage:** `ai-development-guidelines/stories/`

---

## Actor Reference — Jewelry AI Platform

Use these actors consistently across all user stories. Do not invent new actor names without updating this table.

| Actor | Description | Example Usage |
|---|---|---|
| `admin` | System administrator with full platform access | "As an **admin**, I want to configure enrichment API keys so that the pipeline can contact Apollo.io." |
| `manager` | Sales manager who approves outreach and monitors pipeline | "As a **manager**, I want to review AI-generated emails before sending so that brand tone is maintained." |
| `rep` | Sales representative managing assigned leads | "As a **rep**, I want to see matched inventory for a lead so that I can personalise my pitch." |
| `system` | Automated background process or Celery task | "As the **system**, I want to automatically re-score leads nightly so that rep worklists stay current." |
| `buyer` | External jewelry buyer (future self-service portal — Phase 3+) | "As a **buyer**, I want to browse available diamond inventory so that I can shortlist items before a call." |

---

## Definition of Done — Jewelry AI Toolchain

Every user story must meet the following DoD before it can be marked Done:

- [ ] Code follows the layer architecture: `routers → services → repositories → DB models`
- [ ] Unit tests written first (RED → GREEN — TDD mandatory)
- [ ] Integration tests written for any new FastAPI endpoint (`httpx.AsyncClient`)
- [ ] `ruff check src tests` passes with zero errors
- [ ] `mypy src` passes with zero errors
- [ ] `pytest --cov=src --cov-report=term-missing` reports ≥ 80% coverage
- [ ] Alembic migration created for any schema addition or change
- [ ] `ai-development-guidelines/docs/API_SPEC.md` updated if a new endpoint is added
- [ ] `ai-development-guidelines/docs/DB_SCHEMA.md` updated if a table or column changes
- [ ] No direct SQLAlchemy calls outside repository layer
- [ ] No direct LLM API calls outside LangChain agents (`src/agents/`)
- [ ] No mutation of domain objects (use `model.model_copy(update={...})`)
- [ ] Code reviewed and approved
- [ ] Acceptance criteria confirmed by assignee or story owner

---

## Story Points — Jewelry AI Examples

| Points | Meaning | Jewelry AI Example |
|---|---|---|
| **1** | Trivial | Add a field to `LeadResponse` schema; update a config value in `settings.py` |
| **2** | Small | CRUD endpoint for `Contact`; simple repository query by `lead_id` |
| **3** | Moderate | New service method with validation + external Apollo.io API call |
| **5** | Complex | New LangGraph node + service method + repository + unit/integration tests |
| **8** | Large | Full Celery pipeline stage: enrichment agent + task + error handling + retry logic |
| **13** | Split required | — |

---

## Acceptance Criteria Examples — Jewelry AI Context

### Good Example (Lead Outreach Story)

```
Given a lead with status "enriched" and at least one matched inventory item,
When the rep clicks "Generate Outreach" in the Streamlit dashboard,
Then the system creates an OutreachMessage record with tone="professional",
  and the message body references the matched inventory item by SKU,
  and the message status is set to "pending_review",
  and the rep sees a success notification in the UI.
```

### Good Example (System / Celery Task Story)

```
Given a lead with status "ingested" and no existing enrichment record,
When the enrich_lead_task Celery task is triggered,
Then the system calls the Apollo.io API with the lead's domain,
  and persists the returned contact data as a Contact record linked to the lead,
  and updates the lead status to "enriched",
  and logs the API response summary at INFO level with the lead's trace_id.
```

### Good Example (Sad Path / Error Handling Story)

```
Given a CSV upload containing a lead with an email domain already in the database,
When the ingestion service processes the file,
Then the duplicate lead is rejected with error code LEAD_DUPLICATE,
  and the rejection is recorded in the CRMActivity log with reason="duplicate_email",
  and the upload summary response includes a count of duplicates_skipped.
```

---

## Story File Location & Naming (Jewelry AI)

- Store story documents in: `ai-development-guidelines/stories/`
- Organise by epic: `ai-development-guidelines/stories/EPIC-<ID>/`
  - Example: `ai-development-guidelines/stories/EPIC-02/US-001-ingest-csv-leads.md`
  - Example: `ai-development-guidelines/stories/EPIC-03/US-005-match-leads-to-inventory.md`
- One file per story — do not combine multiple stories in one file
- Story IDs are global sequential integers: `US-001`, `US-002`, … — not reset per epic
- Maintain index: `ai-development-guidelines/stories/STORIES.md`

---

## Story Index — Jewelry AI

Maintain `ai-development-guidelines/stories/STORIES.md` with this structure:

```markdown
# Story Index — Jewelry AI Platform

| Story ID | Title | Epic | Status | Points | Sprint |
|---|---|---|---|---|---|
| US-001 | Ingest leads from CSV upload | EPIC-02 | Draft | 3 | — |
| US-002 | Deduplicate leads on email address | EPIC-02 | Draft | 2 | — |
| US-003 | Match leads to available inventory by category | EPIC-03 | Draft | 5 | — |
```

---

## Story Splitting — Jewelry AI Patterns

Apply these domain-specific splits when stories exceed 8 points:

| Scenario | Split Pattern | Result |
|---|---|---|
| Ingestion supports CSV and API push | By data variation | US-A: CSV ingest · US-B: API push ingest |
| Enrichment happy path + retry logic | By happy/sad path | US-A: Enrich lead via Apollo · US-B: Handle API failure and retry |
| Lead matching + match scoring | By acceptance criterion | US-A: Match leads to inventory · US-B: Score and rank matches |
| Outreach generation + review workflow | By workflow step | US-A: Generate outreach message · US-B: Manager review and approval |
| Dashboard: view leads + export leads | By read/write | US-A: View lead list with filters · US-B: Export filtered leads to CSV |
| RBAC: admin config + rep restrictions | By user role | US-A: Admin API key management · US-B: Rep view-only enforcement |

---

## Rules Summary (Project-Specific Additions)

In addition to the non-negotiables in `ai-development-guidelines/rules/user-story-rules.md`:

- **Actor-locked:** Use only the defined actors above — do not coin new actor names mid-sprint
- **Tool DoD:** Every story must clear ruff, mypy, pytest ≥80%, and alembic before Done
- **Layer compliance:** DoD must confirm no layer-architecture violations (no SQL in routers, no LLM calls in services)
- **Immutability check:** DoD must confirm domain objects are not mutated (use `model_copy`)
- **Story storage:** All story files go in `ai-development-guidelines/stories/EPIC-<ID>/`
- **Index maintained:** `ai-development-guidelines/stories/STORIES.md` updated on every state change
