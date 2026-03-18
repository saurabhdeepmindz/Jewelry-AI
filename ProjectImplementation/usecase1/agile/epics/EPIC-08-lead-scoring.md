# EPIC-08: Lead Scoring & Prioritization

**Status:** Ready
**Phase:** Phase 2
**Layer(s):** Layer 3 — Business Services, Layer 7 — AI/Intelligence
**Priority:** High
**Estimated Size:** L

---

## Problem Statement

With hundreds of eligible leads, sales reps have no objective way to prioritize who to contact first. A lead that is a perfect carat-and-cut match with a verified corporate email should be worked before a loose match with an unverified Gmail address. Currently, all leads look the same in the pipeline.

## Goal

An XGBoost model scores every enriched lead on a 0–100 scale based on inventory match quality, company profile signals, and contact data quality. Leads are bucketed into `high`, `medium`, or `low` tiers. Reps see a prioritized lead queue with scores, enabling the highest-potential leads to be worked first.

## Scope (In)

- Feature engineering: 9 features from `leads`, `contacts`, `lead_inventory_matches` tables
- XGBoost classifier with probability calibration (score = probability × 100)
- Tier assignment: high ≥ 70, medium 40–69, low < 40
- MLflow experiment logging (run parameters, metrics, model artifact)
- Celery task: `score_leads_batch` on `ml` queue
- `leads.score` and `leads.score_tier` updated after scoring
- `lead_scored` CRM activity appended with `{score, score_tier}` payload
- `GET /api/v1/leads` supports `?sort_by=score&order=desc` and `?score_tier=high` filter
- Seed synthetic training data script (`scripts/seed_scoring_data.py`) for dev/demo

## Scope (Out)

- Deep learning models (XGBoost is sufficient for Phase 2)
- Real-time scoring on lead ingestion (batch scoring via Celery is the Phase 2 approach)
- A/B model comparison (EPIC-13)

---

## Acceptance Criteria

- [ ] AC1: `score_leads_batch` Celery task runs on all `status=enriched` leads → `leads.score` and `leads.score_tier` populated for each
- [ ] AC2: Tier assignment is deterministic: score ≥ 70 → `high`, 40–69 → `medium`, < 40 → `low`
- [ ] AC3: `lead_scored` CRM activity appended with `{"score": 82.4, "score_tier": "high"}` payload
- [ ] AC4: `GET /api/v1/leads?score_tier=high&sort_by=score&order=desc` returns only high-tier leads sorted by score descending
- [ ] AC5: MLflow run logged with feature importances, AUC score, and model artifact path
- [ ] AC6: Synthetic seed data script produces at least 200 labelled training examples for dev environment

---

## User Stories

- US-028: Feature engineering for scoring model — `agile/stories/EPIC-08/US-028-feature-engineering.md`
- US-029: XGBoost model training and MLflow registration — `agile/stories/EPIC-08/US-029-model-training.md`
- US-030: Batch lead scoring via Celery — `agile/stories/EPIC-08/US-030-batch-scoring-task.md`
- US-031: Score tier assignment and lead list filtering — `agile/stories/EPIC-08/US-031-score-tier-filtering.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| MLflow (self-hosted) | Experiment tracking, model registry | `MLFLOW_TRACKING_URI` in settings |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] Model artifact registered in MLflow model registry
- [ ] Scoring task tested end-to-end with real DB in staging
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
