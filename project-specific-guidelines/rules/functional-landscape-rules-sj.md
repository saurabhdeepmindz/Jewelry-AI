# Functional Landscape Rules — Jewelry AI Platform (Project-Specific)

> **Extends:** `best-practices_rule_set_code/docs/rules/functional-landscape-rules.md` (generic rules)
> **Purpose:** Jewelry AI-specific layer names, module catalog, actor-layer mapping, and out-of-scope boundaries.
> **Artifact:** `project-specific-guidelines/docs/functional-landscape/FUNCTIONAL_LANDSCAPE.md`

---

## Platform Context

**Platform:** Jewelry AI Lead Automation — Shivam Jewels
**Domain:** Diamond and jewelry wholesale lead generation, enrichment, and outreach automation
**Stack:** FastAPI · LangChain · LangGraph · PostgreSQL + pgvector · Redis · Celery · n8n · Streamlit

---

## Jewelry AI — 7-Layer Structure

| Layer | Name (Jewelry AI) | Description |
|---|---|---|
| Layer 7 | AI / Intelligence | Lead scoring agent, outreach generation, pgvector semantic search, support AI |
| Layer 6 | Reporting & Analytics | Pipeline funnel, outreach performance, lead source quality, audit log viewer |
| Layer 5 | Applications & Portals | Streamlit Dashboard, Admin Panel, Manager Review UI |
| Layer 4 | Workflows & Transactions | Lead Pipeline Workflow, Outreach Campaign, Enrichment Workflow, CRM Logging |
| Layer 3 | Business Services | Lead Ingestion, Inventory Matching, Contact Enrichment, Lead Scoring, Outreach Service |
| Layer 2 | Integration Services | Apollo.io, Hunter.io, Proxycurl, SendGrid, Twilio, n8n, OpenAI/Anthropic, MLflow |
| Layer 1 | Core Data & Master Data | Leads, Inventory, Contacts, Outreach Messages, CRM Activity, Users & Config |

---

## Module Catalog

### Layer 1 — Core Data & Master Data

| Module | Description | Key Entities | Linked Epic |
|---|---|---|---|
| Lead Master Data | Buyer company records sourced from trade directories | `Lead`, `LeadStatus` enum | EPIC-02 |
| Inventory Catalog | Shivam Jewels' diamond and jewelry stock | `Inventory`, `ItemCategory` enum | EPIC-01, EPIC-03 |
| Contact Data | Enriched buyer contacts at lead companies | `Contact` | EPIC-04 |
| Outreach Messages | AI-generated email and WhatsApp drafts | `OutreachMessage`, `OutreachStatus` enum | EPIC-05 |
| CRM Activity Log | Immutable audit trail of all lead interactions | `CRMActivity` (append-only) | EPIC-07 |
| User & Role Config | Platform users, roles, permissions, API key storage | `User`, `Role`, `Permission` | EPIC-11 |

### Layer 2 — Integration Services

| Module | Description | External System | Linked Epic |
|---|---|---|---|
| Apollo.io Client | Contact enrichment (email, phone, title, LinkedIn) | Apollo.io REST API | EPIC-04 |
| Hunter.io Client | Email deliverability verification | Hunter.io REST API | EPIC-04 |
| Proxycurl Client | LinkedIn profile enrichment | Proxycurl REST API | EPIC-04 |
| SendGrid Client | Transactional and campaign email delivery | SendGrid API v3 | EPIC-06 |
| Twilio Client | WhatsApp outreach messages | Twilio Conversations API | EPIC-12 |
| n8n Webhook Client | Trigger multi-step email sequences | n8n REST webhook | EPIC-10 |
| OpenAI / Anthropic Client | LLM calls for outreach generation and embeddings | OpenAI API, Anthropic API | EPIC-03, EPIC-05 |
| MLflow Client | Experiment tracking and model registry | MLflow REST API | EPIC-13 |

### Layer 3 — Business Services

| Module | Description | Linked Epic |
|---|---|---|
| Lead Ingestion Service | Validate, deduplicate, and persist leads from CSV or API | EPIC-02 |
| Inventory Matching Service | Match leads to available inventory by category, carat, price | EPIC-03 |
| Contact Enrichment Service | Orchestrate Apollo/Hunter/Proxycurl with caching and credit management | EPIC-04 |
| Lead Scoring Service | Score leads 0–100 using ML model; prioritise outreach queue | EPIC-08 |
| Outreach Service | Generate, review-gate, send, and track outreach messages | EPIC-05, EPIC-06 |

### Layer 4 — Workflows & Transactions

