# EPIC-04: Contact Enrichment Pipeline

**Status:** Ready
**Phase:** Phase 1
**Layer(s):** Layer 2 — Integration, Layer 3 — Business Services
**Priority:** Critical
**Estimated Size:** L

---

## Problem Statement

After a lead is marked eligible, the platform needs verified buyer contact information (name, email, phone, title) before outreach can begin. Currently, sales reps spend 15–30 minutes per lead manually searching LinkedIn and company websites. API credits from Apollo.io and Hunter.io are expensive — re-enriching the same company twice is money wasted.

## Goal

For every eligible lead, the platform automatically fetches buyer contacts using a cascading provider strategy (Apollo → Hunter → Proxycurl), caches results in Redis for 7 days to prevent re-enrichment, stores all contacts in the `contacts` table, and advances the lead to `status=enriched`.

## Scope (In)

- Strategy cascade: Apollo.io (primary) → Hunter.io (fallback) → Proxycurl (final fallback)
- Redis cache: 7-day TTL keyed by `enrichment:{domain}`; always check cache before API call
- Store results in `contacts` table: `full_name`, `email`, `phone`, `title`, `linkedin_url`, `enrichment_source`
- Set `leads.status = enriched`
- CRM activity: `lead_enriched` event appended
- `email_verified` flag set via Hunter.io email verification
- Graceful degradation: if all providers return empty, log warning; do not block pipeline
- Celery task on `enrichment` queue with exponential backoff (3 retries)

## Scope (Out)

- LinkedIn scraping (Proxycurl is the adapter; direct scraping is out of scope)
- Manual contact data entry (EPIC-09 UI feature)
- Re-enrichment triggered by user (7-day TTL covers this; manual override is Phase 3)
- WhatsApp contact lookup (EPIC-12)

---

## Acceptance Criteria

- [ ] AC1: Apollo.io returns contacts → `Contact` records created with `enrichment_source=apollo`; lead advances to `status=enriched`
- [ ] AC2: Apollo.io fails (non-2xx) → Hunter.io is called automatically; contacts created with `enrichment_source=hunter`
- [ ] AC3: All providers fail → lead remains `status=enriched` with zero contacts; `lead_enriched` CRM event still appended; no exception raised to caller
- [ ] AC4: Domain already cached in Redis → no external API call made; cached contacts returned immediately; cache hit logged at DEBUG level
- [ ] AC5: A contact with a duplicate `(lead_id, email)` → upsert (not duplicate insert); `idx_contacts_lead_email` unique index respected
- [ ] AC6: Celery task failure → retried up to 3 times with exponential backoff (60s, 120s, 240s); `system_error` CRM event appended after final failure

---

## User Stories

- US-014: Apollo.io contact enrichment — `agile/stories/EPIC-04/US-014-apollo-enrichment.md`
- US-015: Hunter.io fallback enrichment — `agile/stories/EPIC-04/US-015-hunter-fallback.md`
- US-016: Redis enrichment cache — `agile/stories/EPIC-04/US-016-redis-enrichment-cache.md`
- US-017: Enriched contact storage and lead status update — `agile/stories/EPIC-04/US-017-contact-storage.md`

---

## External API Dependencies

| API | Purpose | Credential Required |
|-----|---------|-------------------|
| Apollo.io People Search API | Primary contact fetch | `APOLLO_KEY_ENCRYPTED` |
| Hunter.io Email Finder API | Email verification + fallback | `HUNTER_KEY_ENCRYPTED` |
| Proxycurl LinkedIn API | LinkedIn profile enrichment (final fallback) | `PROXYCURL_KEY_ENCRYPTED` |

---

## Definition of Done

- [ ] All user stories marked Done
- [ ] ruff: zero linting errors
- [ ] mypy: zero type errors
- [ ] pytest: all tests pass, coverage ≥ 80%
- [ ] Apollo.io and Hunter.io tested end-to-end in staging (not just mocked)
- [ ] Redis cache TTL verified with `TTL enrichment:{domain}` command
- [ ] No hardcoded secrets
- [ ] PR reviewed and merged to master
