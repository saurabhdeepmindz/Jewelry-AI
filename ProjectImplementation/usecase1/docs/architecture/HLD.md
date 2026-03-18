# High-Level Design (HLD) — Jewelry AI Lead Automation Platform

**Version:** 1.0
**Status:** Approved
**Stage:** 3.2 — Architecture
**Created:** 2026-03-18
**Input:** Architecture.md, FUNCTIONAL_LANDSCAPE.md, PRD.md

---

## 1. System Overview

The Jewelry AI Platform is a modular, event-driven automation system that transforms raw trade lead lists into enriched, scored, and personally outreached buyer relationships — with zero manual data entry. It is composed of loosely coupled services orchestrated by LangGraph agents, Celery background workers, and n8n workflow sequences.

All components run in Docker Compose for local development. The platform is designed for single-VPS production deployment.

---

## 2. Overall Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    JEWELRY AI LEAD AUTOMATION PLATFORM                       ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │                    LAYER 5 — PRESENTATION                            │    ║
║  │                                                                      │    ║
║  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │    ║
║  │   │  Dashboard   │  │  Outreach    │  │    Admin     │             │    ║
║  │   │  (rep/mgr)   │  │  Review UI   │  │    Panel     │             │    ║
║  │   │  Streamlit   │  │  (manager)   │  │   (admin)    │             │    ║
║  │   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │    ║
║  └──────────┼─────────────────┼─────────────────┼─────────────────────┘    ║
║             │                 │                  │                           ║
║             └────────────────►│◄─────────────────┘                          ║
║                               │ HTTPS / REST+JSON                           ║
║  ┌────────────────────────────▼────────────────────────────────────────┐    ║
║  │               LAYER 4 — API GATEWAY (FastAPI :8000)                  │    ║
║  │                                                                      │    ║
║  │   JWT Auth Middleware · Rate Limiter · CORS · Request Logger         │    ║
║  │   trace_id injected on every request                                 │    ║
║  │                                                                      │    ║
║  │   /health  /auth  /leads  /inventory  /enrichment                   │    ║
║  │   /outreach  /crm  /analytics  /admin                               │    ║
║  └────┬─────────────────┬────────────────┬──────────────┬──────────────┘    ║
║       │                 │                │              │                    ║
║  ┌────▼──────┐  ┌───────▼──────┐  ┌──────▼──────┐ ┌───▼────────────┐      ║
║  │  LAYER 3  │  │   LAYER 7    │  │   LAYER 4   │ │   LAYER 7      │      ║
║  │ SERVICES  │  │   AGENTS     │  │ BACKGROUND  │ │  ML LAYER      │      ║
║  │           │  │              │  │   TASKS     │ │                │      ║
║  │ Lead      │  │ LangChain    │  │  Celery     │ │ Lead Scorer    │      ║
║  │ Ingestion │  │ Enrichment   │  │  Workers    │ │ (XGBoost)      │      ║
║  │ Inventory │  │ Agent        │  │             │ │                │      ║
║  │ Match     │  │              │  │ ingestion   │ │ Inventory      │      ║
║  │ Enrichment│  │ LangChain    │  │ enrichment  │ │ Match          │      ║
║  │ Outreach  │  │ Outreach     │  │ outreach    │ │ Embedding      │      ║
║  │ Scoring   │  │ Agent        │  │ ml          │ │ (pgvector)     │      ║
║  │ CRM       │  │              │  │  queues     │ │                │      ║
║  │           │  │ LangGraph    │  │             │ │ MLflow         │      ║
║  │           │  │ Lead Pipeline│  │             │ │ Tracking       │      ║
║  └────┬──────┘  └───────┬──────┘  └──────┬──────┘ └───────┬────────┘      ║
║       │                 │                 │                │                 ║
║       └─────────────────┴─────────────────┴────────────────┘                ║
║                                           │                                  ║
║  ┌────────────────────────────────────────▼────────────────────────────┐    ║
║  │                    LAYER 1 — DATA LAYER                              │    ║
║  │                                                                      │    ║
║  │   ┌─────────────────────────────┐   ┌──────────────────────────┐   │    ║
║  │   │        PostgreSQL :5432      │   │       Redis :6379         │   │    ║
║  │   │    + pgvector extension      │   │  Celery broker + cache    │   │    ║
║  │   │                              │   │                           │   │    ║
║  │   │  leads                       │   │  celery task queues       │   │    ║
║  │   │  inventory                   │   │  enrichment cache (7d)    │   │    ║
║  │   │  contacts                    │   │  rate limit counters       │   │    ║
║  │   │  lead_inventory_matches      │   │  session store             │   │    ║
║  │   │  outreach_messages           │   └──────────────────────────┘   │    ║
║  │   │  crm_activity                │                                   │    ║
║  │   │  users / roles               │                                   │    ║
║  │   │  lead_embeddings (vector)    │                                   │    ║
║  │   └─────────────────────────────┘                                   │    ║
║  └──────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  ┌──────────────────────────────────────────────────────────────────────┐    ║
║  │              LAYER 2 — EXTERNAL INTEGRATIONS                         │    ║
║  │                                                                      │    ║
║  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │    ║
║  │  │Apollo.io │ │Hunter.io │ │Proxycurl │ │SendGrid  │ │  n8n     │  │    ║
║  │  │Contact   │ │Email     │ │LinkedIn  │ │Email     │ │Workflow  │  │    ║
║  │  │Enrichment│ │Verify    │ │Enrichment│ │+ Webhooks│ │Sequences │  │    ║
║  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │    ║
║  │                                                                      │    ║
║  │  ┌──────────┐  ┌──────────────────────────────────────────────┐     │    ║
║  │  │  Twilio  │  │              LLM PROVIDERS                    │     │    ║
║  │  │ WhatsApp │  │  OpenAI GPT-4o  ·  Anthropic Claude (fallback)│     │    ║
║  │  │(Phase 3) │  └──────────────────────────────────────────────┘     │    ║
║  │  └──────────┘                                                        │    ║
║  └──────────────────────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. Lead Pipeline Flow Diagram

