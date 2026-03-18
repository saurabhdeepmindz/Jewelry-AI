# US-032: Lead Pipeline Dashboard with Filters

**Epic:** EPIC-09
**Actor:** `rep`
**Story Points:** 5
**Priority:** High
**Status:** Ready

## User Story

As a **rep**,
I want a dashboard showing my leads with status and score_tier filters,
so that I can quickly focus on the leads that need my attention today.

## Acceptance Criteria

### AC1: Lead list loads with assigned leads only
**Given** a rep is logged in
**When** they navigate to the Leads page
**Then** only leads where `assigned_to = current_user.id` are displayed; a paginated table shows: company name, country, status, score, score_tier, created_at

### AC2: Filters work correctly
**Given** the rep selects `status=enriched` and `score_tier=high` from the filter dropdowns
**When** the filter is applied
**Then** the table updates to show only leads matching both filters; count shows e.g. `"Showing 8 of 8 leads"`

### AC3: Error from API displayed gracefully
**Given** the FastAPI backend returns a 500 error
**When** the Streamlit page tries to load leads
**Then** `st.error("Unable to load leads. Please try again.")` is displayed; no Python traceback is shown

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests for `APIClient.get_leads()` with mocked httpx
- [ ] E2E test: rep login → leads page loads → filter applied → filtered results shown
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded API URLs — use `Settings.API_BASE_URL`
- [ ] PR squash-merged to master

## Notes

- Streamlit session state: `st.session_state.jwt_token` stored after login
- `APIClient` is a thin wrapper over `httpx.Client` — no business logic
- Pagination: `st.session_state.leads_page` tracks current page; prev/next buttons
