# US-010: Rule-Based Inventory Matching

**Epic:** EPIC-03
**Actor:** `system`
**Story Points:** 5
**Priority:** Critical
**Status:** Ready

## User Story

As the **system**,
I want to match each ingested lead against available inventory using explicit business rules,
so that only buyers whose stated preferences align with current stock are flagged as eligible.

## Acceptance Criteria

### AC1: Matching lead found via rules
**Given** a lead with `buyer_category="RBC diamonds"` and preferred carat range 1.0–2.0
**When** the rule-based matching engine runs
**Then** all `inventory` rows with `stone_type=RBC`, `carat_weight` between 1.0 and 2.0, and `is_available=true` are returned as matches; `match_reason` JSONB contains `{"stone_type": true, "carat_range": true}`

### AC2: No matching inventory
**Given** a lead whose buyer preferences don't match any available inventory
**When** the rule-based matching engine runs
**Then** an empty match list is returned; `match_reason` reflects which fields failed: `{"stone_type": false, "carat_range": true}`

### AC3: Unavailable inventory excluded
**Given** an inventory item with `is_available=false` (sold or reserved)
**When** the matching engine runs
**Then** that item is never included in match results, regardless of other field matches

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test against real test DB
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- Rule engine implemented as `InventoryMatchService.match_by_rules(lead, inventory_items) → list[MatchResult]`
- Carat range tolerance: ±10% of stated preference if no explicit range provided
- `match_score` for rule-based matches = fraction of matching fields (e.g., 2/3 fields → 0.67)