```
  ┌─────────────────────────────────────────────────────┐
  │            rep uploads CSV / API push                │
  └────────────────────────┬────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Lead Ingestion       │
              │   Service              │  → Validate columns
              │   (Layer 3)            │  → Deduplicate by email_domain
              │                        │  → Persist Lead (status=ingested)
              └────────────┬───────────┘
                           │ LeadIngestedEvent (EventBus)
                           ▼
              ┌────────────────────────┐
              │   Inventory Match      │
              │   Service              │  → Rule-based: stone_type, carat, shape
              │   (Layer 3 + L7)       │  → pgvector: semantic similarity
              └────────────┬───────────┘
                           │
               ┌───────────┴────────────┐
               │                        │
         ELIGIBLE                  NOT_ELIGIBLE
               │                        │
               ▼                        ▼
  ┌────────────────────────┐  ┌─────────────────────┐
  │  Contact Enrichment    │  │  Mark NOT_ELIGIBLE   │
  │  Workflow (Celery L4)  │  │  Log to CRM          │
  │                        │  │  Stop pipeline       │
  │  Apollo.io →           │  └─────────────────────┘
  │  Hunter.io (fallback) →│
  │  Proxycurl (LinkedIn)  │
  │  ↓ Cache in Redis 7d   │
  └────────────┬───────────┘
               │
               ▼
  ┌────────────────────────┐
  │   Lead Scoring         │
  │   Service (Layer 3+L7) │  → Extract features from Lead+Contact+Match
  │                        │  → XGBoost inference → score 0–100
  │                        │  → Update Lead.score
  └────────────┬───────────┘
               │
               ▼
  ┌────────────────────────┐
  │  Outreach Generation   │
  │  Agent (Layer 7)       │  → LangChain + GPT-4o
  │                        │  → System prompt: Shivam Jewels persona
  │                        │  → User prompt: lead + matched SKUs
  │                        │  → Save OutreachMessage (status=pending_review)
  └────────────┬───────────┘
               │
               ▼
  ┌────────────────────────┐
  │  Human Review Gate     │  ← HUMAN_REVIEW_REQUIRED=true (default)
  │  (Manager Review UI)   │
  │                        │
  │  manager APPROVES ─────┼──────────────────────────────────────┐
  │  manager REJECTS ──────┼── Log rejection reason to CRM        │
  └────────────────────────┘                                       │
                                                                   ▼
                                               ┌────────────────────────┐
                                               │   SendGrid Email Send  │
                                               │   (Layer 2)            │
                                               │                        │
                                               │   → sent_at recorded   │
                                               │   → CRM: email_sent    │
                                               └────────────┬───────────┘
                                                            │
                                      ┌─────────────────────┴──────────────────┐
                                      │                                         │
                              Webhook: open/click/reply             n8n Follow-Up Sequence
                                      │                                         │
                                      ▼                                         ▼
                              CRM Activity appended             Day 4 follow-up email
                              OutreachMessage updated           Day 7 final follow-up
                                                                (stops if lead replied)
```

