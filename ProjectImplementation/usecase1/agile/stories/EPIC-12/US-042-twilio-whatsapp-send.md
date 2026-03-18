# US-042: WhatsApp Message Send via Twilio

**Epic:** EPIC-12
**Actor:** `system`
**Story Points:** 5
**Priority:** Medium
**Status:** Draft

## User Story

As the **system**,
I want to send approved WhatsApp messages to buyer phone numbers via Twilio,
so that buyers in WhatsApp-first markets receive outreach on their preferred channel.

## Acceptance Criteria

### AC1: Approved WhatsApp message sent successfully
**Given** an `OutreachMessage` with `channel=whatsapp` and `status=approved`
**When** `POST /api/v1/outreach/messages/{id}/send-whatsapp` is called
**Then** Twilio Conversations API is called; `status=sent`; `sent_at=NOW()`; `whatsapp_sent` CRM event appended

### AC2: Invalid phone number blocked before API call
**Given** the buyer contact has `phone="+91invalid"`
**When** the send endpoint validates the number
**Then** 422 response: `"Invalid phone number format. Expected E.164: +{country_code}{number}"`; no Twilio call made

### AC3: WhatsApp body length enforced
**Given** a WhatsApp draft body is 1100 characters
**When** the generation step validates the output
**Then** the body is truncated to 1024 characters with `"..."` appended; a WARNING log is emitted

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test with mocked Twilio SDK
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Twilio credentials from `Settings` — never hardcoded
- [ ] Twilio tested end-to-end in staging
- [ ] PR squash-merged to master

## Notes

- Twilio SDK: `twilio.rest.Client(account_sid, auth_token)`
- WhatsApp sender: `whatsapp:{TWILIO_WHATSAPP_NUMBER}` (from Settings)
- Phone number validation: use `phonenumbers` library (`phonenumbers.is_valid_number()`)
