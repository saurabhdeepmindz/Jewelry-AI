# EPIC-12: WhatsApp Outreach Channel

**Status:** Draft
**Phase:** Phase 3
**Layer(s):** Layer 2 — Integration (Twilio)
**Priority:** Medium
**Estimated Size:** M

---

## Problem Statement

Email open rates in the jewelry wholesale trade are often below 20%. WhatsApp messages in B2B contexts achieve significantly higher open and response rates, especially in markets like India, the Middle East, and Southeast Asia where buyers are active on WhatsApp throughout the day.

## Goal

The platform supports sending AI-generated WhatsApp messages to verified buyer phone numbers via Twilio Conversations API. WhatsApp outreach follows the same human review gate as email — drafts must be approved before sending. Replies are tracked and linked to the lead's CRM activity.

## Scope (In)

- Twilio Conversations API integration via `twilio` Python SDK
- `OutreachMessage` with `channel=whatsapp` — same model, different channel
- WhatsApp draft generation: shorter, conversational tone (system prompt variant)
- Human review gate applies: `status=pending_review` → approved → sent
- `POST /api/v1/outreach/messages/{id}/send-whatsapp` — send approved WhatsApp
- Twilio webhook: `POST /api/v1/outreach/whatsapp-webhook` — reply tracking
- `whatsapp_sent`, `whatsapp_replied` CRM activity events
- Phone number format validation (E.164: `+{country_code}{number}`)

## Scope (Out)

- WhatsApp Business Account setup (pre-requisite handled by Shivam Jewels ops team)
- Rich media messages (images, PDFs of GIA certs) — Phase 4 enhancement
- WhatsApp sequence automation (single message only in Phase 3)

---

## Acceptance Criteria

- [ ] AC1: An approved WhatsApp message is sent via Twilio → `status=sent`, `sent_at` set, `whatsapp_sent` CRM event
- [ ] AC2: Buyer replies on WhatsApp → Twilio webhook fires → `whatsapp_replied` CRM event appended, `leads.status=responded`
- [ ] AC3: Phone number missing or invalid E.164 format → 422 before any API call is made
- [ ] AC4: WhatsApp draft body is ≤ 1024 characters (WhatsApp template limit) — enforced at generation time
- [ ] AC5: Twilio webhook signature verified — invalid signature → 401; payload discarded
- [ ] AC6: `ROLE_REP` cannot approve WhatsApp messages — approval requires `ROLE_MANAGER` or `ROLE_ADMIN`

---

## User Stories

- US-042: WhatsApp message send via Twilio — `agile/stories/EPIC-12/US-042-twilio-whatsapp-send.md`
- US-043: WhatsApp reply tracking via webhook — `agile/stories/EPIC-12/US-043-whatsapp-reply-tracking.md`
- US-044: WhatsApp outreach review gate — `agile/stories/EPIC-12/US-044-whatsapp-review-gate.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| Twilio Conversations API | WhatsApp message send + reply webhook | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER` |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] Twilio send + reply webhook tested end-to-end in staging
- [ ] Webhook signature verification confirmed working
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
