# US-006: CSV File Upload and Parsing

**Epic:** EPIC-02
**Actor:** `rep`
**Story Points:** 3
**Priority:** Critical
**Status:** Ready

## User Story

As a **rep**,
I want to upload a CSV file of raw buyer company data via the API,
so that trade directory leads are loaded into the platform without manual data entry.

## Acceptance Criteria

### AC1: Valid CSV parsed and rows returned to caller
**Given** a rep uploads a CSV with columns: `company_name`, `domain`, `country`, `source`
**When** `POST /api/v1/leads/upload` is called with the file as `multipart/form-data`
**Then** all rows are parsed; a 202 response is returned with a `job_id` for async tracking

### AC2: Missing required column rejected
**Given** the uploaded CSV is missing the `company_name` column
**When** the file is submitted
**Then** a 422 response is returned with message: `"Missing required column: company_name"`; no records are created

### AC3: Batch size limit enforced
**Given** the uploaded CSV contains 501 rows (exceeds limit of 500)
**When** the file is submitted
**Then** a 422 response is returned with message: `"Batch size 501 exceeds maximum 500"`; nothing is persisted

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test for the API endpoint
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- Use `python-multipart` for file upload; `csv.DictReader` for parsing (no pandas dependency needed)
- File is not stored to disk — parse in-memory from `SpooledTemporaryFile`
- `source` must be one of: `gmt | trade_book | rapid_list | manual | api`; invalid source → row skipped, counted as `skipped_invalid`
