# US-021: Manager Approval and Rejection Workflow

**Epic:** EPIC-05
**Actor:** `manager`
**Story Points:** 3
**Priority:** Critical
**Status:** Ready

## User Story

As a **manager**,
I want to approve or reject AI-generated outreach drafts with a single API call,
so that I can quickly process the review queue and give reps clear feedback on rejected drafts.

## Acceptance Criteria

### AC1: Approval transitions message to approved
**Given** an `OutreachMessage` with `status=pending_review`
**When** a manager calls `PATCH /api/v1/outreach/messages/{id}/approve`
**Then** `status=approved`, `approved_by={manager_user_id}`, `approved_at=NOW()`, and `outreach_approved` CRM activity is appended; response is 200 with updated message

### AC2: Rejection stores reason and transitions to rejected
**Given** an `OutreachMessage` with `status=pending_review`
**When** a manager calls `PATCH /api/v1/outreach/messages/{id}/reject` with `{"rejection_reason": "Tone too informal"}`
**Then** `status=rejected`, `rejection_reason="Tone too informal"`, `outreach_rejected` CRM activity appended; response is 200 with updated message

### AC3: Cannot approve an already-approved message
**Given** an `OutreachMessage` with `status=approved`
**When** the same approve endpoint is called again
**Then** a 422 response is returned: `"Message is already in status: approved"`; no duplicate CRM event

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: approve → status change → CRM event
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- Valid state transitions: `pending_review → approved`, `pending_review → rejected`
- Attempting to approve from `draft`, `sent`, `rejected` returns 422
- `rejection_reason` is required for rejection (400 if absent)
