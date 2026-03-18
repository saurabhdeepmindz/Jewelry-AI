# EPIC-10: n8n Workflow Automation

**Status:** Ready
**Phase:** Phase 2
**Layer(s):** Layer 4 — Workflows, Layer 2 — Integration
**Priority:** Medium
**Estimated Size:** M

---

## Problem Statement

A single outreach email rarely converts. The proven approach is a structured 3-step sequence: initial email (day 0), first follow-up (day 4), second follow-up (day 7). Currently this cadence is managed manually by reps who often forget or send inconsistently.

## Goal

n8n orchestrates the multi-step email sequence automatically. When a message is sent (step 1), n8n schedules step 2 (day 4) and step 3 (day 7) follow-ups. If the buyer replies at any point, n8n is notified and the sequence is cancelled — preventing awkward follow-ups to already-engaged leads.

## Scope (In)

- n8n self-hosted via Docker Compose (`n8n` service in `docker-compose.yml`)
- FastAPI triggers n8n workflow via `POST /api/v1/workflows/trigger` webhook
- n8n workflow: 3-node sequence with Wait nodes (day 4, day 7 delays)
- Each n8n step calls `POST /api/v1/outreach/messages` to create the follow-up draft
- Reply detection: `email_replied` webhook event cancels the active n8n sequence
- `GET /api/v1/workflows/status/{workflow_execution_id}` — check sequence status
- Sequence state tracked in `outreach_messages.sequence_step` (1, 2, 3)

## Scope (Out)

- n8n visual workflow editor usage (workflow JSON is version-controlled)
- WhatsApp sequences (EPIC-12)
- LinkedIn sequence automation (out of scope entirely)
- n8n cloud (self-hosted only)

---

## Acceptance Criteria

- [ ] AC1: A sent day-0 email triggers n8n webhook → n8n schedules day-4 follow-up; `sequence_step=2` draft created at correct time
- [ ] AC2: Day-4 follow-up sent → n8n schedules day-7 follow-up; `sequence_step=3` draft created
- [ ] AC3: Buyer replies before day 4 → `email_replied` event received → n8n workflow execution cancelled; no day-4 or day-7 emails generated
- [ ] AC4: n8n workflow JSON is committed to version control under `src/workflows/n8n/`
- [ ] AC5: FastAPI `POST /api/v1/workflows/trigger` returns `workflow_execution_id` for status tracking
- [ ] AC6: n8n service starts cleanly via `docker compose up` with no manual configuration steps

---

## User Stories

- US-036: n8n webhook trigger integration — `agile/stories/EPIC-10/US-036-n8n-webhook-trigger.md`
- US-037: Day-4 and day-7 follow-up generation — `agile/stories/EPIC-10/US-037-followup-sequence.md`
- US-038: Sequence cancellation on reply — `agile/stories/EPIC-10/US-038-sequence-cancel-on-reply.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| n8n (self-hosted) | Multi-step sequence orchestration | `N8N_WEBHOOK_URL` in settings |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] n8n workflow tested end-to-end in staging (day-4 wait simulated with short timeout)
- [ ] Workflow JSON committed to `src/workflows/n8n/`
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
