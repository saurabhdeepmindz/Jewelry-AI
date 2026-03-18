# EPIC-13: MLflow Experiment Tracking

**Status:** Draft
**Phase:** Phase 3
**Layer(s):** Layer 2 — Integration (MLflow)
**Priority:** Medium
**Estimated Size:** M

---

## Problem Statement

The XGBoost scoring model in EPIC-08 is trained once and deployed. As lead volume grows, the model's accuracy drifts and needs retraining. Without experiment tracking, there is no way to compare model versions, reproduce training runs, or promote the best-performing model to production with confidence.

## Goal

All scoring model training runs are logged to MLflow with parameters, metrics, and model artifacts. The MLflow Model Registry tracks version history. A champion/challenger comparison workflow lets the data team promote a better model to production with a single command — without changing application code.

## Scope (In)

- MLflow self-hosted: `mlflow` service in Docker Compose with PostgreSQL backend + S3-compatible artifact store
- `mlflow.start_run()` wrapping all `train_scoring_model` invocations
- Log: hyperparameters (n_estimators, max_depth, learning_rate), metrics (AUC, F1, precision, recall), feature importances
- Model registration: `mlflow.xgboost.log_model()` → `models:/lead-score-model/Production`
- `scripts/promote_model.py`: transitions a staging model to Production
- Champion/challenger: load model by alias (`Production` or `Staging`) at scoring time
- Model version readable from `Settings.ML_MODEL_VERSION` (default: `Production`)

## Scope (Out)

- Automated retraining pipelines / scheduled retraining (out of scope; manual trigger only)
- A/B testing outreach prompts (prompt variation is out of scope for MLflow)
- Feature store (training features come directly from the DB in Phase 3)

---

## Acceptance Criteria

- [ ] AC1: A training run logs all hyperparameters, AUC ≥ 0.70, and registers the model artifact in MLflow
- [ ] AC2: `scripts/promote_model.py --version 2` transitions model version 2 from Staging → Production in the registry
- [ ] AC3: Scoring task loads model by `Settings.ML_MODEL_VERSION` alias — changing the setting from `Production` to `Staging` switches the active model without code changes
- [ ] AC4: MLflow UI accessible at `http://localhost:5000` via Docker Compose
- [ ] AC5: Two training runs with different hyperparameters can be compared side-by-side in MLflow UI
- [ ] AC6: Model artifact is stored in the local MinIO (S3-compatible) artifact store, not on the local filesystem

---

## User Stories

- US-045: MLflow experiment logging for scoring runs — `agile/stories/EPIC-13/US-045-mlflow-experiment-logging.md`
- US-046: Model registry and version management — `agile/stories/EPIC-13/US-046-model-registry.md`
- US-047: Champion/challenger model comparison — `agile/stories/EPIC-13/US-047-champion-challenger.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| MLflow (self-hosted) | Experiment tracking, model registry | `MLFLOW_TRACKING_URI` |
| MinIO (self-hosted, S3-compatible) | Artifact storage | `MLFLOW_S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] MLflow + MinIO tested end-to-end in staging
- [ ] At least 2 model versions registered and compared in MLflow UI
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
