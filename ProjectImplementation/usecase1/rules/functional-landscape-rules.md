# Functional Landscape Rules — Usecase 1: Jewelry AI Lead Automation

> **Extends:** `best-practices_rule_set_code/docs/rules/functional-landscape-rules.md` (generic rules)
> **Purpose:** Defines the 7-layer functional structure, module catalog, actor–module mapping, and out-of-scope boundaries for the Jewelry AI Lead Automation Platform.
> **Artifact to produce:** `docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md`

---

## Platform Context

**Platform:** Jewelry AI Lead Automation — Shivam Jewels
**Domain:** Diamond and jewelry wholesale lead generation, enrichment, and outreach automation
**Stack:** FastAPI · LangChain · LangGraph · PostgreSQL + pgvector · Redis · Celery · n8n · Streamlit

---

## 7-Layer Structure (Bottom → Top)

| Layer | Name | Description |
|---|---|---|
| Layer 1 | Core Data & Master Data | All persistent domain entities — leads, inventory, contacts, outreach messages, CRM activity log, user and role config |
| Layer 2 | Integration Services | External API adapters — Apollo.io, Hunter.io, Proxycurl, SendGrid, Twilio, n8n, OpenAI/Anthropic, MLflow |
| Layer 3 | Business Services | Domain logic — Lead Ingestion, Inventory Matching, Contact Enrichment, Lead Scoring, Outreach Service |
| Layer 4 | Workflows & Transactions | Orchestration — Lead Pipeline Workflow (LangGraph), Enrichment Workflow (Celery), Outreach Campaign (n8n), CRM Logging (event-driven) |
| Layer 5 | Applications & Portals | User interfaces — Streamlit Dashboard, Manager Review UI, Admin Panel |
| Layer 6 | Reporting & Analytics | Read-only views — Pipeline Funnel, Outreach Performance, Lead Scoring Distribution, Audit Log Viewer |
| Layer 7 | AI / Intelligence | AI/ML modules — Inventory Match Embedding (pgvector), Outreach Generation Agent (LangChain), Lead Scoring Agent (XGBoost), Follow-Up Sequence Agent (LangGraph) |

---

## Module Catalog

### Layer 1 — Core Data & Master Data

| Module | Key Entities | Linked Epic |
|---|---|---|
| Lead Master Data | `Lead`, `LeadStatus`, `LeadSource` | EPIC-02 |
| Inventory Catalog | `Inventory`, `ItemCategory`, `ItemStatus` | EPIC-01, EPIC-03 |
| Contact Data | `Contact`, `ContactSource` | EPIC-04 |
| Outreach Messages | `OutreachMessage`, `OutreachStatus`, `Channel` | EPIC-05 |
| CRM Activity Log | `CRMActivity` (append-only) | EPIC-07 |
| User & Role Config | `User`, `Role`, `Permission`, `APIKeyConfig` | EPIC-11 |

### Layer 2 — Integration Services

| Module | External System | Linked Epic |
|---|---|---|
| Apollo.io Client | Apollo.io REST API | EPIC-04 |
| Hunter.io Client | Hunter.io REST API | EPIC-04 |
| Proxycurl Client | Proxycurl REST API | EPIC-04 |
| SendGrid Client | SendGrid API v3 | EPIC-06 |
| Twilio Client | Twilio Conversations API | EPIC-12 |
| n8n Webhook Client | n8n REST webhook | EPIC-10 |
| OpenAI / Anthropic Client | OpenAI API, Anthropic API | EPIC-03, EPIC-05 |
| MLflow Client | MLflow REST API | EPIC-13 |

### Layer 3 — Business Services

| Module | Description | Linked Epic |
|---|---|---|
| Lead Ingestion Service | Validate, deduplicate (by email domain), persist leads from CSV or API | EPIC-02 |
| Inventory Matching Service | Rule-based + embedding match: category, carat range, price tier, availability | EPIC-03 |
| Contact Enrichment Service | Orchestrate Apollo → Hunter → Proxycurl with cache and credit management | EPIC-04 |
| Lead Scoring Service | Feature extraction + XGBoost inference; writes score to lead record | EPIC-08 |
| Outreach Service | Generate draft → route for human review → send via SendGrid → track events | EPIC-05, EPIC-06 |

### Layer 4 — Workflows & Transactions

| Module | Technology | Linked Epic |
|---|---|---|
| Lead Pipeline Workflow | LangGraph state machine: ingest → match → enrich → score → outreach | EPIC-10 |
| Enrichment Workflow | Celery task chain with retry and exponential backoff | EPIC-04 |
| Outreach Campaign Workflow | n8n multi-step email sequence (Day 1, Day 4, Day 7) | EPIC-10 |
| CRM Activity Logger | Event-driven append-only logging on every lead state change | EPIC-07 |

### Layer 5 — Applications & Portals

| Module | Primary Actor(s) | Linked Epic |
|---|---|---|
| Streamlit Dashboard | `rep`, `manager` | EPIC-09 |
| Manager Review UI | `manager` | EPIC-05 |
| Admin Panel | `admin` | EPIC-11 |
| Buyer Self-Service Portal | `buyer` — **Phase 3+ only, out of scope for v1** | Future |

