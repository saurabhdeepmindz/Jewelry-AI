# US-037: Day-4 and Day-7 Follow-Up Generation

**Epic:** EPIC-10
**Actor:** `system`
**Story Points:** 5
**Priority:** Medium
**Status:** Ready

## User Story

As the **system**,
I want n8n to trigger follow-up email generation at day 4 and day 7,
so that buyers receive a structured outreach sequence without any manual scheduling.

## Acceptance Criteria

### AC1: Day-4 follow-up created after 4-day wait
**Given** n8n workflow was triggered for a sent step-1 message
**When** 4 days have elapsed (n8n Wait node)
**Then** n8n calls `POST /api/v1/outreach/messages` to create a step-2 draft for the same lead/contact; draft has `sequence_step=2`, `status=pending_review`

### AC2: Day-7 follow-up created after step-2 is sent
**Given** the step-2 message has been sent
**When** 3 more days have elapsed (n8n Wait node from step-2 send event)
**Then** n8n calls `POST /api/v1/outreach/messages` to create a step-3 draft with `sequence_step=3`

### AC3: No follow-up if lead already replied
**Given** the lead's `leads.status = responded` (reply received before day-4 trigger fires)
**When** n8n's day-4 Wait node fires and calls the FastAPI endpoint
**Then** the endpoint returns 200 with `{"skipped": true, "reason": "lead_already_responded"}`; no step-2 draft created

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests for the skip logic (lead already responded)
- [ ] Integration test with n8n: end-to-end sequence flow (wait simulated with 1s timeout in test)
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets
- [ ] PR squash-merged to master

## Notes

- n8n Wait node: `4 days` for step 2, `3 days` (from step 2 send) for step 3
- Follow-up generation uses the same LangChain outreach chain (EPIC-05) with step-specific prompts
- `POST /api/v1/outreach/messages` accepts `sequence_step` in the request body
