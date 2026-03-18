# High-Level Design (HLD) — Template

> **Generic template — no project-specific content.**
> Replace `<Platform Name>`, `<Entity>`, and all `<placeholder>` values with your project's specifics.

---

## 1. System Overview

`<Platform Name>` is a modular, event-driven system that `<describe the core transformation or purpose>`. The system is composed of loosely coupled services orchestrated by `<orchestration technology: LangGraph / Celery / n8n>` and automation workflows.

---

## 2. Overall Architecture Diagram

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        <PLATFORM NAME>                                       ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────┐    ║
║  │                    PRESENTATION LAYER                                │    ║
║  │                                                                      │    ║
║  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │    ║
║  │   │   <UI Page>  │  │  <UI Page>   │  │  <UI Page>   │             │    ║
║  │   │  (Streamlit) │  │  (Streamlit) │  │  (Streamlit) │             │    ║
║  │   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │    ║
║  └──────────┼─────────────────┼─────────────────┼─────────────────────┘    ║
║             │                 │                  │                           ║
║             └────────────────►│◄─────────────────┘                          ║
║                               │ REST / JSON                                 ║
║  ┌────────────────────────────▼────────────────────────────────────────┐    ║
║  │                     API GATEWAY LAYER                                │    ║
║  │                  FastAPI  (Port <PORT>)                              │    ║
║  │   Auth Middleware | Rate Limit | Request Logging | CORS              │    ║
║  │                                                                      │    ║
║  │   /<resource_a>  /<resource_b>  /<resource_c>  /<resource_d>        │    ║
║  └───────┬────────────────┬───────────────┬──────────────┬─────────────┘    ║
║          │                │               │              │                   ║
║  ┌───────▼──────┐ ┌───────▼──────┐ ┌──────▼──────┐ ┌───▼──────────┐       ║
║  │   SERVICES   │ │    AGENTS    │ │  BACKGROUND │ │   ML LAYER   │       ║
║  │              │ │              │ │    TASKS    │ │              │       ║
║  │ <Service A>  │ │ LangChain    │ │   Celery    │ │ <Model A>    │       ║
║  │ <Service B>  │ │ LangGraph    │ │   Workers   │ │ <Model B>    │       ║
║  │ <Service C>  │ │ <Agent A>    │ │             │ │              │       ║
║  │ <Service D>  │ │ <Agent B>    │ │ <queue_a>_  │ │ MLflow       │       ║
║  │              │ │              │ │ <queue_b>_  │ │ Tracking     │       ║
║  └───────┬──────┘ └───────┬──────┘ │ tasks       │ └───────┬──────┘       ║
║          │                │        └──────┬──────┘         │               ║
║          └────────────────┼───────────────┼────────────────┘               ║
║                           │               │                                  ║
║  ┌────────────────────────▼───────────────▼────────────────────────────┐    ║
║  │                      DATA LAYER                                      │    ║
║  │                                                                      │    ║
║  │   ┌────────────────────────┐    ┌────────────────────┐              │    ║
║  │   │      PostgreSQL        │    │       Redis         │              │    ║
║  │   │  + pgvector (optional) │    │  Task Queue + Cache │              │    ║
║  │   │                        │    │                     │              │    ║
║  │   │  <table_a>             │    │  celery_broker      │              │    ║
║  │   │  <table_b>             │    │  rate_limit_counters│              │    ║
║  │   │  <table_c>             │    │  session_cache      │              │    ║
║  │   └────────────────────────┘    └────────────────────┘              │    ║
║  └──────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
║  ┌──────────────────────────────────────────────────────────────────────┐    ║
║  │                    EXTERNAL INTEGRATIONS                             │    ║
║  │                                                                      │    ║
║  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │    ║
║  │  │<Provider>│ │<Provider>│ │<Provider>│ │<Provider>│ │<Provider>│  │    ║
║  │  │<Purpose> │ │<Purpose> │ │<Purpose> │ │<Purpose> │ │<Purpose> │  │    ║
║  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │    ║
║  │                                                                      │    ║
║  │  ┌──────────────────────────────────────────────────────────────┐   │    ║
║  │  │                    LLM PROVIDERS                              │   │    ║
║  │  │  OpenAI GPT-4o  /  Anthropic Claude  /  Fine-tuned Model     │   │    ║
║  │  └──────────────────────────────────────────────────────────────┘   │    ║
║  └──────────────────────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 3. Core Pipeline Flow Diagram

