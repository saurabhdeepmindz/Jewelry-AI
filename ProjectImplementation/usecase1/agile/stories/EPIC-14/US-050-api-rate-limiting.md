# US-050: API Rate Limiting per Role

**Epic:** EPIC-14
**Actor:** `system`
**Story Points:** 3
**Priority:** Medium
**Status:** Draft

## User Story

As the **system**,
I want API endpoints rate-limited per authenticated user by role,
so that no single user can overload the platform or external API integrations.

## Acceptance Criteria

### AC1: Rep rate limit enforced
**Given** a rep sends 101 requests within 60 seconds
**When** the 101st request arrives
**Then** 429 response: `{"detail": "Rate limit exceeded. Retry after 60 seconds."}`; `Retry-After: 60` header set

### AC2: Manager has higher rate limit
**Given** a manager sends 300 requests within 60 seconds
**When** the 300th request arrives
**Then** it is processed normally; the 301st request returns 429

### AC3: Rate limit resets after window
**Given** a rep has been rate-limited
**When** 61 seconds have elapsed
**Then** the rep can make requests again without error

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests: rep → 100 OK → 1 rejected; manager → 300 OK → 1 rejected
- [ ] Integration test: rate limit enforced with real Redis
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Rate limit values from `Settings` — not hardcoded
- [ ] PR squash-merged to master

## Notes

- Library: `slowapi` (FastAPI-compatible rate limiter backed by Redis)
- Rate limit key: `{user_id}:{endpoint_path}` — per-user, per-endpoint
- Health endpoints (`/health`, `/health/ready`) are exempt from rate limiting
- Rate limit values: `RATE_LIMIT_REP=100/minute`, `RATE_LIMIT_MANAGER=300/minute` in `Settings`
