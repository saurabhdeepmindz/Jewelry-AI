# US-052: Health Check and Readiness Probe Endpoints

**Epic:** EPIC-15
**Actor:** `system`
**Story Points:** 2
**Priority:** High
**Status:** Draft

## User Story

As the **system**,
I want liveness and readiness health endpoints exposed by the FastAPI application,
so that container orchestration and monitoring tools can automatically detect and recover from failures.

## Acceptance Criteria

### AC1: Liveness probe always returns 200
**Given** the FastAPI process is running (even if DB is down)
**When** `GET /health` is called
**Then** 200 response: `{"status": "ok", "service": "jewelry-ai", "version": "1.0.0"}` in < 5ms; no DB or Redis check performed

### AC2: Readiness probe returns 200 when dependencies are healthy
**Given** PostgreSQL and Redis are both reachable
**When** `GET /health/ready` is called
**Then** 200 response: `{"status": "ready", "db": "ok", "redis": "ok", "checks_ms": {"db": 12, "redis": 3}}`

### AC3: Readiness probe returns 503 when DB is down
**Given** PostgreSQL is unreachable (container stopped)
**When** `GET /health/ready` is called
**Then** 503 response: `{"status": "not_ready", "db": "error: connection refused", "redis": "ok"}`; FastAPI process continues running (does not crash)

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: DB stopped → /health/ready returns 503
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Health endpoints exempt from JWT auth and rate limiting
- [ ] PR squash-merged to master

## Notes

- `/health` must never fail — no external dependencies checked
- `/health/ready` uses `SELECT 1` for DB check; `PING` for Redis check
- `version` field from `Settings.APP_VERSION` or `importlib.metadata.version("jewelry-ai")`
- Docker Compose `healthcheck` uses `GET /health/ready`
