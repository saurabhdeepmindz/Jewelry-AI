# US-033: Lead Detail View with CRM Timeline

**Epic:** EPIC-09
**Actor:** `rep`
**Story Points:** 5
**Priority:** High
**Status:** Ready

## User Story

As a **rep**,
I want to view a lead's full detail including matched inventory, enriched contacts, and activity timeline,
so that I have all context in one place before making a call or sending a follow-up.

## Acceptance Criteria

### AC1: Detail page shows all lead sections
**Given** a rep clicks on a lead from the pipeline dashboard
**When** the lead detail page loads
**Then** the page displays: company info section, matched inventory items (SKU, carat, stone type, price), enriched contacts (name, email, phone, title), and CRM activity timeline

### AC2: CRM timeline in descending order
**Given** the lead has 8 CRM activity events
**When** the timeline section renders
**Then** events are displayed newest-first with event type, timestamp, actor, and payload summary

### AC3: Missing sections handled gracefully
**Given** a lead has no enriched contacts yet
**When** the contacts section renders
**Then** a message is shown: `"No contacts enriched yet."` — not an empty section or crash

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests for each section's data-fetching function
- [ ] E2E test: lead detail page loads all sections
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or API URLs
- [ ] PR squash-merged to master

## Notes

- Lead detail = 3 API calls in parallel: `GET /leads/{id}`, `GET /leads/{id}/contacts`, `GET /crm/{id}/activity`
- Use `st.columns()` layout: left column = company info + contacts; right column = matched inventory + timeline
- Timestamps rendered as relative time (e.g., "2 hours ago") using `humanize` library
