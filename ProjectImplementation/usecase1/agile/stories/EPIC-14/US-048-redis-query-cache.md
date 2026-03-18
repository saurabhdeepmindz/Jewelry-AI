# US-048: Redis Query Result Caching

**Epic:** EPIC-14
**Actor:** `system`
**Story Points:** 5
**Priority:** Medium
**Status:** Draft

## User Story

As the **system**,
I want hot API query results cached in Redis,
so that repeated lead list and analytics requests are served in milliseconds without hitting the database.

## Acceptance Criteria

### AC1: Lead list cache hit avoids DB query
**Given** `GET /api/v1/leads?status=enriched&page=1` was called once and cached
**When** the same request is made within 60 seconds
**Then** the response is served from Redis; no SQL query is executed (confirmed via `DB_ECHO=true` logs showing no SELECT)

### AC2: Cache invalidated on lead status change
**Given** a lead's status changes from `enriched` to `scored`
**When** `LeadRepository.update_status()` commits the change
**Then** all Redis keys matching `leads:*` are deleted; the next `GET /api/v1/leads` call hits the DB and repopulates the cache

### AC3: Analytics funnel cached for 5 minutes
**Given** `GET /api/v1/analytics/funnel` was called
**When** the same endpoint is called within 5 minutes
**Then** the cached count values are returned; `Cache-Control: max-age=300` header is set in the response

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests: cache hit → no DB call; cache miss → DB call + cache set
- [ ] Integration test: update lead → cache invalidated → fresh data returned
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Cache TTLs from `Settings` — not hardcoded
- [ ] PR squash-merged to master

## Notes

- Cache key format: `leads:{status}:{score_tier}:{page}:{limit}:{user_id}` — must include user_id for rep isolation
- Cache invalidation pattern: `SCAN 0 MATCH leads:* COUNT 100` then `DEL` matching keys
- Do NOT cache endpoints that return user-specific data with a shared key
