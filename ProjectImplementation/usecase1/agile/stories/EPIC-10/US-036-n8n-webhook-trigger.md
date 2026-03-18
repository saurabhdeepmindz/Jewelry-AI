# US-036: n8n Webhook Trigger Integration

**Epic:** EPIC-10
**Actor:** `system`
**Story Points:** 5
**Priority:** Medium
**Status:** Ready

## User Story

As the **system**,
I want to trigger n8n email sequence workflows via webhook when an outreach is sent,
so that follow-up scheduling is automated without any manual intervention.

## Acceptance Criteria

### AC1: n8n workflow triggered on outreach send
**Given** an `OutreachMessage` with `sequence_step=1` is successfully sent
**When** the OutreachService calls `POST {N8N_WEBHOOK_URL}` with the workflow trigger payload
**Then** n8n receives the webhook and starts the sequence workflow; a `workflow_execution_id` is returned and stored

### AC2: Trigger payload contains all required fields
**Given** a send event fires
**When** the n8n webhook payload is inspected
**Then** it contains: `lead_id`, `contact_id`, `outreach_message_id`, `contact_email`, `sequence_step=1`, `trace_id`

### AC3: n8n webhook failure does not block the send
**Given** n8n is temporarily unavailable (connection refused)
**When** the OutreachService tries to trigger the workflow
**Then** the send operation completes successfully; the n8n trigger failure is logged at WARNING; a retry is scheduled via Celery (not blocking the main flow)

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test with mocked n8n: send → webhook called → execution_id returned
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] n8n URL from `Settings.N8N_WEBHOOK_URL` — never hardcoded
- [ ] PR squash-merged to master

## Notes

- n8n webhook is a fire-and-forget call with 5s timeout
- n8n workflow JSON committed at `src/workflows/n8n/email_sequence.json`
- `workflow_execution_id` stored in Redis (key: `n8n:{outreach_message_id}`) with TTL 30 days
