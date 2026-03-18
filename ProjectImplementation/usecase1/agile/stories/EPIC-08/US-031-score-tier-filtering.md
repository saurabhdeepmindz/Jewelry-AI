# US-031: Score Tier Assignment and Lead List Filtering

**Epic:** EPIC-08
**Actor:** `rep`
**Story Points:** 3
**Priority:** Medium
**Status:** Ready

## User Story

As a **rep**,
I want to filter my lead list by score tier and sort by score descending,
so that I always work the highest-potential leads first.

## Acceptance Criteria

### AC1: Score tier assigned deterministically
**Given** a lead receives a score of 72.5
**When** `score_tier` is assigned
**Then** `score_tier = "high"` (≥ 70); a lead with score 55.0 gets `"medium"`; score 30.0 gets `"low"`

### AC2: Filter by score_tier works
**Given** the DB has 20 high, 30 medium, 50 low-tier leads
**When** `GET /api/v1/leads?score_tier=high` is called
**Then** exactly 20 leads are returned (all high-tier); no medium or low leads in the response

### AC3: Sort by score descending works
**Given** the DB has leads with various scores
**When** `GET /api/v1/leads?sort_by=score&order=desc` is called
**Then** leads are returned in descending order by `score`; leads with `score=null` appear last

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: filter + sort → correct results
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Seed data script (`scripts/seed_scoring_data.py`) creates at least 200 labelled examples
- [ ] PR squash-merged to master

## Notes

- Tier thresholds: high ≥ 70, medium 40–69, low < 40 — defined as constants in `src/ml/constants.py`
- `score_tier` computed at write time (not dynamically at query time)
- `null` score leads are always last in sort regardless of sort order
