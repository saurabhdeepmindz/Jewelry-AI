# US-025: Append-Only CRM Activity Logging

**Epic:** EPIC-07
**Actor:** `system`
**Story Points:** 3
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want every significant lead lifecycle event appended to `crm_activity` as an immutable record,
so that the complete history of a lead is always available for audit and debugging.

## Acceptance Criteria

### AC1: Activity appended with correct fields
**Given** the enrichment pipeline successfully enriches a lead
**When** `CRMRepository.append()` is called with `event_type=lead_enriched`
**Then** a row is created in `crm_activity` with non-null `lead_id`, `event_type`, `trace_id`, `actor`, and `created_at`; no `updated_at` column exists on this table

### AC2: Update and delete operations rejected
**Given** any code path attempts to call `CRMRepository.update()` or `CRMRepository.soft_delete()`
**When** the method is invoked
**Then** a `CRMImmutableError` is raised immediately (method raises unconditionally — not even a DB call is made)

### AC3: All 18 event types produce a valid row
**Given** each of the 18 `ActivityType` enum values is used
**When** `CRMRepository.append()` is called with each type
**Then** a valid row is created; `event_payload` contains at least one key specific to that event type

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: append called → row in DB; update → CRMImmutableError
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- `CRMRepository` must NOT inherit `soft_delete()` from `BaseRepository` — override with `raise CRMImmutableError()`
- `trace_id` comes from the originating HTTP request context (via `contextvars.ContextVar`)
- `actor` format: `"system"` for Celery/LangGraph; `"user:{uuid}"` for API-triggered actions
