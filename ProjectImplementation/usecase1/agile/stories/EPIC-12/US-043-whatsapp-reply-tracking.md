# US-043: WhatsApp Reply Tracking via Webhook

**Epic:** EPIC-12
**Actor:** `system`
**Story Points:** 3
**Priority:** Medium
**Status:** Draft

## User Story

As the **system**,
I want to receive and process Twilio WhatsApp reply webhooks,
so that buyer responses on WhatsApp are captured and the lead status is updated automatically.

## Acceptance Criteria

### AC1: WhatsApp reply webhook processed
**Given** a buyer replies to a WhatsApp message
**When** Twilio sends `POST /api/v1/outreach/whatsapp-webhook` with the reply payload
**Then** the matching `OutreachMessage` is found; `leads.status=responded`; `whatsapp_replied` CRM event appended with `{"reply_body": "..."}` payload

### AC2: Invalid Twilio signature rejected
**Given** a POST to `/api/v1/outreach/whatsapp-webhook` with invalid signature
**When** the handler validates using `twilio.request_validator.RequestValidator`
**Then** 403 response returned; no DB changes made

### AC3: Unknown sender handled gracefully
**Given** a WhatsApp message arrives from a number not in the contacts table
**When** the webhook handler processes it
**Then** the event is logged at WARNING: `"WhatsApp reply from unknown number: +1234"`; 200 response returned (Twilio must not retry)

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: Twilio webhook → CRM event appended
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Twilio signature validation confirmed working in staging
- [ ] PR squash-merged to master

## Notes

- Twilio webhook validation: `RequestValidator.validate(url, params, signature)`
- Webhook URL must be HTTPS in production (Twilio requirement)
- Reply body stored in `event_payload.reply_body`; truncated to 1000 chars if longer
