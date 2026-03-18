# US-045: MLflow Experiment Logging for Scoring Runs

**Epic:** EPIC-13
**Actor:** `system`
**Story Points:** 5
**Priority:** Medium
**Status:** Draft

## User Story

As the **system**,
I want all scoring model training runs logged to MLflow with parameters, metrics, and artifacts,
so that every experiment is reproducible and the team can compare runs side by side.

## Acceptance Criteria

### AC1: Training run creates an MLflow run with all metadata
**Given** `scripts/train_scoring_model.py` is executed
**When** the run completes
**Then** an MLflow run exists in experiment `jewelry-ai-lead-scoring` with logged: `n_estimators`, `max_depth`, `learning_rate` (params); `auc`, `f1`, `precision`, `recall` (metrics); model artifact

### AC2: Feature importances logged
**Given** the training run completes
**When** the MLflow run is inspected
**Then** feature importance values for all 9 features are logged as a JSON artifact (`feature_importances.json`)

### AC3: Failed run marked as failed in MLflow
**Given** the training run raises an exception after starting
**When** the exception is caught
**Then** `mlflow.end_run(status="FAILED")` is called; the run appears in MLflow UI with status FAILED (not RUNNING)

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests: mock MLflow client; verify `log_param`, `log_metric` called correctly
- [ ] Integration test: training runs → MLflow run visible in UI
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] `MLFLOW_TRACKING_URI` from `Settings` — never hardcoded
- [ ] PR squash-merged to master

## Notes

- Use `mlflow.start_run()` as context manager: `with mlflow.start_run() as run:`
- Artifact store: MinIO S3-compatible (`MLFLOW_S3_ENDPOINT_URL` in settings)
- Experiment created automatically if it doesn't exist: `mlflow.set_experiment("jewelry-ai-lead-scoring")`
