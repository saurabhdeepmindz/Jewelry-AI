# SKILLS-sj.md — Shivam Jewels AI Workflow Skills

> **Purpose:** Jewelry AI project-specific workflow playbooks. Extends generic and Python skills.
> **Extends:** `SKILLS-generic.md` (base) → `SKILLS-python.md` (Python stack) → this file (SJ overrides)
> **Read order:** Always read the parent skill first, then apply SJ-specific steps.
> **Naming:** Each skill is identified by `SKILL-SJ-NNN` for traceability.

---

## SKILL-SJ-001 — Run a Jewelry AI Increment

**Extends:** SKILL-G-001 (Run an Increment) + SKILL-P-002 (FastAPI Scaffold)
**When to use:** Starting any increment in the Jewelry AI platform.

**SJ-specific layer build order:**
```
1. Alembic migration (if schema changes)       SKILL-P-001
2. SQLAlchemy model                            src/db/models/
3. Pydantic schemas                            src/schemas/
4. Repository                                  src/repositories/
5. Service                                     src/services/
6. Celery task (if async)                      src/tasks/          SKILL-P-003
7. FastAPI router                              src/api/routers/
8. Integration client (if external API)        src/integrations/
9. Unit tests                                  tests/unit/         SKILL-P-004 + SKILL-P-005
10. Integration tests                          tests/integration/
11. Streamlit UI screen (if applicable)        SKILL-SJ-004
12. Quality gate                               SKILL-P-006
```

**Before starting:**
- Confirm increment is in `Plan-sj.md` and linked to a User Story
- Read `GUIDELINES_COMPLIANCE-sj.md` — verify relevant rules are ✅ for this increment
- Update compliance checklist Increment Coverage Tracker when done

---

## SKILL-SJ-002 — Lead Ingestion Workflow

**Covers:** CSV upload → deduplication → async Celery task → job polling
**References:** EPIC-02, WF-007, `testing-rules-sj.md`

**Steps:**
1. Validate CSV at boundary: required columns, encoding, row limit
2. Deduplicate against existing leads: match on `company_name` + `country` (case-insensitive)
3. Create ingestion job in Redis via `JobStore` — return `job_id` immediately (202 Accepted)
4. Dispatch Celery task to `ingestion` queue: `tasks.ingestion.process_csv`
5. Task writes progress to Redis: `{"status": "processing", "processed": N, "total": M}`
6. On completion: update Redis to `{"status": "complete", "imported": N, "duplicates": D}`
7. Client polls `GET /api/v1/jobs/{job_id}` until status is `complete` or `failed`

**Test requirements:**
- Unit: mock `LeadRepository`, assert deduplication logic
- Unit: mock Redis `JobStore`, assert status transitions
- Integration: use `LeadFactory`, real DB, `task.apply()` sync
- HTTP: use `respx` to mock any external calls

---

## SKILL-SJ-003 — Contact Enrichment Workflow

**Covers:** Apollo lookup → Hunter verification → cache check → Celery task
**References:** EPIC-03, `ai-ml-rules-sj.md`, `testing-rules-sj.md`

**Steps:**
1. Check enrichment cache: if `contact.enriched_at` is set → skip (never re-enrich)
2. Dispatch Celery task to `enrichment` queue: `tasks.enrichment.enrich_contact`
3. Task calls `ApolloClient.find_person()` — handle 404 gracefully (not all leads have Apollo data)
4. If Apollo returns email → call `HunterClient.verify_email()` — only store if deliverability ≥ 0.7
5. Store result in `contacts` table — update `enriched_at` timestamp
6. Write Celery task status to Redis throughout
7. On failure: retry up to 3 times with 60s backoff — log each attempt with structured context

**Cache rule (critical):** Enrichment API credits are finite.
- NEVER call Apollo or Hunter if `contact.enriched_at IS NOT NULL`
- Cache TTL is indefinite — enriched data does not expire automatically

**Test requirements:**
- Unit: mock `ApolloClient` and `HunterClient` with `respx`
- Unit: assert cache-hit path skips all API calls
- Integration: `ContactFactory` + real DB + `task.apply()`

---

## SKILL-SJ-004 — Streamlit Screen Scaffold

**Covers:** HTML wireframe → APIClient calls → Streamlit page file
**References:** WF-NNN wireframe, `frontend-streamlit-generic.md`, `ui-wireframe-rules-sj.md`

