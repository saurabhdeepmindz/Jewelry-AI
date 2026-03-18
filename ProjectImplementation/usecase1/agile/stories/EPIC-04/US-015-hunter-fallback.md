# US-015: Hunter.io Fallback Enrichment

**Epic:** EPIC-04
**Actor:** `system`
**Story Points:** 3
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want to fall back to Hunter.io when Apollo.io returns no contacts,
so that enrichment succeeds even for companies not in Apollo's database.

## Acceptance Criteria

### AC1: Hunter called only when Apollo returns empty
**Given** Apollo.io returned an empty people list for `domain=acme.com`
**When** the EnrichmentService cascade runs
**Then** Hunter.io Domain Search API is called for the same domain; Apollo is not re-called

### AC2: Hunter contacts stored with correct source
**Given** Hunter.io returns 3 email addresses for a domain
**When** contacts are persisted
**Then** `Contact` records are created with `enrichment_source=hunter`; `email_verified` is set based on Hunter's `smtp_server_status`

### AC3: Hunter also empty → Proxycurl attempted
**Given** both Apollo and Hunter return no contacts
**When** the cascade continues
**Then** Proxycurl LinkedIn API is called as the final fallback; `enrichment_source=proxycurl` if contacts found

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: Apollo empty → Hunter called → contacts stored
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] Hunter.io tested end-to-end in staging
- [ ] PR squash-merged to master

## Notes

- Hunter.io endpoint: `GET /v2/domain-search?domain={domain}&limit=10`
- `email_verified = True` when Hunter `smtp_server_status = "valid"`
- Strategy order enforced in DI: `[ApolloStrategy, HunterStrategy, ProxycurlStrategy]`
