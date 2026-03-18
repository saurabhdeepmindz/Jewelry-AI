# US-016: Redis Enrichment Cache

**Epic:** EPIC-04
**Actor:** `system`
**Story Points:** 3
**Priority:** Critical
**Status:** Ready

## User Story

As the **system**,
I want enrichment results cached in Redis for 7 days,
so that the same domain is never enriched twice within the cache window, protecting our API credits.

## Acceptance Criteria

### AC1: Cache hit skips all external API calls
**Given** `enrichment:acme.com` exists in Redis with cached contact JSON
**When** `EnrichmentService.enrich_lead()` is called for `domain=acme.com`
**Then** no Apollo, Hunter, or Proxycurl API call is made; the cached result is returned immediately; a DEBUG log line `"Cache hit"` with `domain=acme.com` is emitted

### AC2: Cache miss triggers API call and stores result
**Given** `enrichment:acme.com` does NOT exist in Redis
**When** `EnrichmentService.enrich_lead()` is called and Apollo returns contacts
**Then** the result is stored in Redis with key `enrichment:acme.com` and TTL = 604800 seconds (7 days)

### AC3: Cache TTL confirmed
**Given** contacts were cached for a domain
**When** `TTL enrichment:{domain}` is called in Redis
**Then** the returned value is between 604700 and 604800 (within 100s of 7 days)

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: domain enriched → Redis key exists with correct TTL
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] No hardcoded secrets or magic values
- [ ] PR squash-merged to master

## Notes

- Cache key format: `enrichment:{domain}` — lowercase domain always
- Cache value: JSON-serialized `list[Contact.model_dump()]`
- `RedisCache` wrapper handles `json.dumps` / `json.loads` — raw bytes not exposed to callers
- Cache is invalidated manually by admin only (no auto-invalidation in Phase 1)
