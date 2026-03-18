# US-013: Match Results Stored in lead_inventory_matches

**Epic:** EPIC-03
**Actor:** `system`
**Story Points:** 2
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want all inventory matches persisted in the `lead_inventory_matches` table with scores and reasons,
so that outreach generation can reference the exact matched SKUs and match rationale.

## Acceptance Criteria

### AC1: Match rows created with correct data
**Given** the matching engine finds 3 inventory items for a lead
**When** the results are persisted
**Then** 3 rows are created in `lead_inventory_matches` with correct `lead_id`, `inventory_id`, `match_score`, `match_method`, and `match_reason` JSONB

### AC2: Duplicate match not re-inserted
**Given** a `(lead_id, inventory_id)` pair already exists in `lead_inventory_matches`
**When** the matching engine runs again for the same lead
**Then** no duplicate row is inserted; the unique index `idx_matches_lead_inventory` prevents it; an upsert is performed instead

### AC3: match_method field set correctly
**Given** a match was found via the rule engine only
**Then** `match_method = "rule"`; if found via pgvector only → `"embedding"`; if both → `"hybrid"`

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: match results in DB with correct JSONB
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Alembic migration: `idx_matches_lead_inventory` unique index confirmed
- [ ] PR squash-merged to master

## Notes

- Upsert pattern: `INSERT ... ON CONFLICT (lead_id, inventory_id) DO UPDATE SET match_score = EXCLUDED.match_score`
- `match_reason` must always be a non-null JSONB object — never store `null` or `{}`
