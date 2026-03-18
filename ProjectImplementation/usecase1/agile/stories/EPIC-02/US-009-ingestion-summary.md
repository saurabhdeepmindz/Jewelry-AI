# US-009: Ingestion Summary Response

**Epic:** EPIC-02
**Actor:** `rep`
**Story Points:** 2
**Priority:** Medium
**Status:** Ready

## User Story

As a **rep**,
I want to see a clear summary after uploading a CSV,
so that I know exactly how many leads were created, how many were skipped, and why.

## Acceptance Criteria

### AC1: Summary contains all counts
**Given** a CSV with 100 rows: 80 new, 15 duplicate domains, 5 missing company_name
**When** the ingestion task completes and the rep polls `GET /api/v1/leads/jobs/{job_id}`
**Then** the response contains: `{"created": 80, "skipped_duplicates": 15, "skipped_invalid": 5, "errors": 0, "status": "completed"}`

### AC2: In-progress status returned during processing
**Given** the Celery task is still running
**When** the rep polls `GET /api/v1/leads/jobs/{job_id}`
**Then** the response contains `{"status": "processing", "created": 0, ...}` — not a 404

### AC3: Failed job status returned on task error
**Given** the Celery task exhausted all retries
**When** the rep polls `GET /api/v1/leads/jobs/{job_id}`
**Then** the response contains `{"status": "failed", "error": "Database connection failed after 3 retries"}`

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test for the job polling endpoint
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- Job status stored in Redis with TTL 24h: key `job:{job_id}` → JSON status blob
- `GET /api/v1/leads/jobs/{job_id}` returns 404 if `job_id` not found (expired or invalid)
- Polling interval recommendation: 2s; max wait: 5 minutes (documented in API spec)
