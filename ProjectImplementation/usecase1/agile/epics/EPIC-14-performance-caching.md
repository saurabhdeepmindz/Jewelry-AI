# EPIC-14: Performance, Caching & Scale

**Status:** Draft
**Phase:** Phase 4
**Layer(s):** All layers
**Priority:** Medium
**Estimated Size:** L

---

## Problem Statement

As the lead database grows to tens of thousands of records and the team runs more concurrent enrichment and scoring tasks, performance bottlenecks will emerge: slow lead list queries, repeated expensive DB lookups, unthrottled external API calls triggering rate limit errors.

## Goal

Key read paths are cached in Redis. N+1 query patterns are eliminated with `selectinload` or batch queries. API endpoints are rate-limited per user/role to prevent abuse. The platform handles 1,000 concurrent leads in the pipeline without degradation.

## Scope (In)

- Redis caching: `GET /api/v1/leads` list results (TTL 60s), analytics funnel counts (TTL 300s)
- Cache invalidation: on lead status change, flush affected cache keys
- N+1 elimination: `LeadRepository.list_*` methods use `selectinload` for `contacts` and `outreach_messages`
- `EXPLAIN ANALYZE` review for all queries touching > 1,000 rows
- Rate limiting: `slowapi` middleware — 100 req/min per `ROLE_REP`, 300 req/min per `ROLE_MANAGER/ADMIN`
- DB connection pool tuning: `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` exposed in settings
- Celery concurrency tuning: queue-specific worker concurrency settings
- `GET /api/v1/health/db` — connection pool status endpoint

## Scope (Out)

- Horizontal scaling / Kubernetes (infrastructure concern, not in this epic)
- CDN for static assets (Streamlit handles this)
- Database read replicas

---

## Acceptance Criteria

- [ ] AC1: `GET /api/v1/leads` with 10,000 lead records responds in < 200ms (cache hit) and < 800ms (cache miss)
- [ ] AC2: Lead list endpoint has no N+1 queries — confirmed via `EXPLAIN ANALYZE` showing no per-row subqueries
- [ ] AC3: A `ROLE_REP` sending > 100 requests/minute receives 429 responses on excess requests
- [ ] AC4: Cache invalidation: updating a lead's status purges the corresponding list cache key
- [ ] AC5: `GET /api/v1/health/db` returns pool utilization metrics: `{pool_size, checked_out, overflow, invalid}`
- [ ] AC6: Celery `ml` queue worker runs with `concurrency=2` (CPU-bound); `enrichment` queue runs with `concurrency=8` (I/O-bound) — configurable via environment

---

## User Stories

- US-048: Redis query result caching — `agile/stories/EPIC-14/US-048-redis-query-cache.md`
- US-049: N+1 query elimination — `agile/stories/EPIC-14/US-049-n-plus-one-elimination.md`
- US-050: API rate limiting per role — `agile/stories/EPIC-14/US-050-api-rate-limiting.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| Redis (internal) | Cache layer | `REDIS_URL` in settings |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] Load test: 1,000 concurrent lead list requests with < 800ms p99 latency
- [ ] `EXPLAIN ANALYZE` output reviewed and documented for all hot queries
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
