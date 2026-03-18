# US-014: Apollo.io Contact Enrichment

**Epic:** EPIC-04
**Actor:** `system`
**Story Points:** 5
**Priority:** Critical
**Status:** Ready

## User Story

As the **system**,
I want to fetch buyer contacts for eligible leads from Apollo.io,
so that reps have verified names, emails, and titles without any manual research.

## Acceptance Criteria

### AC1: Apollo returns contacts → stored in DB
**Given** an eligible lead with `domain=acme.com`
**When** the enrichment task calls Apollo.io People Search API for that domain
**Then** `Contact` records are created with `full_name`, `email`, `title`, `phone` (where available), `enrichment_source=apollo`, and `enriched_at` timestamp set

### AC2: Apollo HTTP error → IntegrationError raised
**Given** Apollo.io returns HTTP 429 (rate limit)
**When** the enrichment strategy processes the response
**Then** an `ApolloError` (subclass of `IntegrationError`) is raised; the calling strategy cascade catches it and tries the next provider

### AC3: Apollo returns empty result → cascade continues
**Given** Apollo.io returns HTTP 200 with `{"people": []}`
**When** the enrichment strategy processes the response
**Then** an empty list is returned (no exception); the EnrichmentService tries Hunter.io next

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test with mocked httpx: Apollo → contacts created
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Apollo.io tested end-to-end against real API in staging
- [ ] PR squash-merged to master

## Notes

- `ApolloClient` uses `httpx.AsyncClient` — never `requests`
- Titles to search: `["buyer", "purchasing manager", "procurement", "diamond buyer", "jewelry buyer"]`
- Max contacts per domain: 10 (Apollo API `per_page=10`)
- API key decrypted at factory time via `decrypt_fernet()` — never stored in plain text
