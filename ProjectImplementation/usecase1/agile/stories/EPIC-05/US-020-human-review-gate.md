# US-020: Human Review Gate

**Epic:** EPIC-05
**Actor:** `manager`
**Story Points:** 3
**Priority:** Critical
**Status:** Ready

## User Story

As a **manager**,
I want all AI-generated outreach drafts held in `pending_review` status until I approve them,
so that no message is sent to a buyer without a human having reviewed it first.

## Acceptance Criteria

### AC1: Draft stays pending_review when HUMAN_REVIEW_REQUIRED=true
**Given** `HUMAN_REVIEW_REQUIRED=true` in settings
**When** an `OutreachMessage` is created by the generation agent
**Then** its `status=pending_review`; it is NOT sent automatically; no SendGrid API call is made

### AC2: Draft auto-approved when HUMAN_REVIEW_REQUIRED=false
**Given** `HUMAN_REVIEW_REQUIRED=false` in settings
**When** an `OutreachMessage` is created
**Then** its `status` is immediately advanced to `approved`; the OutreachService queues it for sending

### AC3: Rep cannot approve messages
**Given** a rep calls `PATCH /api/v1/outreach/messages/{id}/approve`
**When** the request is processed
**Then** a `403 Forbidden` response is returned; the message status remains `pending_review`

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: HUMAN_REVIEW_REQUIRED=true → message not sent
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- `HUMAN_REVIEW_REQUIRED` is a `bool` in `Settings` — not a per-message flag
- The feature flag check lives in `OutreachService.create_draft()`, not in the router
- Default value must be `True` — unsafe to default to auto-send
