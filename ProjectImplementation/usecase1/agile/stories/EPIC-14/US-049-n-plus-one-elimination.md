# US-049: N+1 Query Elimination

**Epic:** EPIC-14
**Actor:** `system`
**Story Points:** 5
**Priority:** Medium
**Status:** Draft

## User Story

As the **system**,
I want lead list queries to load related contacts and outreach messages in a single query,
so that the API responds consistently fast regardless of how many leads are on the page.

## Acceptance Criteria

### AC1: Lead list uses selectinload for contacts
**Given** a page of 20 leads is requested
**When** `LeadRepository.list_by_status()` executes
**Then** exactly 2 SQL queries are issued (1 for leads, 1 for all contacts via `selectinload`) — not 21 queries; confirmed via `EXPLAIN ANALYZE` or SQL echo log count

### AC2: Lead detail loads all relations in 3 queries max
**Given** `GET /api/v1/leads/{id}` is called
**When** the lead and all relations are loaded
**Then** at most 3 queries: leads + contacts + outreach_messages; no per-row subqueries

### AC3: Performance benchmark passes
**Given** the DB has 10,000 leads with 3 contacts each
**When** `GET /api/v1/leads?limit=50` is benchmarked
**Then** p99 response time < 800ms (cache miss); p99 < 50ms (cache hit)

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] `EXPLAIN ANALYZE` output reviewed for all hot queries and documented
- [ ] Unit tests: repository methods verified with SQL echo counting queries
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets
- [ ] PR squash-merged to master

## Notes

- Use `selectinload` for `contacts` and `outreach_messages` on `LeadORM`
- Use `joinedload` only for single-row relations (e.g., `assigned_to` user)
- Avoid `lazy="dynamic"` — it causes N+1 in async context
- Add `idx_contacts_lead_id` and `idx_outreach_lead_id` indexes if missing (confirm in migrations)
