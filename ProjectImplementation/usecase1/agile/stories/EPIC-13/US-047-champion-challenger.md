# US-047: Champion / Challenger Model Comparison

**Epic:** EPIC-13
**Actor:** `admin`
**Story Points:** 5
**Priority:** Low
**Status:** Draft

## User Story

As an **admin**,
I want to compare a new (challenger) model against the current production (champion) model before promoting it,
so that I only promote models that genuinely improve scoring quality.

## Acceptance Criteria

### AC1: Comparison script runs both models on the same holdout set
**Given** a challenger model in Staging and the champion in Production
**When** `python scripts/compare_models.py --holdout-file data/holdout.csv` is run
**Then** both models score the same leads; a comparison table is printed with: version, AUC, F1, precision, recall for each model

### AC2: Challenger improvement logged to MLflow
**Given** the comparison is run
**When** the results are recorded
**Then** an MLflow run is created in experiment `jewelry-ai-model-comparison` with both models' metrics and a `comparison_winner` tag (champion or challenger)

### AC3: No automatic promotion
**Given** the challenger model outperforms the champion
**When** the comparison script finishes
**Then** no automatic promotion happens; the script prints a recommendation and the admin must explicitly run `promote_model.py` to promote

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] `scripts/compare_models.py` committed with `--holdout-file` argument
- [ ] Unit test: both models loaded, metrics computed, comparison table generated
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets
- [ ] PR squash-merged to master

## Notes

- Holdout set: at least 50 labelled leads not used in training
- Metrics computed using `sklearn.metrics`: `roc_auc_score`, `f1_score`, `precision_score`, `recall_score`
- `comparison_winner` = "challenger" if challenger AUC > champion AUC by > 0.02 (meaningful improvement threshold)
