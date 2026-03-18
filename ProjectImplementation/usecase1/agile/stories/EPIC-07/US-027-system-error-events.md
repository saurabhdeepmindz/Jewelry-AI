# US-027: System Error Event Logging

**Epic:** EPIC-07
**Actor:** `system`
**Story Points:** 2
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want all pipeline failures logged as `system_error` CRM activity events,
so that the engineering team can diagnose exactly which step failed for any lead.

## Acceptance Criteria

### AC1: Celery task final failure appends system_error
**Given** a Celery enrichment task exhausts all 3 retries
**When** the final retry also fails
**Then** a `system_error` CRM event is appended with `event_payload: {"step": "enrich_contact", "error": "<exception message>", "attempt": 3}`

### AC2: LangGraph node failure appends system_error
**Given** the `generate_outreach` LangGraph node raises an unhandled exception
**When** the pipeline catches it at the graph level
**Then** a `system_error` CRM event is appended for the affected lead with `{"step": "generate_outreach", "error": "..."}` before the pipeline exits

### AC3: system_error does not block the audit trail
**Given** a `system_error` event is being appended
**When** the CRM append itself fails (e.g., DB connection lost)
**Then** the error is logged to structured logs at `CRITICAL` level; the system does NOT raise a second exception or enter an infinite error loop

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: task fails → system_error event in DB
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- `system_error` must include `trace_id` for correlation with application logs
- `event_payload.step` uses the function/node name as defined in the pipeline
- CRM append in error handler uses a separate DB session — not the one that may have failed
