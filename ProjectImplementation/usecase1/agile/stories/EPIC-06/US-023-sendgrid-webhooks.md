# US-023: SendGrid Webhook Processing

**Epic:** EPIC-06
**Actor:** `system`
**Story Points:** 5
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want to receive and process SendGrid event webhooks,
so that email engagement events (open, click, bounce, reply) are captured in real time.

## Acceptance Criteria

### AC1: Valid webhook processed and event stored
**Given** SendGrid sends a POST to `/api/v1/outreach/webhook` with a valid signature and event `type=open`
**When** the webhook handler processes it
**Then** the matching `OutreachMessage` is found by `sendgrid_message_id`; `status=opened`; `opened_at=NOW()`; `email_opened` CRM activity appended; 200 response returned

### AC2: Invalid signature rejected
**Given** a POST to `/api/v1/outreach/webhook` with a missing or invalid `X-Twilio-Email-Event-Webhook-Signature` header
**When** the handler validates the signature
**Then** 401 response returned; no DB changes made; event discarded

### AC3: Unknown message_id handled gracefully
**Given** a webhook event references a `sendgrid_message_id` that does not exist in the DB
**When** the handler processes it
**Then** the event is logged at WARNING level and a 200 response is returned (idempotent — SendGrid must not retry)

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: webhook POST → CRM event appended
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] SendGrid webhook signature verification confirmed working in staging
- [ ] PR squash-merged to master

## Notes

- SendGrid sends webhook events as an array: `[{"event": "open", "sg_message_id": "...", "timestamp": 1234}]`
- Webhook endpoint must return 200 quickly (< 5s) — delegate DB writes to Celery if needed
- Signature verification uses `sendgrid.helpers.eventwebhook.EventWebhookHeader`