```
 [<Input Source>]
          │
          ▼
 ┌─────────────────┐
 │  <Step 1>       │  → Validate → Deduplicate → Persist
 │  Service        │
 └────────┬────────┘
          │ <DomainEvent>
          ▼
 ┌─────────────────┐
 │  <Step 2>       │  → Apply rules → Flag: ELIGIBLE / NOT_ELIGIBLE
 │  Engine         │
 └────────┬────────┘
          │ (ELIGIBLE only)
          ▼
 ┌─────────────────┐
 │  <Step 3>       │  → External API A → External API B (fallback)
 │  Agent          │  → Store enriched data
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │  <Step 4>       │  → ML model → Score 0-100
 │  Service        │
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │  <Step 5>       │  → LLM generates output
 │  Generation     │  → [HUMAN REVIEW GATE] (optional)
 │  Agent          │  → Delivery channel → Track events
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │  Activity Log   │  → Log all events → Assign follow-ups
 │  Service        │
 └─────────────────┘
```

---

## 4. Deployment Diagram (Local)

```
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL MACHINE                             │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Docker Compose                      │   │
│  │                                                      │   │
│  │  ┌───────────────┐  ┌───────────────┐               │   │
│  │  │  streamlit    │  │   fastapi     │               │   │
│  │  │  :<PORT>      │  │   :<PORT>     │               │   │
│  │  └───────────────┘  └───────────────┘               │   │
│  │                                                      │   │
│  │  ┌───────────────┐  ┌───────────────┐               │   │
│  │  │  celery       │  │   celery      │               │   │
│  │  │  worker       │  │   beat        │               │   │
│  │  │  (async jobs) │  │  (scheduler)  │               │   │
│  │  └───────────────┘  └───────────────┘               │   │
│  │                                                      │   │
│  │  ┌───────────────┐  ┌───────────────┐               │   │
│  │  │  postgres     │  │    redis      │               │   │
│  │  │  :5432        │  │    :6379      │               │   │
│  │  └───────────────┘  └───────────────┘               │   │
│  │                                                      │   │
│  │  ┌───────────────┐  ┌───────────────┐               │   │
│  │  │  <service_a>  │  │  <service_b>  │               │   │
│  │  │  :<PORT>      │  │   :<PORT>     │               │   │
│  │  └───────────────┘  └───────────────┘               │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
          │                      │
          ▼                      ▼
  [External APIs]         [LLM Providers]
  <Provider A>            OpenAI / Anthropic
  <Provider B>            (via HTTPS)
```

---

## 5. Data Flow Architecture

### Synchronous (FastAPI)
- UI → FastAPI → Service → Repository → PostgreSQL
- Response returned in request-response cycle
- Used for: CRUD operations, dashboard queries, single-record actions

### Asynchronous (Celery)
- API enqueues task to Redis
- Celery worker picks up task
- Worker runs: bulk operations, external API calls, processing pipelines
- Results stored in PostgreSQL
- UI polls status via FastAPI

### Event-Driven (Internal Event Bus)
- Services publish domain events
- Subscribers trigger downstream actions
- Fully in-process for POC (no external message broker needed)

---

## 6. Security Architecture

```
Browser/Frontend
      │
      │ HTTPS (TLS)
      ▼
  FastAPI ──► JWT Validation Middleware
      │
      │ Parameterized queries only
      ▼
  PostgreSQL ──► Row-level security (recommended for multi-tenant)
```

- All API keys stored in `.env` (never committed to version control)
- JWT tokens with configurable expiry (default: 24 hours)
- Rate limiting on sensitive/expensive endpoints
- All external API calls over HTTPS

---

## 7. Integration Architecture

```
<Platform> Backend
       │
       ├──► <Provider A> REST API     [<Purpose>]
       │         └── Retry: 3x with exponential backoff
       │
       ├──► <Provider B> REST API     [<Purpose>]
       │         └── Fallback: <fallback strategy>
       │
       ├──► <Provider C> REST API     [<Purpose>]
       │         └── Cache results in Redis for <N> days
       │
       ├──► <Delivery Provider> API   [<Purpose>]
       │         └── Webhook: events → activity log
       │
       ├──► <Workflow Engine> API     [Workflow trigger]
       │         └── Trigger multi-step sequences
       │
       └──► OpenAI / Anthropic        [LLM generation]
                 └── Model: <model-name>
                 └── Max tokens: <N> per generation
```

---

## 8. Technology Stack Summary

| Layer | Technology | Version |
|---|---|---|
| Frontend | Streamlit | 1.32+ |
| API | FastAPI | 0.110+ |
| ORM | SQLAlchemy (async) | 2.0+ |
| Migrations | Alembic | 1.13+ |
| AI Orchestration | LangChain | 0.2+ |
| Workflow Graphs | LangGraph | 0.1+ |
| Task Queue | Celery | 5.3+ |
| Message Broker | Redis | 7.2+ |
| Database | PostgreSQL | 16+ |
| Vector Search | pgvector (optional) | 0.7+ |
| ML | scikit-learn / XGBoost | latest |
| Experiment Tracking | MLflow | 2.x |
| Workflow Automation | n8n (optional) | 1.x |
| Containerization | Docker + Docker Compose | latest |

> **Note:** Remove or replace rows that do not apply to your project. Add rows for project-specific technologies.