**Steps:**
1. Read the relevant wireframe: `docs/wireframes/WF-NNN-{screen}.html`
2. Identify all API calls annotated in the wireframe
3. Add any missing API methods to `src/ui/api_client.py` (thin — HTTP only, no logic)
4. Create page file: `src/ui/pages/{screen}.py`
5. Implement 5-state machine: `idle → loading → success → error → empty`
6. Use `st.session_state` for navigation state — never global variables
7. Use `@st.cache_data(ttl=30)` for read-only data, never for write operations
8. Use `error_banner` component for all error states — never raw `st.error()`
9. Register page in `src/ui/app.py` navigation
10. Manual smoke test: idle → trigger → loading → success → error paths

**SJ screen catalog:**
| WF | Screen | Page file |
|---|---|---|
| WF-000 | Screen index | — |
| WF-001 | Login | `pages/login.py` |
| WF-002 | Lead pipeline dashboard | `pages/dashboard.py` |
| WF-003 | Lead detail view | `pages/lead_detail.py` ✅ |
| WF-004 | Outreach review queue | `pages/outreach_review.py` |
| WF-005 | Analytics funnel | `pages/analytics.py` |
| WF-006 | Admin users | `pages/admin_users.py` |
| WF-007 | CSV upload | `pages/upload.py` ✅ |

---

## SKILL-SJ-005 — LangGraph Agent Workflow

**Covers:** Defining a new LangGraph state machine node
**References:** `ai-ml-rules-sj.md`, `workflow-rules-sj.md`

**Steps:**
1. Define the state schema as a `TypedDict` in `src/agents/state.py`
2. Create node functions in `src/agents/{domain}_agent.py` — each node is a pure function: `(state) → state`
3. Define the graph in `src/agents/{domain}_graph.py`:
   - `add_node` for each processing step
   - `add_edge` / `add_conditional_edges` for transitions
   - `set_entry_point` and `set_finish_point`
4. Never call LLM APIs directly in service methods — only inside agent nodes
5. Wrap LLM calls with cost logging: model name, input tokens, output tokens, latency
6. Add MLflow tracking for each agent run: log parameters and metrics
7. Unit test each node function independently — nodes are pure functions, easy to test
8. Integration test the full graph with a real LangChain client (use a low-cost model in tests)

---

## SKILL-SJ-006 — Outreach Message Generation

**Covers:** Lead match → personalisation context → LLM call → human review queue
**References:** EPIC-07, `ai-ml-rules-sj.md`

**Steps:**
1. Confirm lead has at least one `lead_inventory_match` — no match = no outreach (business rule)
2. Build personalisation context: lead company, contact name/title, matched inventory items (carat, cut, price)
3. Call outreach LangGraph agent: `src/agents/outreach_graph.py`
4. Agent generates email + WhatsApp variants using GPT-4o (primary) or Claude (fallback)
5. Store draft in `outreach_messages` table with `status = DRAFT`
6. If `HUMAN_REVIEW_REQUIRED = true` → add to review queue (WF-004), do not send
7. If auto-approved → dispatch to `outreach` Celery queue for sending via SendGrid/Twilio
8. Log `CRMActivity` row as append-only audit entry — never update existing rows

---

## SKILL-SJ-007 — Adding a New Inventory Match Rule

**Covers:** Extending the matching criteria between leads and inventory
**References:** `LLD-sj.md`, `data-rules-python.md`

**Steps:**
1. Read `LLD-sj.md` matching section — understand existing scoring weights
2. Add new criterion to `src/services/matching_service.py` using Strategy pattern
3. Add migration if new column is needed on `lead_inventory_matches`
4. Update scoring formula — document weights in a comment block
5. Add unit tests for the new criterion in isolation
6. Run regression: existing match results must not change score by more than ±5%
7. Update `LLD-sj.md` matching section with new criterion and weight

---

## Skills Inheritance Summary

```
SKILLS-generic.md          (G-001 to G-009)
  └── SKILLS-python.md     (P-001 to P-007) — extends generic
        └── SKILLS-sj.md   (SJ-001 to SJ-007) — extends Python + SJ overrides
```

| Generic Skill | Python Extension | SJ Override |
|---|---|---|
| G-001 Run Increment | P-002 FastAPI Scaffold | SJ-001 SJ Layer Order |
| G-002 TDD Cycle | P-004 factory_boy + P-005 respx | SJ-002/003 domain test patterns |
| G-005 DB Migration | P-001 Alembic Workflow | — |
| G-006 Code Review | P-006 mypy + ruff gate | — |
| — | P-003 Celery Task | SJ-002/003 queue assignments |
| — | — | SJ-004 Streamlit Screen |
| — | — | SJ-005 LangGraph Agent |
| — | — | SJ-006 Outreach Generation |
| — | — | SJ-007 Inventory Match Rule |

---

*Last updated: 2026-03-20*
*Add new skills here when a repeatable workflow is identified during an increment.*
