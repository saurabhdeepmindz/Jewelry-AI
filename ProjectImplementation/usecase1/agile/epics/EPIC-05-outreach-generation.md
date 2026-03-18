# EPIC-05: AI Outreach Generation & Review

**Status:** Ready
**Phase:** Phase 1
**Layer(s):** Layer 3 — Business Services, Layer 7 — AI/Intelligence
**Priority:** Critical
**Estimated Size:** L

---

## Problem Statement

Writing personalized outreach emails for each buyer is the most time-consuming step in the sales workflow. A generic template performs poorly; a truly personalized message requires reading the buyer's profile, matching inventory, and crafting a compelling narrative. This is where AI adds the most value.

## Goal

For every enriched, eligible lead, the AI outreach agent generates a personalized email (and optional WhatsApp draft) referencing the matched SKUs and buyer profile. The draft sits in `status=pending_review` until a manager or admin approves it, at which point the Outreach Service sends it. Rejected drafts include a reason and can be regenerated.

## Scope (In)

- LangChain LCEL chain: retrieve lead context → build prompt → call GPT-4o-mini → validate output
- 3-step email sequence: initial (day 0), follow-up 1 (day 4), follow-up 2 (day 7)
- `OutreachMessage` created with `status=pending_review`, `sequence_step=1`
- Human review gate: `HUMAN_REVIEW_REQUIRED=true` → message held until approval
- `PATCH /api/v1/outreach/messages/{id}/approve` — manager/admin only
- `PATCH /api/v1/outreach/messages/{id}/reject` — with `rejection_reason`
- Fallback LLM: if OpenAI fails → Anthropic Claude Haiku
- CRM activity: `outreach_drafted` on create; `outreach_approved` or `outreach_rejected` on decision
- System prompt: reference matched SKU details, buyer name, company, stone preference

## Scope (Out)

- Actual email sending (EPIC-06 — SendGrid)
- WhatsApp outreach (EPIC-12 — Twilio)
- n8n follow-up sequence automation (EPIC-10)
- A/B testing of prompts (EPIC-13 — MLflow)

---

## Acceptance Criteria

- [ ] AC1: A lead with enriched contact and matched inventory → `OutreachMessage` created with `status=pending_review`; body references at least one matched SKU by carat weight and stone type
- [ ] AC2: `HUMAN_REVIEW_REQUIRED=true` → message is NOT sent; it remains `pending_review` until explicitly approved
- [ ] AC3: Manager POSTs approve → `status=approved`, `approved_by` set, `approved_at` timestamp set, `outreach_approved` CRM event appended
- [ ] AC4: Manager POSTs reject → `status=rejected`, `rejection_reason` stored, `outreach_rejected` CRM event appended
- [ ] AC5: OpenAI API fails → Anthropic fallback is attempted; if both fail, `system_error` CRM event logged and task retried
- [ ] AC6: Generated body must contain: buyer's first name, company name, at least one SKU reference, a clear call to action

---

## User Stories

- US-018: AI email draft generation via LangChain — `agile/stories/EPIC-05/US-018-ai-email-draft.md`
- US-019: 3-step email sequence generation — `agile/stories/EPIC-05/US-019-email-sequence.md`
- US-020: Human review gate (pending_review status) — `agile/stories/EPIC-05/US-020-human-review-gate.md`
- US-021: Manager approval and rejection workflow — `agile/stories/EPIC-05/US-021-approval-rejection.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| OpenAI GPT-4o-mini | Primary outreach generation | `OPENAI_KEY_ENCRYPTED` |
| Anthropic Claude Haiku | Fallback LLM when OpenAI fails | `ANTHROPIC_KEY_ENCRYPTED` |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] OpenAI generation tested end-to-end in staging (not just mocked)
- [ ] Prompt reviewed and validated to produce quality output on 5 sample leads
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
