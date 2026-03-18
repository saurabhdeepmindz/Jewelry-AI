# US-046: Model Registry and Version Management

**Epic:** EPIC-13
**Actor:** `admin`
**Story Points:** 3
**Priority:** Medium
**Status:** Draft

## User Story

As an **admin**,
I want scoring model versions tracked in the MLflow Model Registry with Staging and Production stages,
so that model promotion is a controlled, auditable process.

## Acceptance Criteria

### AC1: Model registered after training
**Given** a training run completes with AUC ≥ 0.65
**When** `mlflow.register_model()` is called at the end of training
**Then** the model is registered under name `lead-score-model` with `stage=None` (newly registered)

### AC2: Promote to Staging via script
**Given** the model is registered as version 2 with `stage=None`
**When** `python scripts/promote_model.py --version 2 --stage Staging` is run
**Then** version 2 transitions to `stage=Staging`; MLflow UI shows version 2 as Staging

### AC3: Promote Staging to Production
**Given** version 2 is in Staging and has been validated
**When** `python scripts/promote_model.py --version 2 --stage Production` is run
**Then** version 2 transitions to Production; the previous Production version is archived automatically; scoring tasks immediately pick up the new model

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] `scripts/promote_model.py` committed with `--version` and `--stage` arguments
- [ ] Unit test: model registry transition tested with mocked MLflow client
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets
- [ ] PR squash-merged to master

## Notes

- Model name constant: `ML_MODEL_NAME = "lead-score-model"` in `src/ml/constants.py`
- Scoring task loads via: `mlflow.xgboost.load_model(f"models:/{ML_MODEL_NAME}/{Settings.ML_MODEL_VERSION}")`
- MLflow model stage transitions use `MlflowClient.transition_model_version_stage()`
