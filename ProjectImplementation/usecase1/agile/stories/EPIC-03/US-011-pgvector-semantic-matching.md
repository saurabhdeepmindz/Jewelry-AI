# US-011: Semantic Matching via pgvector Embeddings

**Epic:** EPIC-03
**Actor:** `system`
**Story Points:** 8
**Priority:** High
**Status:** Ready

## User Story

As the **system**,
I want to find inventory items semantically similar to a lead's buyer profile using vector embeddings,
so that matches are found even when the buyer's language doesn't exactly match the inventory field values.

## Acceptance Criteria

### AC1: Embedding generated for new lead
**Given** a new lead is ingested with `company_name` and available profile text
**When** the matching pipeline runs
**Then** an OpenAI `text-embedding-3-small` embedding (1536 dimensions) is generated for the lead's profile text and stored in `leads.embedding`

### AC2: Semantic similarity search returns top matches
**Given** a lead with an embedding stored
**When** the pgvector cosine similarity query runs
**Then** the top 10 inventory items by cosine similarity (lowest distance) are returned; cosine distance is stored as part of `match_score`

### AC3: Embedding not regenerated if already set
**Given** a lead already has `leads.embedding` set (non-null)
**When** the matching pipeline runs again for the same lead
**Then** no OpenAI API call is made; the existing embedding is reused

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: embedding stored → pgvector query returns results
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] OpenAI embedding tested end-to-end in staging (not just mocked)
- [ ] PR squash-merged to master

## Notes

- pgvector IVFFlat index: `WITH (lists = 100)` — set in migration 007
- Embedding text = concatenation of: `company_name`, `country`, `buyer_category` (if available)
- Cosine distance threshold: inventory items with distance > 0.5 are excluded from matches
- OpenAI API call uses `text-embedding-3-small` (1536 dims, cheapest option)
