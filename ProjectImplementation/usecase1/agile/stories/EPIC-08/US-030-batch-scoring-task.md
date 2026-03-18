# US-030: Batch Lead Scoring via Celery

**Epic:** EPIC-08
**Actor:** `system`
**Story Points:** 5
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want a Celery task that scores all enriched leads in batch,
so that every eligible lead has a numeric priority score before outreach begins.

## Acceptance Criteria

### AC1: Batch task scores all enriched leads
**Given** 50 leads with `status=enriched` and no existing score
**When** `score_leads_batch` Celery task runs on the `ml` queue
**Then** all 50 leads have `score` (float 0–100) and `score_tier` (high/medium/low) populated; `leads.status` remains `enriched` (scoring does not change pipeline status)

### AC2: Previously scored leads not re-scored
**Given** 10 leads already have `score` set
**When** `score_leads_batch` runs
**Then** those 10 leads are skipped; only un-scored leads are processed; logged as `"Skipping already-scored leads: 10"`

### AC3: lead_scored CRM event appended per lead
**Given** batch scoring completes
**When** each lead's score is written
**Then** a `lead_scored` CRM event is appended for each lead with payload `{"score": 82.4, "score_tier": "high"}`

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: 10 leads → batch task → all scored
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets
- [ ] PR squash-merged to master

## Notes

- Task runs on `ml` queue with `concurrency=2` (CPU-bound; don't parallelize aggressively)
- Batch size: process 100 leads per task invocation; pagination via `offset`
- Model loaded once at task start via `mlflow.xgboost.load_model(Settings.ML_MODEL_VERSION)`; not reloaded per lead
- Score = `model.predict_proba(feature_matrix)[:, 1] * 100` → rounded to 1 decimal place
