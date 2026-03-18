# US-029: XGBoost Model Training and MLflow Registration

**Epic:** EPIC-08
**Actor:** `system`
**Story Points:** 8
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want to train an XGBoost lead scoring model and register it in MLflow,
so that the scoring pipeline always uses a versioned, reproducible model artifact.

## Acceptance Criteria

### AC1: Training run logged to MLflow
**Given** the training script `scripts/train_scoring_model.py` is run with seed data
**When** training completes
**Then** an MLflow run is created with logged parameters (`n_estimators`, `max_depth`, `learning_rate`), metrics (`auc`, `f1`, `precision`, `recall`), and model artifact

### AC2: Model registered in MLflow registry
**Given** the training run completes with AUC ≥ 0.65
**When** the registration step runs
**Then** the model is registered as `lead-score-model` in MLflow registry with `stage=Staging`

### AC3: Model loadable for inference
**Given** the model is registered in MLflow
**When** `mlflow.xgboost.load_model("models:/lead-score-model/Production")` is called
**Then** the model loads successfully and returns a probability array for a 9-feature input matrix

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] `scripts/train_scoring_model.py` committed and documented
- [ ] Unit test: feature vector → model predicts a float between 0.0 and 1.0
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] AUC ≥ 0.65 on seed data (documented in MLflow run)
- [ ] No hardcoded secrets — MLflow URI from `Settings`
- [ ] PR squash-merged to master

## Notes

- Training data: synthetic seed from `scripts/seed_scoring_data.py` (EPIC-08 US-031 prerequisite)
- XGBoost hyperparameters: `n_estimators=100`, `max_depth=4`, `learning_rate=0.1` as defaults
- Probability calibration: `sklearn.calibration.CalibratedClassifierCV` wraps XGBoost for score = probability × 100
- MLflow experiment name: `jewelry-ai-lead-scoring`
