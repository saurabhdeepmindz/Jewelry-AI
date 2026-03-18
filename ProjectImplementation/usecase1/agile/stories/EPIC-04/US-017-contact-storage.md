# US-017: Enriched Contact Storage and Lead Status Update

**Epic:** EPIC-04
**Actor:** `system`
**Story Points:** 2
**Priority:** Critical
**Status:** Ready

## User Story

As the **system**,
I want enriched contacts stored in the database and the lead status advanced to `enriched`,
so that outreach generation has access to verified buyer contact information.

## Acceptance Criteria

### AC1: Contacts stored and lead status updated
**Given** enrichment returns 2 contacts for a lead
**When** the enrichment service persists results
**Then** 2 `Contact` rows are created with correct `lead_id` foreign key; `leads.status` is updated to `enriched`; `lead_enriched` CRM activity is appended

### AC2: Duplicate contact upserted, not duplicated
**Given** a `Contact` with `(lead_id=X, email=buyer@acme.com)` already exists
**When** enrichment returns the same email for the same lead
**Then** the existing contact is updated (upsert); no second row is created; `idx_contacts_lead_email` unique index is respected

### AC3: Zero contacts — lead still advances
**Given** all enrichment providers returned no contacts for an eligible lead
**When** the enrichment service completes
**Then** `leads.status = enriched` still; zero `Contact` rows created; `lead_enriched` CRM activity appended with `{"contact_count": 0, "source": "none"}`; pipeline continues to scoring

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: enrichment → contacts in DB → lead status = enriched
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Alembic migration: `idx_contacts_lead_email` unique partial index confirmed
- [ ] PR squash-merged to master

## Notes

- Upsert: `INSERT INTO contacts ... ON CONFLICT (lead_id, email) WHERE is_deleted=false DO UPDATE SET ...`
- `updated_at` on the upserted contact must be refreshed to `NOW()`
- `leads.status` update and CRM append must happen in the same DB transaction (Unit of Work)