| Module | Description | Linked Epic |
|---|---|---|
| Lead Pipeline Workflow | LangGraph state machine: ingest → match → enrich → score → outreach | EPIC-10 |
| Enrichment Workflow | Celery task chain for async enrichment with retry and backoff | EPIC-04 |
| Outreach Campaign Workflow | n8n multi-step email sequence (Day 1, Day 4, Day 7) | EPIC-10 |
| CRM Activity Logger | Event-driven logging of all lead state changes (append-only) | EPIC-07 |

### Layer 5 — Applications & Portals

| Module | Description | Primary Actor(s) | Linked Epic |
|---|---|---|---|
| Streamlit Dashboard | Main UI: lead list, enrichment status, outreach queue, analytics | `rep`, `manager` | EPIC-09 |
| Manager Review UI | Approve or reject AI-generated outreach drafts | `manager` | EPIC-05 |
| Admin Panel | API key management, user management, system config | `admin` | EPIC-11 |

### Layer 6 — Reporting & Analytics

| Module | Description | Primary Actor(s) | Linked Epic |
|---|---|---|---|
| Pipeline Funnel Dashboard | Lead counts at each pipeline stage (ingested → outreach sent) | `manager`, `admin` | EPIC-09 |
| Outreach Performance Report | Open rates, click rates, reply rates per campaign | `manager` | EPIC-09 |
| Lead Source Quality Report | Conversion rate by trade directory source | `manager`, `admin` | EPIC-09 |
| Lead Scoring Distribution | Score histogram; high/medium/low tier breakdown | `rep`, `manager` | EPIC-09 |
| Audit Log Viewer | Immutable CRM activity log for all leads | `admin` | EPIC-07 |

### Layer 7 — AI / Intelligence

| Module | Description | Linked Epic |
|---|---|---|
| Inventory Match Embedding | pgvector semantic similarity matching between lead profile and inventory | EPIC-03 |
| Outreach Generation Agent | LangChain LLM chain generating personalised emails referencing matched inventory | EPIC-05 |
| Lead Scoring Agent | XGBoost model scoring leads on conversion likelihood | EPIC-08 |
| Follow-Up Sequence Agent | LangGraph state machine for automated multi-touch follow-up | EPIC-10 |
| Jewelry LLM (Fine-Tuned) | Domain fine-tuned model for superior outreach quality (Phase 7) | EPIC-05 (Phase 7) |

---

## Actor–Module Interaction Matrix

> Legend: C = Create, R = Read, U = Update, D = Delete, A = Approve, T = Trigger, — = No access

| Module | admin | manager | rep | system | external |
|---|---|---|---|---|---|
| Lead Master Data | CRUD | R | R (assigned) | C, U | — |
| Inventory Catalog | CRUD | R | R | C, U | — |
| Contact Data | R | R | R | C, U | — |
| Outreach Messages | R | R, A | R (assigned) | C | — |
| CRM Activity Log | R | R | R (own) | C | — |
| User & Role Config | CRUD | R | — | — | — |
| Lead Ingestion Service | T | T | T | C | C (API) |
| Inventory Matching Service | T | — | T | T | — |
| Contact Enrichment Service | T | — | T | T | — |
| Lead Scoring Service | T | — | — | T | — |
| Outreach Service | T, A | A | — | T | — |
| Streamlit Dashboard | R | R | R | — | — |
| Manager Review UI | R | R, A | — | — | — |
| Admin Panel | CRUD | — | — | — | — |
| All Reporting Modules | R | R | R (own data) | — | — |

---

## Out of Scope (Jewelry AI v1)

The following are explicitly NOT in scope for the current platform build:

- Buyer-facing self-service portal (planned Phase 3+)
- Direct ERP/accounting system integration (Tally, SAP)
- Mobile application
- Multi-tenant / white-label mode
- Real-time chat between rep and buyer
- Automated telephone calling (voice AI)
- Inventory procurement / purchase order management
- Diamond grading lab integrations (GIA, IGI)

---

## Rules Summary (Jewelry AI Additions)

In addition to the generic rules in `best-practices_rule_set_code/docs/rules/functional-landscape-rules.md`:

- **pgvector is Layer 3, not Layer 1:** Embedding-based matching is a Business Service, not core data — vector storage is an implementation detail of the Matching Service
- **CRM Activity is append-only:** The CRM Activity Log module never supports Update or Delete — this is a business rule, not a technical limitation
- **Enrichment credits are finite:** The Contact Enrichment module must check the cache before calling Layer 2 integration clients — cache hit rate is a tracked metric
- **LLM calls are Layer 7 only:** All OpenAI/Anthropic calls are made from Layer 7 AI modules via LangChain — never directly from Layer 3 services
- **Human review gate:** Outreach Messages require manager approval before the Outreach Service sends them (configurable via `HUMAN_REVIEW_REQUIRED`)