---

## 4. Deployment Diagram (Local Docker Compose)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LOCAL MACHINE                                │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     Docker Compose Network                    │   │
│  │                                                              │   │
│  │  ┌─────────────────┐   ┌─────────────────┐                  │   │
│  │  │   streamlit     │   │    fastapi      │                  │   │
│  │  │   :8501         │   │    :8000        │                  │   │
│  │  │  (Streamlit UI) │   │  (REST API)     │                  │   │
│  │  └─────────────────┘   └────────┬────────┘                  │   │
│  │                                 │                            │   │
│  │  ┌─────────────────┐   ┌────────▼────────┐                  │   │
│  │  │  celery-worker  │   │  celery-beat    │                  │   │
│  │  │  (async tasks)  │   │  (scheduler)    │                  │   │
│  │  └─────────────────┘   └─────────────────┘                  │   │
│  │                                                              │   │
│  │  ┌─────────────────┐   ┌─────────────────┐                  │   │
│  │  │   postgres      │   │     redis       │                  │   │
│  │  │   :5432         │   │     :6379       │                  │   │
│  │  │ + pgvector ext  │   │  broker+cache   │                  │   │
│  │  └─────────────────┘   └─────────────────┘                  │   │
│  │                                                              │   │
│  │  ┌─────────────────┐   ┌─────────────────┐                  │   │
│  │  │      n8n        │   │    mlflow       │                  │   │
│  │  │   :5678         │   │    :5000        │                  │   │
│  │  │ (workflows)     │   │  (ML tracking)  │                  │   │
│  │  └─────────────────┘   └─────────────────┘                  │   │
│  │                                                              │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          │                      │                    │
└──────────────────────────┼──────────────────────┼────────────────────┘
                           │                      │
                           ▼                      ▼
               [External APIs]           [LLM Providers]
               Apollo.io                 OpenAI GPT-4o
               Hunter.io                 Anthropic Claude
               Proxycurl                 (via HTTPS only)
               SendGrid
               Twilio (Phase 3)
```

---

## 5. Data Flow Patterns

### Pattern A — Synchronous (FastAPI Request-Response)
```
Streamlit UI
    │ HTTP POST /api/v1/leads/upload
    ▼
FastAPI Router (leads.py)
    │ call
    ▼
LeadIngestionService.ingest_batch()
    │ call
    ▼
LeadRepository.create()
    │ async SQL
    ▼
PostgreSQL
    │ result
    ▲
FastAPI returns 201 with summary
```
**Used for:** CRUD operations, status queries, single-record actions.

### Pattern B — Asynchronous (Celery Task Queue)
```
FastAPI Router
    │ enqueue task
    ▼
Redis (broker)
    │ picked up by
    ▼
Celery Worker
    │ executes
    ▼
EnrichmentService → Apollo/Hunter/Proxycurl
    │ result
    ▼
PostgreSQL (Contact record)
    │
FastAPI: client polls GET /api/v1/enrichment/status/{job_id}
```
**Used for:** Bulk enrichment, outreach generation, ML scoring, batch ingestion.

### Pattern C — Event-Driven (Internal EventBus)
```
LeadIngestionService.ingest()
    │ publishes LeadIngestedEvent
    ▼
EventBus.publish(LeadIngestedEvent)
    │ dispatches to all subscribers
    ├── InventoryMatchService.on_lead_ingested()
    └── CRMService.log_activity(lead_ingested)
```
**Used for:** Decoupled post-ingestion triggers, CRM logging on state changes.

### Pattern D — Webhook Inbound (SendGrid Events)
```
SendGrid
    │ POST /api/v1/outreach/webhook
    ▼
FastAPI WebhookRouter
    │ parse event type (open/click/reply/bounce)
    ▼
OutreachService.handle_webhook_event()
    ├── OutreachRepository.update_status()
    └── CRMService.log_activity(email_opened / email_replied)
