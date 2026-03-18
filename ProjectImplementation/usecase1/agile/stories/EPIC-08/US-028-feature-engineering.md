# US-028: Feature Engineering for Scoring Model

**Epic:** EPIC-08
**Actor:** `system`
**Story Points:** 5
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want to extract and transform 9 structured features from each enriched lead,
so that the XGBoost scoring model has a consistent, well-defined input vector.

## Acceptance Criteria

### AC1: Feature vector extracted for an enriched lead
**Given** a lead with enriched contacts and at least one inventory match
**When** `FeatureEngineer.extract(lead_id)` is called
**Then** a dict with all 9 features is returned with no null values (nulls replaced by defaults)

### AC2: Null handling — missing contact data defaults gracefully
**Given** a lead with zero enriched contacts
**When** features are extracted
**Then** `has_email=0`, `email_verified=0`, `contact_count=0`; other features computed normally; no exception raised

### AC3: Features match the DB_SCHEMA and LLD definitions
**Given** the 9 features defined in LLD.md
**When** the feature vector is inspected
**Then** it contains exactly: `match_score`, `match_count`, `has_email`, `email_verified`, `contact_count`, `carat_weight_avg`, `country_tier`, `source_tier`, `days_since_ingestion`

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Unit tests cover all null/missing data scenarios
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded magic values — thresholds in `Settings` or constants
- [ ] PR squash-merged to master

## Notes

- `country_tier`: 1=Tier1 (US/UK/EU), 2=Tier2 (India/UAE/HK), 3=Other (default: 3)
- `source_tier`: 1=gmt/trade_book, 2=rapid_list, 3=manual/api (default: 3)
- `days_since_ingestion` = `(NOW() - leads.created_at).days`
- All features are float32 for XGBoost compatibility
