# US-034: Outreach Review Queue for Managers

**Epic:** EPIC-09
**Actor:** `manager`
**Story Points:** 5
**Priority:** High
**Status:** Ready

## User Story

As a **manager**,
I want an outreach review queue showing all pending_review messages,
so that I can approve or reject AI-generated drafts without switching to an API client.

## Acceptance Criteria

### AC1: Queue shows all pending_review messages
**Given** a manager is logged in
**When** they navigate to the Review Queue page
**Then** all `OutreachMessage` records with `status=pending_review` are listed with: lead company name, contact name, email subject, sequence_step, created_at

### AC2: Approve action works inline
**Given** the manager is viewing a pending message in the queue
**When** they click the "Approve" button
**Then** the UI calls `PATCH .../approve`; the message disappears from the queue; a success toast is shown

### AC3: Reject with reason
**Given** the manager clicks "Reject" on a pending message
**When** they enter a rejection reason and confirm
**Then** the UI calls `PATCH .../reject` with the reason; the message is removed from the queue; `rejection_reason` stored; toast confirms rejection

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests for approve/reject API calls with mocked httpx
- [ ] E2E test: manager login → review queue → approve → item removed
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or API URLs
- [ ] PR squash-merged to master

## Notes

- Rep role cannot see this page — route guarded by `require_role("manager", "admin")`
- `st.expander()` for each message: shows full body before approve/reject decision
- Rejection reason input: `st.text_area()` with `max_chars=500`; required before reject button enables
