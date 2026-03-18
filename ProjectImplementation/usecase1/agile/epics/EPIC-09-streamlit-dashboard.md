# EPIC-09: Streamlit Dashboard & UI

**Status:** Ready
**Phase:** Phase 2
**Layer(s):** Layer 5 — Applications
**Priority:** High
**Estimated Size:** L

---

## Problem Statement

The platform's value is invisible without a UI. Sales reps need to see their lead queue, track pipeline progress, and review outreach messages. Managers need to approve or reject drafts and monitor funnel metrics. All of this currently requires querying APIs manually.

## Goal

A Streamlit web application provides a role-aware UI for the platform's three main workflows: lead pipeline management for reps, outreach review for managers, and funnel analytics for managers and admins. The UI calls the FastAPI backend exclusively — no direct DB access.

## Scope (In)

- Lead list page: paginated table with status/score_tier/source filters, sortable by score
- Lead detail page: company info, matched inventory, enriched contacts, CRM activity timeline
- Outreach review queue: list of `pending_review` messages with approve/reject actions
- Analytics page: pipeline funnel chart (ingested → matched → enriched → scored → contacted → responded)
- Streamlit `st.session_state` for JWT token storage and current user context
- `APIClient` wrapper: all HTTP calls via `httpx` to FastAPI; handles 401 refresh
- Role-aware navigation: rep sees only their leads; manager sees all leads
- Error handling: API errors displayed as `st.error()` banners (no raw tracebacks)

## Scope (Out)

- Direct database queries from UI
- Real-time WebSocket push updates (polling is acceptable for Phase 2)
- Mobile-responsive layout
- Admin user management UI (EPIC-11)

---

## Acceptance Criteria

- [ ] AC1: A rep logs in → sees only leads assigned to them, filtered by their role; unassigned leads not visible
- [ ] AC2: Lead detail page shows: company info, matched SKUs, enriched contacts, full CRM activity timeline in descending order
- [ ] AC3: Manager opens outreach review queue → lists all `pending_review` messages; clicking Approve calls `PATCH .../approve` and refreshes the list
- [ ] AC4: Analytics page shows funnel chart with correct counts at each pipeline stage
- [ ] AC5: A 401 response from API → session cleared, user redirected to login page
- [ ] AC6: All API errors surfaced as `st.error()` with a user-friendly message; no Python traceback visible to end users

---

## User Stories

- US-032: Lead pipeline dashboard with filters — `agile/stories/EPIC-09/US-032-lead-pipeline-dashboard.md`
- US-033: Lead detail view with CRM timeline — `agile/stories/EPIC-09/US-033-lead-detail-view.md`
- US-034: Outreach review queue for managers — `agile/stories/EPIC-09/US-034-outreach-review-queue.md`
- US-035: Analytics funnel visualization — `agile/stories/EPIC-09/US-035-analytics-funnel.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| FastAPI backend (internal) | All data via REST API | JWT token from login |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] E2E test: rep login → lead list → detail page → CRM timeline visible
- [ ] E2E test: manager login → review queue → approve → status updates
- [ ] No hardcoded secrets or API URLs
- [ ] PR reviewed and merged to master
