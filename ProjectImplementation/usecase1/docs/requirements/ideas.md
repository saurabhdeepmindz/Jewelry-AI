# Ideas & Approach — Jewelry AI Lead Automation Platform

**Version:** 1.0
**Status:** Approved
**Stage:** 2.1 — Requirements
**Created:** 2026-03-18
**Input:** Requirements.txt, FUNCTIONAL_LANDSCAPE.md, ACTORS.md

---

## 1. Problem Statement

Shivam Jewels sources diamond buyers from trade directories (GMTs, Jewelry Book of Trade, Hill Lists, Rapid Lists). Today, every step of the lead lifecycle is manual:

| Step | Manual Effort | Pain |
|---|---|---|
| Lead collection | Download/import trade lists | Time-consuming, inconsistent format |
| Inventory match | Human checks against stock manually | Error-prone, delayed |
| Contact research | LinkedIn + Google search per lead | 30–60 min per lead |
| Email outreach | Individually drafted emails | Inconsistent quality, slow |
| CRM logging | Manual entry after every action | Often skipped, always delayed |
| Follow-up | Calendar reminders, manual follow-up | Leads fall through the cracks |

**Result:** A rep can process only a small number of leads per day. Response time is slow. Outreach quality is inconsistent. CRM data is incomplete.

---

## 2. Proposed Solution

Build an AI-powered lead automation platform that executes the full lifecycle automatically — from raw trade list to personalised outreach — with humans involved only at the approval gate.

### Core Automation Loop

```
Trade Directory Data
        │
        ▼
[1] Lead Ingestion          ← CSV upload or scheduled scraping
        │
        ▼
[2] Inventory Match         ← Rule-based + pgvector semantic match
        │ ELIGIBLE only
        ▼
[3] Contact Enrichment      ← Apollo.io → Hunter.io → Proxycurl (cascade)
        │
        ▼
[4] Lead Scoring            ← XGBoost ML model (0–100 conversion score)
        │
        ▼
[5] AI Outreach Generation  ← LangChain + GPT-4o → personalised email draft
        │
        ▼
[6] Human Review Gate       ← Manager approves / rejects (configurable)
        │ APPROVED
        ▼
[7] Email Send + Track      ← SendGrid → open/click/reply webhooks
        │
        ▼
[8] CRM Auto-Log            ← Every event appended automatically
        │
        ▼
[9] Follow-Up Sequence      ← n8n: Day 4 + Day 7 automated follow-ups
```

**After automation:** 1 lead processed in minutes. Standardised enriched data. Outreach within hours. CRM always current.

---

## 3. Technology Stack Rationale

| Technology | Role | Why Chosen |
|---|---|---|
| **FastAPI** | REST API backend | Async-native Python, automatic OpenAPI docs, high performance |
| **LangChain** | LLM orchestration | Composable chains, tool-use patterns, provider-agnostic |
| **LangGraph** | Stateful workflow automation | State machine with branching, resumable, auditable |
| **PostgreSQL + pgvector** | Primary database + semantic search | Single store for structured data and embeddings; avoids managing a separate vector DB |
| **Redis** | Task queue broker + cache | Celery broker; enrichment API response cache to protect finite credits |
| **Celery** | Async background tasks | Battle-tested Python task queue; retry/backoff built-in |
| **n8n** | Multi-step outreach sequences | Visual workflow automation; Day 1/4/7 email cadence without code |
| **Streamlit** | Frontend UI | Fast to build; no frontend engineer needed; ideal for data-heavy ops dashboards |
| **XGBoost** | Lead scoring ML model | Interpretable, fast inference, good performance on tabular data |
| **MLflow** | ML experiment tracking | Open-source; tracks training runs, models, and evaluation metrics |
| **SendGrid** | Email delivery | Reliable transactional email; webhook events for open/click/bounce tracking |
| **Apollo.io** | Primary contact enrichment | Best-in-class B2B contact database |
| **Hunter.io** | Email verification | Fast email deliverability check; fallback enrichment |
| **Proxycurl** | LinkedIn enrichment | LinkedIn profile data without scraping risk |
| **Twilio** | WhatsApp outreach (Phase 2) | Industry standard for programmatic messaging |

---

## 4. Key Design Decisions

### Decision 1: pgvector over a dedicated vector database
**Choice:** Use `pgvector` extension on the existing PostgreSQL instance.
**Rationale:** Eliminates operational overhead of a separate Qdrant/Pinecone/Weaviate cluster. For the lead volumes expected (10k–100k), pgvector performance is more than adequate. All data stays in one ACID-compliant store.

