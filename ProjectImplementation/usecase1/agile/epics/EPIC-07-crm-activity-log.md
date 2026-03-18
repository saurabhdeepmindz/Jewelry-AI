# EPIC-07: CRM Activity & Audit Log

**Status:** Ready
**Phase:** Phase 2
**Layer(s):** Layer 1 — Core Data, Layer 6 — Reporting
**Priority:** High
**Estimated Size:** S

---

## Problem Statement

Sales managers and admins need a complete, trustworthy audit trail of everything that has happened to a lead — from first ingestion through every enrichment attempt, outreach draft, approval decision, email event, and system error. Without this, debugging pipeline issues is impossible and compliance is at risk.

## Goal

Every significant lead lifecycle event is appended to `crm_activity` as an immutable record. The activity log is accessible via API for any lead, enabling timeline views in the dashboard and supporting audit queries.

## Scope (In)

- `CRMRepository.append()` — only method permitted on `crm_activity` (no update, no delete)
- All 18 activity event types from `ActivityType` enum logged at the correct pipeline stage
- `GET /api/v1/crm/{lead_id}/activity` — paginated timeline for a lead
- `actor` field set correctly: `system` for automated events, `user:{user_id}` for manual actions
- `trace_id` propagated from originating HTTP request through all activity events
- `event_payload` JSONB stores relevant context per event type
- System error events: `system_error` with `event_payload.error` and `event_payload.step`

## Scope (Out)

- CRM activity export to CSV (future reporting feature)
- Cross-lead activity feed (global activity stream — out of scope)
- Activity deletion or correction (append-only; immutable by design)

---

## Acceptance Criteria

- [ ] AC1: Every pipeline stage (ingest → match → enrich → score → outreach) appends the correct `event_type` to `crm_activity` with a non-null `trace_id`
- [ ] AC2: `GET /api/v1/crm/{lead_id}/activity` returns events in descending `created_at` order, paginated (default limit=20)
- [ ] AC3: Attempting an `UPDATE` or `DELETE` on `crm_activity` raises an application-level exception (`CRMImmutableError`) — enforced at repository layer
- [ ] AC4: A `system_error` event is appended whenever a Celery task exhausts all retries
- [ ] AC5: `actor` field is `system` for all Celery/LangGraph events and `user:{user_id}` for all API-triggered events
- [ ] AC6: `event_payload` is valid JSONB with at least one key per event type (no empty `{}` payloads for known event types)

---

## User Stories

- US-025: Append-only CRM activity logging — `agile/stories/EPIC-07/US-025-crm-append-logging.md`
- US-026: Lead activity timeline API endpoint — `agile/stories/EPIC-07/US-026-activity-timeline-api.md`
- US-027: System error event logging — `agile/stories/EPIC-07/US-027-system-error-events.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| None | CRM activity is internal only | — |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] Alembic migration for `crm_activity` confirmed applied cleanly
- [ ] Immutability enforced — integration test confirms no UPDATE path exists
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
