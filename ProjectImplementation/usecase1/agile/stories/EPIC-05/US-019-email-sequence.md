# US-019: 3-Step Email Sequence Generation

**Epic:** EPIC-05
**Actor:** `system`
**Story Points:** 5
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want to generate a 3-step email sequence (day 0, day 4, day 7) for each eligible lead,
so that buyers who don't respond to the first email receive contextually varied follow-ups.

## Acceptance Criteria

### AC1: Three OutreachMessage records created per lead
**Given** outreach generation runs for an eligible, enriched lead
**When** the sequence generation task completes
**Then** 3 `OutreachMessage` rows are created: `sequence_step=1` (initial), `sequence_step=2` (day-4 follow-up), `sequence_step=3` (day-7 follow-up); all with `status=pending_review`

### AC2: Follow-up messages reference the initial
**Given** the 3-message sequence is generated
**When** the step-2 body is inspected
**Then** it acknowledges the prior email (e.g., "following up on my previous message") without repeating the full pitch

### AC3: Step prompts produce varied tone
**Given** step-1 is formal introduction, step-2 is gentle follow-up, step-3 is value-add
**When** all 3 messages are generated
**Then** step-2 body is shorter than step-1 (< 300 chars vs < 500 chars for step-1); step-3 offers something new (e.g., latest inventory update, GIA cert availability)

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: 3 OutreachMessage rows in DB for one lead
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- Sequence generation is a single Celery task with 3 LLM calls (not 3 separate tasks)
- Each step uses a different system prompt variant stored in `src/agents/prompts.py`
- n8n is responsible for *scheduling* step 2 and 3 sends (EPIC-10) — this story only covers generation
