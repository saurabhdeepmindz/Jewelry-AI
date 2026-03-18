# US-007: Lead Record Creation and Deduplication

**Epic:** EPIC-02
**Actor:** `system`
**Story Points:** 3
**Priority:** Critical
**Status:** Ready

## User Story

As the **system**,
I want to deduplicate incoming leads by email domain before creating records,
so that the same buyer company is never stored twice.

## Acceptance Criteria

### AC1: New lead created successfully
**Given** a parsed row with `domain=acme.com` that does not exist in the database
**When** the ingestion service processes the row
**Then** a `Lead` row is created with `status=ingested`, `match_status=pending`, and the correct `source` value

### AC2: Duplicate domain skipped
**Given** a lead with `domain=acme.com` already exists in the database (`is_deleted=false`)
**When** a CSV row with the same domain is processed
**Then** no new `Lead` row is created; the row is counted as `skipped_duplicates` in the response

### AC3: Null domain does not trigger deduplication
**Given** a CSV row where `domain` is empty or absent
**When** the ingestion service processes the row
**Then** the lead is created without a domain; no deduplication check is performed (null domains are allowed)

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: duplicate domain → no second row in DB
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Alembic migration: `idx_leads_domain` unique partial index confirmed in place
- [ ] PR squash-merged to master

## Notes

- Deduplication uses `LeadRepository.get_by_domain()` — checks `is_deleted=false` only
- Unique index `idx_leads_domain` on `leads(domain) WHERE is_deleted=false AND domain IS NOT NULL` provides DB-level guard
- Soft-deleted leads with the same domain do NOT block re-creation (intentional)
