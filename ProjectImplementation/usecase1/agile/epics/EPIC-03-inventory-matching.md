# EPIC-03: AI Inventory Matching Engine

**Status:** Ready
**Phase:** Phase 1
**Layer(s):** Layer 3 — Business Services, Layer 7 — AI/Intelligence
**Priority:** Critical
**Estimated Size:** L

---

## Problem Statement

Not every buyer is a match for Shivam Jewels' current inventory. Without an automated matching engine, sales reps manually compare each lead's buyer profile against the diamond catalog — a time-consuming, error-prone task. Outreach to non-matching buyers wastes enrichment credits and damages sender reputation.

## Goal

For every ingested lead, the platform automatically compares the buyer profile against available inventory using rule-based filters (stone type, carat range, certification) combined with pgvector semantic search. Leads are marked `eligible` or `not_eligible` before any enrichment is triggered, ensuring downstream credits are never wasted.

## Scope (In)

- Rule-based matching: stone_type, carat_weight range, certification filter
- Semantic matching: pgvector IVFFlat cosine similarity on `leads.embedding`
- Hybrid scoring: combine rule score (0–1) and cosine similarity into `match_score`
- Store results in `lead_inventory_matches` table with `match_reason` JSONB
- Set `leads.match_status` to `eligible` or `not_eligible`
- Set `leads.status` to `matched`
- CRM activity: `lead_matched` or `lead_not_eligible` event appended
- OpenAI embedding generation for lead text (company profile) via `text-embedding-3-small`
- Minimum match threshold: configurable via `Settings.MATCH_MIN_SCORE`

## Scope (Out)

- Manual override of match results (EPIC-09 dashboard feature)
- Inventory CRUD management (separate admin feature, not in scope for Phase 1)
- Machine-learning-trained matching model (rule + embedding is sufficient for Phase 1)

---

## Acceptance Criteria

- [ ] AC1: A lead whose buyer profile matches available inventory → `match_status=eligible`, at least one `lead_inventory_matches` row created
- [ ] AC2: A lead with no matching inventory → `match_status=not_eligible`, no enrichment task triggered
- [ ] AC3: Match score is computed correctly: rule_score (boolean fields) + cosine similarity; stored as `match_score` float 0.0–1.0
- [ ] AC4: `match_reason` JSONB contains field-by-field rule results (e.g., `{"stone_type": true, "carat_range": false}`)
- [ ] AC5: OpenAI embedding is generated once per lead and stored in `leads.embedding`; re-matching does not re-generate the embedding if already set
- [ ] AC6: Match engine respects `is_available=true` filter on inventory — sold/reserved items are never matched

---

## User Stories

- US-010: Rule-based inventory matching — `agile/stories/EPIC-03/US-010-rule-based-matching.md`
- US-011: Semantic matching via pgvector embeddings — `agile/stories/EPIC-03/US-011-pgvector-semantic-matching.md`
- US-012: Eligible / not-eligible status assignment — `agile/stories/EPIC-03/US-012-eligibility-assignment.md`
- US-013: Match results stored in lead_inventory_matches — `agile/stories/EPIC-03/US-013-match-results-storage.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| OpenAI Embeddings API (`text-embedding-3-small`) | Generate 1536-dim embedding for lead profile text | `OPENAI_KEY_ENCRYPTED` in `api_key_configs` |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] pgvector extension confirmed active in migration
- [ ] OpenAI embedding tested end-to-end in staging (not just mocked)
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
