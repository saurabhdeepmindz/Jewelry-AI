# EPIC-02: Lead Ingestion & Deduplication

**Status:** Ready
**Phase:** Phase 1
**Layer(s):** Layer 3 — Business Services
**Priority:** Critical
**Estimated Size:** M

---

## Problem Statement

Sales reps currently copy buyer company data from trade directories (GMTs, Hill Lists, Rapid Lists) by hand into spreadsheets. There is no systematic way to load raw lead data into the platform, deduplicate it against existing records, or trigger the downstream pipeline automatically.

## Goal

A sales rep uploads a CSV of raw buyer companies via the API, and the platform automatically ingests valid records, deduplicates by email domain, creates `Lead` rows with `status=ingested`, and enqueues each new lead for inventory matching — all within a single API call.

## Scope (In)

- `POST /api/v1/leads/upload` — CSV file upload endpoint
- CSV parsing with `pandas` or `csv.DictReader`; required columns: `company_name`, `source`
- Lead record creation in `leads` table
- Domain-based deduplication: skip rows whose domain already exists in DB
- Async pipeline trigger via Celery `ingestion` queue on successful create
- Ingestion summary response: `{created, skipped_duplicates, skipped_invalid, errors}`
- CRM activity append: `lead_ingested` event per created lead
- Max batch size: 500 rows per upload

## Scope (Out)

- Real-time scraping from GMT / Trade Book APIs (EPIC-02 covers file upload only)
- Scheduled scraping (EPIC-10)
- Contact enrichment (EPIC-04)
- Inventory matching logic (EPIC-03)

---

## Acceptance Criteria

- [ ] AC1: A rep uploads a valid CSV → all new rows become `Lead` records with `status=ingested`; response includes accurate `created` count
- [ ] AC2: A domain already in the DB → row is skipped; `skipped_duplicates` count incremented; no duplicate row created
- [ ] AC3: A row missing `company_name` → row is skipped; `skipped_invalid` count incremented; valid rows in the same file still succeed
- [ ] AC4: Batch exceeding 500 rows → 422 response returned; nothing is persisted
- [ ] AC5: Each created lead has a `lead_ingested` event appended to `crm_activity`
- [ ] AC6: Each created lead triggers `process_lead` Celery task on the `ingestion` queue

---

## User Stories

- US-006: CSV file upload and parsing — `agile/stories/EPIC-02/US-006-csv-upload-parsing.md`
- US-007: Lead record creation and deduplication — `agile/stories/EPIC-02/US-007-lead-deduplication.md`
- US-008: Async ingestion via Celery — `agile/stories/EPIC-02/US-008-async-ingestion-task.md`
- US-009: Ingestion summary response — `agile/stories/EPIC-02/US-009-ingestion-summary.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| None | Ingestion is from uploaded files only in this epic | — |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] Alembic migrations applied cleanly
- [ ] `POST /api/v1/leads/upload` documented in OpenAPI with example request/response
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
