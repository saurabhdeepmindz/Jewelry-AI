# US-008: Async Ingestion via Celery

**Epic:** EPIC-02
**Actor:** `system`
**Story Points:** 3
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want lead ingestion to run asynchronously via a Celery task,
so that large CSV uploads return immediately to the caller without blocking the API.

## Acceptance Criteria

### AC1: Upload returns immediately with job_id
**Given** a rep uploads a valid CSV
**When** `POST /api/v1/leads/upload` is called
**Then** a 202 response is returned within 500ms, containing a `job_id` (UUID) for polling

### AC2: Celery task processes the file
**Given** the upload has returned a `job_id`
**When** the Celery worker processes the `ingest_lead_file` task from the `ingestion` queue
**Then** all valid rows are persisted as `Lead` records and a `lead_ingested` CRM activity is appended for each

### AC3: Task failure retried with backoff
**Given** the Celery worker encounters a database connection error during ingestion
**When** the task fails
**Then** it is retried up to 3 times with delays of 60s, 120s, 240s; after the 3rd failure, a `system_error` CRM activity is appended

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: upload → task completes → leads in DB
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- Task uses `acks_late=True` and `reject_on_worker_lost=True` for at-least-once delivery
- File content passed to task as string (base64 or temp file path) — never pass `UploadFile` object directly
- `celery_app.conf.task_routes` must route `tasks.ingest_*` to `ingestion` queue
