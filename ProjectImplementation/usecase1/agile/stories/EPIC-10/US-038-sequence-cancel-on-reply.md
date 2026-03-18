# US-038: Sequence Cancellation on Reply

**Epic:** EPIC-10
**Actor:** `system`
**Story Points:** 3
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want the email sequence to stop automatically when a buyer replies,
so that the buyer is never sent a follow-up after they've already engaged.

## Acceptance Criteria

### AC1: Reply event cancels pending sequence steps
**Given** a buyer replies to a step-1 email (SendGrid `email_replied` webhook fires)
**When** the reply event is processed
**Then** `leads.status = responded`; any existing `pending_review` step-2 and step-3 `OutreachMessage` records are set to `status=rejected` with `rejection_reason="cancelled_due_to_reply"`

### AC2: n8n workflow execution cancelled
**Given** the n8n workflow is waiting at its day-4 Wait node
**When** FastAPI receives the reply event and calls `DELETE /api/v1/workflows/{execution_id}`
**Then** n8n cancels the workflow execution; no day-4 callback fires

### AC3: Cancellation is idempotent
**Given** the reply event is received twice (webhook retry)
**When** the cancellation logic runs the second time
**Then** no error is raised; already-cancelled messages remain `rejected`; n8n cancel call for an already-cancelled workflow returns gracefully

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: reply webhook → pending messages cancelled → n8n execution cancelled
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets
- [ ] PR squash-merged to master

## Notes

- Cancellation of step-2/3 messages uses `OutreachRepository.cancel_sequence(lead_id, from_step=2)`
- n8n cancellation via `DELETE {N8N_API_URL}/executions/{execution_id}`
- n8n execution_id retrieved from Redis key `n8n:{outreach_message_id}`
