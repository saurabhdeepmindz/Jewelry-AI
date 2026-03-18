# User Story Rules — Usecase 1: Jewelry AI Lead Automation

> **Extends:** `best-practices_rule_set_code/docs/rules/user-story-rules.md` (generic rules)
> **Purpose:** Defines actor labels, story format, toolchain DoD, acceptance criteria examples, and splitting patterns for the Jewelry AI platform.
> **Artifact to produce:** Individual story files in `agile/stories/EPIC-<ID>/US-<NNN>-<slug>.md`

---

## Actor Labels

Use these exact labels in all user stories:

| Label | Maps To | Description |
|---|---|---|
| `admin` | `ROLE_ADMIN` | Platform administrator managing users, API keys, system config |
| `manager` | `ROLE_MANAGER` | Sales manager approving outreach, monitoring pipeline |
| `rep` | `ROLE_REP` | Sales representative uploading leads, triggering enrichment |
| `system` | `ROLE_SYSTEM` | Automated Celery workers and LangGraph pipeline nodes |
| `buyer` | `ROLE_BUYER` | External jewelry buyer — **Phase 3+ only, do not use in Phase 0–2** |

---

## User Story Format

```markdown
# US-<NNN>: <Title>

**Epic:** EPIC-<ID>
**Actor:** `<actor>`
**Story Points:** <Fibonacci: 1 | 2 | 3 | 5 | 8 | 13>
**Priority:** Critical | High | Medium | Low
**Status:** Draft | Ready | In Progress | Done

## User Story
As a **<actor>**,
I want to **<action>**,
so that **<business value>**.

## Acceptance Criteria

### AC1: <Happy path title>
**Given** <initial context / precondition>
**When** <action taken>
**Then** <observable outcome>

### AC2: <Validation / edge case title>
**Given** ...
**When** ...
**Then** ...

### AC3: <Error / negative case title>
**Given** ...
**When** ...
**Then** ...

## Definition of Done
- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test for the API endpoint
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Alembic migration (if schema changed)
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes
<Optional: technical constraints, open questions, linked issues>
```

---

## Acceptance Criteria Examples (Jewelry AI)

### Lead Ingestion (EPIC-02)

```
As a rep, I want to upload a CSV of trade leads,
so that new buyer companies are ingested into the pipeline automatically.

AC1: Valid CSV upload
Given: A rep uploads a valid CSV with company_name, domain, email, source
When:  The file is submitted via POST /api/v1/leads/upload
Then:  All valid rows are persisted as Lead records with status=ingested
       and a 201 response is returned with a summary (created, duplicates, errors)

AC2: Duplicate detection
Given: A lead with the same email domain already exists in the database
When:  The same domain appears in a new CSV upload
Then:  The duplicate row is skipped (not inserted), and included in the "duplicates" count in the response

AC3: Invalid CSV format
Given: The uploaded file is missing the required company_name column
When:  The file is submitted
Then:  A 422 response is returned with a clear error message identifying the missing column
```

### Inventory Matching (EPIC-03)

```
As the system, I want to match each ingested lead against available inventory,
so that only eligible leads proceed to enrichment.

AC1: Eligible match found
Given: A lead has company_name and buyer_category="RBC diamonds"
When:  The inventory match engine runs
Then:  The lead's match_status is set to ELIGIBLE and at least one inventory record is linked

AC2: No inventory match
Given: A lead's buyer profile does not match any available inventory item
When:  The inventory match engine runs
Then:  The lead's match_status is set to NOT_ELIGIBLE and no enrichment is triggered

AC3: Match threshold respected
Given: The configured minimum carat match threshold is 0.50
When:  A lead matches only inventory items below 0.50 carat
Then:  The lead is marked NOT_ELIGIBLE
```

### Contact Enrichment (EPIC-04)

```
As the system, I want to enrich eligible leads with buyer contact details,
so that reps have verified email and phone without manual research.

AC1: Apollo enrichment succeeds
Given: A lead is ELIGIBLE with a known domain
When:  The enrichment task runs
Then:  A Contact record is created with full_name, email, phone, title from Apollo.io

AC2: Apollo fails, Hunter fallback
Given: Apollo.io returns a non-2xx response for the domain
When:  The enrichment task retries
Then:  Hunter.io is called as fallback and email_verified is set based on Hunter result

AC3: Already enriched — no re-enrichment
Given: A Contact already exists for the lead with enriched_at set
When:  A duplicate enrichment task is triggered
Then:  The task exits without calling any external API (cache hit logged)
```

### Outreach Generation (EPIC-05)

```
As the system, I want to generate a personalized outreach email for each enriched lead,
so that reps and managers have AI-drafted messages ready for review.

AC1: Draft created successfully
Given: A lead is ELIGIBLE and has an enriched contact and at least one inventory match
When:  The outreach generation agent runs
Then:  An OutreachMessage is created with status=pending_review and body referencing matched SKUs

AC2: Human review gate enforced
Given: HUMAN_REVIEW_REQUIRED=true
When:  An outreach draft is generated
Then:  The message status is pending_review and it is NOT sent until approved by manager or admin

AC3: Manager approval triggers send
Given: A manager approves a pending_review message via PATCH /api/v1/outreach/messages/{id}/approve
When:  The approval is submitted
Then:  The message status changes to approved, the Outreach Service sends it via SendGrid,
       and a CRM activity record is appended
```

---

## Story Splitting Patterns (Jewelry AI)

| Too-Large Story | Split Into |
|---|---|
| "As a rep, I want to manage leads" | 1) Upload CSV, 2) View assigned leads, 3) Trigger enrichment, 4) View outreach queue |
| "As the system, I want to run the full pipeline" | 1) Match inventory, 2) Trigger enrichment, 3) Score lead, 4) Generate outreach draft |
| "As a manager, I want outreach analytics" | 1) View pipeline funnel, 2) View outreach open rates, 3) View reply rates per rep |
| "As admin, I want to manage users" | 1) Create user, 2) Assign role, 3) Deactivate user, 4) Reset password |

---

## Story File Naming Convention

```
agile/stories/EPIC-01/US-001-dev-environment-setup.md
agile/stories/EPIC-02/US-002-csv-upload-ingestion.md
agile/stories/EPIC-02/US-003-duplicate-detection.md
agile/stories/EPIC-03/US-004-inventory-eligibility-check.md
agile/stories/EPIC-04/US-005-apollo-enrichment.md
agile/stories/EPIC-04/US-006-hunter-fallback-enrichment.md
agile/stories/EPIC-05/US-007-outreach-draft-generation.md
agile/stories/EPIC-05/US-008-manager-approval-gate.md
...
```

---

## Toolchain DoD (applies to all stories)

All stories in this project MUST meet:

| Check | Command | Standard |
|---|---|---|
| Linting | `ruff check src tests` | Zero errors |
| Type checking | `mypy src` | Zero errors |
| Unit tests | `pytest tests/unit/` | RED → GREEN |
| Coverage | `pytest --cov=src` | ≥ 80% on changed files |
| Migration | `alembic upgrade head` | Applies cleanly |
| Secret scan | Manual / pre-commit | No secrets in code |
