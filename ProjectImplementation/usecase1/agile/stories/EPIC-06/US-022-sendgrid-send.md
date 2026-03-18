# US-022: Send Approved Emails via SendGrid

**Epic:** EPIC-06
**Actor:** `system`
**Story Points:** 5
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want to send approved outreach emails via SendGrid,
so that buyers actually receive the AI-generated messages after manager approval.

## Acceptance Criteria

### AC1: Approved message sent successfully
**Given** an `OutreachMessage` with `status=approved`
**When** `POST /api/v1/outreach/messages/{id}/send` is called by the system or manager
**Then** SendGrid API is called; `sendgrid_message_id` stored; `status=sent`; `sent_at=NOW()`; `leads.status=contacted`; `outreach_sent` CRM event appended

### AC2: Non-approved message cannot be sent
**Given** an `OutreachMessage` with `status=pending_review`
**When** the send endpoint is called
**Then** 422 response: `"Cannot send message with status: pending_review"`; no SendGrid call made

### AC3: SendGrid failure retried
**Given** SendGrid returns HTTP 503
**When** the send task processes the message
**Then** the task retries up to 3 times; after final failure, `status` remains `approved` (not `sent`); `system_error` CRM event appended

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test with mocked SendGrid: send → status=sent
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] SendGrid tested end-to-end in staging
- [ ] PR squash-merged to master

## Notes

- SendGrid v3 API: `POST /v3/mail/send` with `from`, `to`, `subject`, `content`
- Tracking settings: `open_tracking=true`, `click_tracking=true` enabled in SendGrid payload
- `sendgrid_message_id` = value of `X-Message-Id` response header
