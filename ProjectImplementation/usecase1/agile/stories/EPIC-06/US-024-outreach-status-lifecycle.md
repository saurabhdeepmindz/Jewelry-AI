# US-024: Outreach Message Status Lifecycle

**Epic:** EPIC-06
**Actor:** `system`
**Story Points:** 2
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want the outreach message status to follow a strict lifecycle state machine,
so that the pipeline always knows the current state of every message without ambiguity.

## Acceptance Criteria

### AC1: Valid transitions allowed
**Given** an `OutreachMessage` at any status
**When** a valid state transition is attempted (e.g., `pending_review → approved`, `sent → opened`)
**Then** the transition succeeds; `updated_at` is refreshed; the corresponding CRM event is appended

### AC2: Invalid transitions rejected
**Given** an `OutreachMessage` with `status=bounced`
**When** an `approve` or `send` action is attempted
**Then** a 422 response is returned with message: `"Invalid transition: bounced → approved"`; no state change occurs

### AC3: Lead status advances in sync
**Given** an `OutreachMessage` transitions from `approved → sent`
**When** the send completes
**Then** `leads.status` advances from `enriched/scored` to `contacted` (if not already)

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests: all valid and invalid transitions tested
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] State machine diagram added to `docs/design/` or inline in `OutreachService`
- [ ] PR squash-merged to master

## Notes

**Valid state machine transitions:**
```
draft → pending_review → approved → sent → opened → clicked → replied → closed
                       → rejected
                       → bounced
```
- A message can go from `opened` or `clicked` back to its terminal state via `replied` or `bounced`
- `replied` and `bounced` are terminal — no further transitions