```

---

## 6. Security Architecture

```
Streamlit / External Client
         │
         │ HTTPS (TLS 1.2+)
         ▼
    FastAPI
         │
         ├── JWTAuthMiddleware
         │     └── Validate Bearer token on every request
         │         Decode user_id + role → inject into request.state
         │
         ├── RateLimitMiddleware
         │     └── 100 req/min per IP on enrichment endpoints
         │         100 req/min per user on outreach generation
         │
         ├── CORSMiddleware
         │     └── Allowed origins: Streamlit host only
         │
         ▼
    Service Layer
         │
         ├── Role check via RBAC decorator on each service method
         │     └── rep: assigned_to = current_user.id filter added to all queries
         │
         ▼
    Repository Layer
         │
         └── Parameterized queries only — no string concatenation in SQL
         └── Soft deletes — no hard DELETE statements
         │
         ▼
    PostgreSQL
         └── Row-level security (future Phase 4)
```

**API Key Storage:**
- All external API keys stored in `.env` — never committed to version control
- In Admin Panel: keys displayed masked (`sk-...****`), rotation triggers re-encryption
- Encryption at rest: `cryptography.fernet` symmetric encryption for stored keys

**JWT Configuration:**
- Algorithm: `HS256`
- Expiry: 24 hours
- Payload: `user_id`, `role`, `exp`, `iat`

---

## 7. Integration Architecture

```
Jewelry AI Backend
         │
         ├──► Apollo.io REST API      [Primary contact enrichment]
         │         └── POST /v1/people/match
         │         └── Retry: 3x with exponential backoff (60s, 120s, 240s)
         │         └── Cache response in Redis key: apollo:{email_domain} TTL=7d
         │
         ├──► Hunter.io REST API      [Email verification + fallback enrichment]
         │         └── GET /v2/email-finder
         │         └── Fallback: triggered when Apollo returns no email
         │         └── Mark email_verified=true/false based on result
         │
         ├──► Proxycurl REST API      [LinkedIn enrichment — high-value leads only]
         │         └── GET /api/v2/linkedin
         │         └── Only called for leads with score ≥ LEAD_SCORE_HIGH_THRESHOLD
         │         └── Cache response in Redis key: proxycurl:{linkedin_url} TTL=7d
         │
         ├──► SendGrid API v3         [Email delivery + event tracking]
         │         └── POST /v3/mail/send
         │         └── Webhooks: open, click, reply, bounce → POST /api/v1/outreach/webhook
         │         └── store sendgrid_message_id on OutreachMessage
         │
         ├──► n8n REST Webhook        [Multi-step follow-up sequence trigger]
         │         └── POST {N8N_WEBHOOK_URL}/outreach-sequence
         │         └── Payload: lead_id, contact_id, sequence_step, send_at
         │
         ├──► OpenAI API              [LLM generation + embeddings]
         │         └── POST /v1/chat/completions — outreach email generation
         │         └── POST /v1/embeddings — inventory match vectors
         │         └── Model: gpt-4o; max_tokens: 800 per outreach email
         │
         ├──► Anthropic API           [Fallback LLM for reasoning agents]
         │         └── Only invoked when OpenAI returns error or timeout
         │         └── Model: claude-sonnet-4-6
         │
         └──► MLflow REST API         [Experiment tracking + model registry]
                   └── Log training runs, parameters, metrics
                   └── Register and version XGBoost model artifacts
```

---

## 8. Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Frontend | Streamlit | 1.32+ | Ops dashboard — rep, manager, admin UIs |
| API | FastAPI | 0.110+ | Async REST API with OpenAPI docs |
| ORM | SQLAlchemy (async) | 2.0+ | Database access with connection pooling |
| Migrations | Alembic | 1.13+ | Schema versioning and rollback |
| AI Orchestration | LangChain | 0.2+ | LLM chains, tool use, prompt templates |
| Workflow Graphs | LangGraph | 0.1+ | Stateful multi-step pipeline automation |
| Task Queue | Celery | 5.3+ | Async background task execution |
| Message Broker | Redis | 7.2+ | Celery broker + enrichment cache |
| Database | PostgreSQL | 16+ | Primary RDBMS |
| Vector Search | pgvector | 0.7+ | Semantic inventory matching |
| ML | XGBoost | 2.x | Lead conversion scoring |
| Experiment Tracking | MLflow | 2.x | Model versioning and metrics |
| Workflow Automation | n8n | 1.x | Email follow-up sequences |
| Containerisation | Docker + Compose | latest | Local dev + production packaging |
| Linting | ruff | latest | Fast Python linter + formatter |
| Type Checking | mypy | latest | Static type analysis |
| Testing | pytest + pytest-asyncio | latest | Unit + integration + e2e tests |
| Auth | python-jose + passlib | latest | JWT creation/validation + password hashing |

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-03-18 | Initial HLD — architecture diagram, pipeline flow, deployment, data flows, security, integration architecture |
