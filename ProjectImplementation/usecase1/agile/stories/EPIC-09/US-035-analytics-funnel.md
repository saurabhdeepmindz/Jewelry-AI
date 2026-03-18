# US-035: Analytics Funnel Visualization

**Epic:** EPIC-09
**Actor:** `manager`
**Story Points:** 3
**Priority:** Medium
**Status:** Ready

## User Story

As a **manager**,
I want to see the lead pipeline funnel as a chart,
so that I can identify bottlenecks at a glance and take action before the pipeline stalls.

## Acceptance Criteria

### AC1: Funnel chart displays all pipeline stages
**Given** a manager navigates to the Analytics page
**When** the funnel data loads from `GET /api/v1/analytics/funnel`
**Then** a bar or funnel chart is rendered with counts for each stage: ingested, matched, enriched, scored, contacted, responded, closed

### AC2: Funnel data reflects current DB state
**Given** 100 leads in the DB at various stages
**When** the analytics page loads
**Then** the chart counts match a direct DB query of `SELECT status, COUNT(*) FROM leads GROUP BY status` (no stale cache)

### AC3: Empty pipeline handled gracefully
**Given** no leads exist in the DB
**When** the analytics page loads
**Then** a message is shown: `"No leads in pipeline yet."` — no empty chart or crash

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit test: funnel API returns correct stage counts
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or API URLs
- [ ] PR squash-merged to master

## Notes

- Chart library: `st.bar_chart()` or `plotly` via `st.plotly_chart()` — keep dependency lightweight
- Cache analytics data in Streamlit with `@st.cache_data(ttl=300)` — 5-minute TTL
- Rep role sees only their own funnel counts (filtered by `assigned_to`); manager sees global
