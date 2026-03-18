# US-001: Dev Environment and Docker Compose Setup

**Epic:** EPIC-01
**Actor:** `admin`
**Story Points:** 5
**Priority:** Critical
**Status:** Ready

## User Story

As an **admin**,
I want to start the full platform locally with a single `make up` command,
so that every developer has an identical, reproducible environment from day one.

## Acceptance Criteria

### AC1: All services start successfully
**Given** a developer has Docker Desktop running and has copied `.env.example` to `.env`
**When** they run `make up` (or `docker compose up --build -d`)
**Then** all five containers start without errors: `fastapi`, `postgres`, `redis`, `celery_worker`, `n8n`; and `docker compose ps` shows all as `Up`

### AC2: FastAPI health endpoint responds
**Given** all containers are running
**When** the developer calls `GET http://localhost:8000/health`
**Then** the response is `200 OK` with body `{"status": "ok"}`

### AC3: PostgreSQL and Redis are reachable from FastAPI container
**Given** all containers are running
**When** `docker compose exec fastapi python -c "from src.db.session import _engine; print('ok')"`
**Then** the command prints `ok` with no connection error

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: health endpoint returns 200
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- `.env.example` must document every variable with a comment explaining its purpose
- `docker-compose.yml` must use named volumes for Postgres data persistence across restarts
- Line endings enforced by `.gitattributes`: `* text=auto eol=lf` — required for Windows/Linux parity