### Decision 2: LangGraph for the pipeline, not a simple Celery chain
**Choice:** LangGraph state machine for the lead pipeline.
**Rationale:** The pipeline has conditional branching (eligible / not eligible), error recovery nodes, and the need for state introspection. LangGraph makes branches explicit and auditable. A plain Celery chain would make branching messy.

### Decision 3: Human review gate is configurable, not hardcoded
**Choice:** `HUMAN_REVIEW_REQUIRED` feature flag in config.
**Rationale:** For POC and trusted high-volume scenarios, the gate can be disabled. For production with a new lead source, it should be on. Operators should control this without code changes.

### Decision 4: Enrichment cascade with cache
**Choice:** Apollo → Hunter → Proxycurl waterfall; cache all results in Redis for 7 days.
**Rationale:** API credits (especially Proxycurl) are expensive and finite. Caching prevents redundant calls. The cascade ensures highest-quality data without calling all providers every time.

### Decision 5: Streamlit UI over React/Next.js
**Choice:** Streamlit for the frontend.
**Rationale:** The platform is an internal ops tool, not a consumer product. Streamlit delivers a functional dashboard quickly without a dedicated frontend engineer. Can be replaced with a richer frontend in Phase 5+.

---

## 5. POC Scope (Phase 0 — Proof of Concept)

The POC demonstrates the core value proposition end-to-end using synthetic data:

| POC Step | Functionality | Success Criteria |
|---|---|---|
| Upload 20 synthetic leads | CSV upload → Lead Ingestion Service | Leads appear in Streamlit with `status=ingested` |
| Inventory match | Match against 10 synthetic inventory items | At least 8 leads flagged `ELIGIBLE` |
| Mock enrichment | Stubbed Apollo/Hunter responses | Contacts created with name, email, title |
| AI outreach draft | OpenAI call with matched inventory context | Draft email created, referencing actual SKUs |
| Manager review | Approve button in Streamlit | Message status changes to `approved` |
| Send simulation | SendGrid sandbox mode | Email logged as `sent` in CRM activity |
| Dashboard | Lead list with status, score, enrichment state | All data visible in Streamlit |

**POC is demo-ready when:** Full flow runs end-to-end in under 5 minutes on a local laptop with `docker compose up`.

---

## 6. Full Product Scope (Phase 0 → Phase 4)

| Phase | Deliverable | Key Milestone |
|---|---|---|
| **Phase 0** | Project skeleton, config, Docker, CI | `GET /health` returns ok; all services start |
| **Phase 1** | Lead ingestion, inventory matching, enrichment, AI outreach drafts | CSV → eligible → enriched → AI draft |
| **Phase 2** | Email send + tracking, CRM log, lead scoring, Streamlit dashboard, Auth/RBAC, n8n automation | Full automated pipeline, manager review, outreach sent |
| **Phase 3** | WhatsApp channel, MLflow experiment tracking | Multi-channel outreach, ML model versioned |
| **Phase 4** | Performance hardening, observability, production deployment | Production-ready platform |

---

## 7. Key Assumptions

1. Trade directory data is available as downloadable CSV/Excel files (structured)
2. Shivam Jewels' diamond inventory can be exported to CSV for initial seeding
3. Apollo.io, Hunter.io, Proxycurl, SendGrid API keys are procured by the client
4. OpenAI API key is available for outreach generation and embeddings
5. All outreach is in English (internationalisation is out of scope)
6. The platform is single-tenant — Shivam Jewels only (no multi-tenancy in v1)
7. Lead volumes: up to 500 new leads per batch upload, up to 10,000 total active leads per month
8. A manager or admin must approve all outreach before it is sent in production

---

## 8. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Apollo/Hunter API rate limits hit during bulk enrichment | Medium | High | Celery rate-limited queue; exponential backoff; Redis cache |
| LLM hallucination in outreach emails | Medium | High | Human review gate; prompt engineering with strict inventory context |
| OpenAI API latency in high-volume mode | Low | Medium | Celery async; outreach generation is non-blocking |
| SendGrid email bounces damaging domain reputation | Low | High | Hunter.io email verification before send; bounce webhook to flag contacts |
| pgvector query performance at scale | Low | Medium | IVFFlat index on embedding column; query plan reviewed before Phase 4 |
| CSV format inconsistency from trade directories | High | Medium | Flexible ingestion with column mapping config; validation errors returned to rep |

---

## 9. Success Metrics

| Metric | Baseline (Manual) | Target (Automated) |
|---|---|---|
| Time to process one lead | 30–60 minutes | < 5 minutes |
| Leads processed per day | 5–10 | 100+ |
| CRM data completeness | ~60% | 100% |
| Outreach consistency | Variable | Standardised |
| Contact enrichment accuracy | Manual, variable | > 80% email verified |
| Lead-to-response rate | Unmeasured | Tracked per campaign |