### Layer 6 — Reporting & Analytics

| Module | Primary Actor(s) | Linked Epic |
|---|---|---|
| Pipeline Funnel Dashboard | `manager`, `admin` | EPIC-09 |
| Outreach Performance Report | `manager` | EPIC-09 |
| Lead Source Quality Report | `manager`, `admin` | EPIC-09 |
| Lead Scoring Distribution | `rep`, `manager` | EPIC-09 |
| Audit Log Viewer | `admin` | EPIC-07 |

### Layer 7 — AI / Intelligence

| Module | Description | Linked Epic |
|---|---|---|
| Inventory Match Embedding | pgvector semantic similarity — matches lead buyer profile to inventory | EPIC-03 |
| Outreach Generation Agent | LangChain LLM chain producing personalised emails referencing matched SKUs | EPIC-05 |
| Lead Scoring Agent | XGBoost model scoring leads 0–100 on conversion likelihood | EPIC-08 |
| Follow-Up Sequence Agent | LangGraph state machine — automated multi-touch follow-up (Day 1/4/7) | EPIC-10 |
| Jewelry LLM (Fine-Tuned) | Domain fine-tuned model for superior outreach quality — **Phase 7** | EPIC-05 (Phase 7) |

---

## Actor–Module Interaction Matrix

> Legend: C = Create, R = Read, U = Update, D = Delete, A = Approve, T = Trigger, — = No access

| Module | admin | manager | rep | system | external |
|---|---|---|---|---|---|
| Lead Master Data | CRUD | R | R (assigned) | C, U | — |
| Inventory Catalog | CRUD | R | R | R | — |
| Contact Data | R | R | R (assigned) | C, U | — |
| Outreach Messages | R, A | R, A | R (assigned) | C | — |
| CRM Activity Log | R | R | R (own) | C | — |
| User & Role Config | CRUD | — | — | — | — |
| Lead Ingestion Service | T | — | T | C | C (via API) |
| Inventory Matching Service | T | — | T (assigned) | T | — |
| Contact Enrichment Service | T | — | T (assigned) | T | — |
| Lead Scoring Service | T | — | — | T | — |
| Outreach Service | T, A | A | — | T | — |
| Streamlit Dashboard | R | R | R | — | — |
| Manager Review UI | R, A | R, A | — | — | — |
| Admin Panel | CRUD | — | — | — | — |
| All Reporting Modules | R (global) | R (global) | R (own data) | — | — |

---

## Module Dependency Map

| Module | Depends On | Direction |
|---|---|---|
| Outreach Generation Agent (L7) | Outreach Service (L3), Inventory Catalog (L1) | Upper → Lower |
| Lead Scoring Agent (L7) | Lead Ingestion Service (L3), Contact Data (L1) | Upper → Lower |
| Inventory Match Embedding (L7) | Inventory Matching Service (L3), Inventory Catalog (L1) | Upper → Lower |
| Lead Pipeline Workflow (L4) | All L3 Business Services | Upper → Lower |
| Enrichment Workflow (L4) | Contact Enrichment Service (L3), Apollo/Hunter/Proxycurl (L2) | Upper → Lower |
| Contact Enrichment Service (L3) | Apollo.io Client, Hunter.io Client, Proxycurl Client (L2) | Upper → Lower |
| Outreach Service (L3) | SendGrid Client (L2), Outreach Messages (L1), CRM Logger (L4) | Cross-layer |
| All Reporting Modules (L6) | All L1 data, L4 workflow logs | Read-only consumers |

---

## Out of Scope (Version 1 — Phase 0 through Phase 6)

- Buyer-facing self-service portal (deferred to Phase 3+)
- Direct ERP/accounting integration (Tally, SAP, QuickBooks)
- Mobile application (iOS or Android)
- Multi-tenant / white-label mode
- Real-time chat between rep and buyer
- Automated voice calling (voice AI / IVR)
- Inventory procurement / purchase order management
- Diamond grading lab integrations (GIA, IGI)
- Marketplace listing (IndiaMART, JewelryStreet)

---

## Project-Specific Rules (Additions to Generic)

1. **pgvector is Layer 3, not Layer 1:** Embedding-based matching is a Business Service — vector storage is an implementation detail of the Inventory Matching Service, not core data.
2. **CRM Activity is append-only:** The CRM Activity Log module never supports Update or Delete — this is a business rule enforced at the service layer.
3. **Enrichment credits are finite:** Contact Enrichment must check Redis cache before calling Layer 2 clients. Cache hit rate is a tracked metric. Re-enrichment of an already-enriched lead is a bug.
4. **LLM calls are Layer 7 only:** All OpenAI/Anthropic calls are made from Layer 7 AI modules via LangChain — never directly from Layer 3 services.
5. **Human review gate:** Outreach Messages require manager approval before the Outreach Service sends them (configurable via `HUMAN_REVIEW_REQUIRED` feature flag).
6. **Inventory match is prerequisite for outreach:** A lead must have `match_status = ELIGIBLE` before enrichment or outreach can be triggered.
