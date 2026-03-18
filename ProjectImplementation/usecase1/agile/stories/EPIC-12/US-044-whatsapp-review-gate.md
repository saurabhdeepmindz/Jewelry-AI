# US-044: WhatsApp Outreach Review Gate

**Epic:** EPIC-12
**Actor:** `manager`
**Story Points:** 2
**Priority:** Medium
**Status:** Draft

## User Story

As a **manager**,
I want WhatsApp outreach drafts to require the same review and approval as emails,
so that no WhatsApp message is sent to a buyer without human oversight.

## Acceptance Criteria

### AC1: WhatsApp draft held in pending_review
**Given** `HUMAN_REVIEW_REQUIRED=true`
**When** the outreach generation agent creates a WhatsApp `OutreachMessage`
**Then** `status=pending_review`; no Twilio call made; message appears in the outreach review queue alongside email drafts

### AC2: WhatsApp drafts visible in review queue
**Given** there are both email and WhatsApp pending_review messages
**When** a manager opens the review queue (Streamlit or API)
**Then** both channel types are listed; `channel=whatsapp` messages are visually distinguished (e.g., WhatsApp icon)

### AC3: Rep cannot approve WhatsApp messages
**Given** a rep calls the approve endpoint for a WhatsApp message
**When** the request is processed
**Then** 403 response returned; approval requires `ROLE_MANAGER` or `ROLE_ADMIN` regardless of channel

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: WhatsApp draft → review queue → approve → Twilio called
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets
- [ ] PR squash-merged to master

## Notes

- The same `OutreachMessage` model handles both email and WhatsApp — differentiated by `channel` field
- Approval endpoint is channel-agnostic: `PATCH /api/v1/outreach/messages/{id}/approve`
- After approval, the system routes to SendGrid (email) or Twilio (whatsapp) based on `channel`
