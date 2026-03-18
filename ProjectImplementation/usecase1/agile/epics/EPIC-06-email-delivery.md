# EPIC-06: Email Delivery & Tracking

**Status:** Ready
**Phase:** Phase 2
**Layer(s):** Layer 2 — Integration (SendGrid)
**Priority:** High
**Estimated Size:** M

---

## Problem Statement

An approved outreach draft sitting in the database is worthless until it is actually sent. Once sent, the team needs to know whether the buyer opened it, clicked a link, replied, or bounced — this data drives follow-up decisions and pipeline analytics.

## Goal

Approved `OutreachMessage` records are delivered to buyers via SendGrid. Delivery events (open, click, reply, bounce) are received via SendGrid webhooks and update the message status and timestamps in real time, enabling the sales team to see engagement at a glance.

## Scope (In)

- SendGrid `send_email()` via `sendgrid` Python SDK
- `POST /api/v1/outreach/messages/{id}/send` — triggers send for approved messages
- Store `sendgrid_message_id` and `sent_at` on `OutreachMessage`
- Set `leads.status = contacted` after first send
- SendGrid inbound webhook: `POST /api/v1/outreach/webhook`
- Handle webhook events: `open`, `click`, `delivered`, `bounce`, `spam_report`, `unsubscribe`
- Update `OutreachMessage` fields: `opened_at`, `clicked_at`, `bounced_at`
- CRM activity: `outreach_sent`, `email_opened`, `email_clicked`, `email_bounced` events
- Webhook signature verification (SendGrid Event Webhook Signature)

## Scope (Out)

- n8n follow-up sequence automation (EPIC-10)
- WhatsApp channel (EPIC-12)
- Analytics dashboards (EPIC-09)

---

## Acceptance Criteria

- [ ] AC1: An approved message is sent via SendGrid → `sendgrid_message_id` stored, `status=sent`, `sent_at` set, `leads.status=contacted`, `outreach_sent` CRM event appended
- [ ] AC2: SendGrid fires an `open` event → `status=opened`, `opened_at` set, `email_opened` CRM event appended
- [ ] AC3: SendGrid fires a `bounce` event → `status=bounced`, `bounced_at` set, `email_bounced` CRM event appended; no follow-up triggered for bounced addresses
- [ ] AC4: Webhook received with invalid signature → 401 response; payload discarded
- [ ] AC5: Only messages with `status=approved` can be sent — attempting to send a `draft` or `pending_review` message returns 422
- [ ] AC6: `leads.status` advances to `responded` when a `reply` event is received

---

## User Stories

- US-022: Send approved emails via SendGrid — `agile/stories/EPIC-06/US-022-sendgrid-send.md`
- US-023: SendGrid webhook processing — `agile/stories/EPIC-06/US-023-sendgrid-webhooks.md`
- US-024: Outreach message status lifecycle — `agile/stories/EPIC-06/US-024-outreach-status-lifecycle.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| SendGrid API v3 | Email delivery + event webhooks | `SENDGRID_KEY_ENCRYPTED` |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] SendGrid send + webhook tested end-to-end in staging
- [ ] Webhook signature verification confirmed working
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
