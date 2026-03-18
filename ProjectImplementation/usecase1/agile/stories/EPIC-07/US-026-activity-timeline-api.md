# US-026: Lead Activity Timeline API Endpoint

**Epic:** EPIC-07
**Actor:** `rep`
**Story Points:** 2
**Priority:** Medium
**Status:** Ready

## User Story

As a **rep**,
I want to view the complete activity timeline for any of my leads via the API,
so that I can understand exactly what has happened to a lead without asking the engineering team.

## Acceptance Criteria

### AC1: Timeline returned in descending order
**Given** a lead with 10 CRM activity events
**When** `GET /api/v1/crm/{lead_id}/activity` is called
**Then** events are returned in descending `created_at` order (newest first); default `limit=20`

### AC2: Pagination works correctly
**Given** a lead has 50 CRM events
**When** `GET /api/v1/crm/{lead_id}/activity?page=2&limit=20` is called
**Then** events 21–40 are returned; `total=50`, `page=2`, `limit=20` in response envelope

### AC3: Rep cannot see another rep's lead timeline
**Given** a rep tries to access the timeline for a lead not assigned to them
**When** the request is processed
**Then** 403 response returned; no CRM data exposed

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test for the API endpoint
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- Response uses `PageResponse[CRMActivityResponse]` envelope
- `event_payload` is returned as-is (raw JSONB) — never filtered or redacted
- Manager and admin can access any lead's timeline; rep is restricted to assigned leads
