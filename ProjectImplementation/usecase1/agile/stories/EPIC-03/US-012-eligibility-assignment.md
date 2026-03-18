# US-012: Eligible / Not-Eligible Status Assignment

**Epic:** EPIC-03
**Actor:** `system`
**Story Points:** 2
**Priority:** Critical
**Status:** Ready

## User Story

As the **system**,
I want to mark each lead as eligible or not-eligible based on whether inventory matches were found,
so that the enrichment pipeline is only triggered for leads that have real sales potential.

## Acceptance Criteria

### AC1: Lead marked eligible
**Given** the matching engine found at least one inventory match above the minimum score threshold
**When** the eligibility assignment step runs
**Then** `leads.match_status = eligible`, `leads.status = matched`, and a `lead_matched` CRM activity is appended with `{"match_count": N, "top_match_score": X}` payload

### AC2: Lead marked not_eligible
**Given** the matching engine found no matches (or all matches below threshold)
**When** the eligibility assignment step runs
**Then** `leads.match_status = not_eligible`, `leads.status = matched`, and a `lead_not_eligible` CRM activity is appended; no enrichment task is enqueued

### AC3: Not-eligible leads do not proceed to enrichment
**Given** a lead has `match_status = not_eligible`
**When** the LangGraph pipeline evaluates the conditional edge after `match_inventory_node`
**Then** the pipeline routes to `END` and no `enrich_contact` node is executed

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: not-eligible lead → no enrichment task in Celery queue
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- Minimum score threshold: `Settings.MATCH_MIN_SCORE` (default: 0.3)
- LangGraph conditional edge function `_route_after_match` must be a pure function (no DB calls)
