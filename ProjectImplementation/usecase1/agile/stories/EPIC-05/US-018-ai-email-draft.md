# US-018: AI Email Draft Generation via LangChain

**Epic:** EPIC-05
**Actor:** `system`
**Story Points:** 8
**Priority:** Critical
**Status:** Ready

## User Story

As the **system**,
I want to generate a personalized outreach email for each enriched lead using an LLM,
so that every buyer receives a message that references their specific interests and Shivam Jewels' matching inventory.

## Acceptance Criteria

### AC1: Email draft created with personalization
**Given** a lead has an enriched contact and at least one matched inventory item
**When** the outreach generation agent runs
**Then** an `OutreachMessage` is created with `status=pending_review`, `channel=email`, `sequence_step=1`; the body mentions the buyer's first name, company, and at least one matched inventory SKU (stone type + carat weight)

### AC2: Output validated for minimum quality
**Given** the LLM returns a response shorter than 50 characters
**When** the chain's validation step runs
**Then** a `ValueError` is raised; the task retries with a clarifying note appended to the prompt

### AC3: Subject line generated
**Given** a successful generation
**When** the `OutreachMessage` is created
**Then** `subject` is set (not null) and is between 20 and 100 characters; it does not start with "Subject:"

## Definition of Done

- [ ] Implementation complete and reviewed
- [ ] Unit tests written first (RED → GREEN)
- [ ] Integration test: enriched lead → OutreachMessage in DB with non-empty body
- [ ] ruff: zero errors
- [ ] mypy: zero errors
- [ ] Coverage ≥ 80% for changed files
- [ ] OpenAI generation tested end-to-end in staging with 5 real lead samples
- [ ] PR squash-merged to master

## Notes

- LangChain LCEL chain: `RunnablePassthrough | ChatPromptTemplate | ChatOpenAI | StrOutputParser | validate_output`
- System prompt includes: company context (Shivam Jewels), tone (professional, concise), output format (subject + body)
- Model: `gpt-4o-mini` (settings: `OPENAI_MODEL`); temperature: 0.7
- Max tokens: 600 for initial email (avoids truncation)
