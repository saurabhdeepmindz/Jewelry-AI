# Functional Landscape — Jewelry AI Lead Automation Platform

**Version:** 1.0
**Status:** Approved
**Stage:** 1.1 — Discovery
**Created:** 2026-03-18
**Rules reference:** `rules/functional-landscape-rules.md`
**Generic rules:** `best-practices_rule_set_code/docs/rules/functional-landscape-rules.md`

---

## System Purpose

The Jewelry AI Platform transforms raw trade directory lists into enriched, scored, and outreached buyer relationships for **Shivam Jewels** — with zero manual data entry. The system automates the full lead lifecycle:

```
Ingest → Match Inventory → Enrich Contact → Score → Generate AI Outreach → Send & Track
```

**As-Is (Manual):** A rep spends hours per lead — searching LinkedIn, verifying emails, drafting emails, and logging to CRM manually.

**To-Be (Automated):** 1 lead processed in minutes. Standardized enriched data every time. Outreach within hours of identification. CRM always current.

---

## Actors

| Actor | Type | Primary Interaction Layer |
|---|---|---|
| `admin` | Administrative | All layers — config, monitoring, user management |
| `manager` | Supervisory | Layer 5 (Review UI), Layer 6 (Reporting) |
| `rep` | Primary Human | Layer 5 (Dashboard), Layer 4 (trigger workflows) |
| `system` | System Actor | Layers 3, 4, 7 (automated pipeline) |
| `buyer` | External (Phase 3+) | Layer 5 (future self-service portal) |

> Full definitions: `docs/actors/ACTORS.md`

---

## Layer 7 — AI / Intelligence

> Top layer — consumes all layers below. All LLM and ML calls originate here.

| Module | Description | Priority | Linked Epic |
|---|---|---|---|
| Inventory Match Embedding | pgvector semantic similarity — matches lead buyer profile to available inventory | Critical | EPIC-03 |
| Outreach Generation Agent | LangChain LLM chain producing personalised emails referencing matched SKUs | Critical | EPIC-05 |
| Lead Scoring Agent | XGBoost model scoring leads 0–100 on conversion likelihood | High | EPIC-08 |
| Follow-Up Sequence Agent | LangGraph state machine — automated multi-touch follow-up (Day 1 / Day 4 / Day 7) | Medium | EPIC-10 |
| Jewelry LLM (Fine-Tuned) | Domain fine-tuned model for superior outreach tone and relevance | Low | EPIC-05 (Phase 7) |

**Layer rules:**
- All OpenAI/Anthropic API calls are made from this layer only — never from Layer 3 or below
- pgvector embedding generation and similarity search lives here, not in Layer 1

---

## Layer 6 — Reporting & Analytics

> Read-only consumers of Layer 1 data and Layer 4 workflow logs.

| Module | Description | Primary Actor(s) | Linked Epic |
|---|---|---|---|
| Pipeline Funnel Dashboard | Lead counts at each stage: ingested → matched → enriched → outreach sent | `manager`, `admin` | EPIC-09 |
| Outreach Performance Report | Open rates, click rates, reply rates per campaign and rep | `manager` | EPIC-09 |
| Lead Source Quality Report | Conversion rate by trade directory source (GMT, Trade Book, etc.) | `manager`, `admin` | EPIC-09 |
| Lead Scoring Distribution | Score histogram; High / Medium / Low tier breakdown | `rep`, `manager` | EPIC-09 |
| Audit Log Viewer | Immutable CRM activity viewer — all lead events with timestamps | `admin` | EPIC-07 |

---

## Layer 5 — Applications & Portals

> Human-facing interfaces. Thin UI layer — all business logic lives in Layer 3.

| Module | Description | Actor(s) | Linked Epic |
|---|---|---|---|
| Streamlit Dashboard | Main rep UI: lead list, enrichment status, match results, outreach queue | `rep`, `manager` | EPIC-09 |
| Manager Review UI | Approve or reject AI-generated outreach drafts before sending | `manager` | EPIC-05 |
| Admin Panel | User management, API key config, system feature flags | `admin` | EPIC-11 |
| Buyer Self-Service Portal | Browse inventory, submit inquiries — **Phase 3+ only, out of scope for v1** | `buyer` | Future |

---

## Layer 4 — Workflows & Transactions

> Orchestration and event handling. Connects Layer 3 services into end-to-end automated flows.

| Module | Technology | Description | Priority | Linked Epic |
|---|---|---|---|---|
| Lead Pipeline Workflow | LangGraph | State machine: ingest → match → enrich → score → queue outreach | Critical | EPIC-10 |
| Enrichment Workflow | Celery | Async task chain — enrichment with retry and exponential backoff | Critical | EPIC-04 |
| Outreach Campaign Workflow | n8n | Multi-step email sequence — Day 1 intro, Day 4 follow-up, Day 7 final | High | EPIC-10 |
| CRM Activity Logger | Event bus | Event-driven — appends immutable activity records on every lead state change | High | EPIC-07 |

---

## Layer 3 — Business Services

> Core domain logic. All rules, validation, and orchestration of Layer 2 clients.

| Module | Description | Priority | Linked Epic |
|---|---|---|---|
| Lead Ingestion Service | Validate, deduplicate (by email domain), and persist leads from CSV or API | Critical | EPIC-02 |
| Inventory Matching Service | Rule-based + embedding match: category, carat range, price tier, availability | Critical | EPIC-03 |
| Contact Enrichment Service | Orchestrate Apollo → Hunter → Proxycurl with Redis cache and credit management | Critical | EPIC-04 |
| Lead Scoring Service | Feature extraction + XGBoost inference; writes score to lead record | High | EPIC-08 |
| Outreach Service | Generate draft → route for human review → send via SendGrid → track events | Critical | EPIC-05, EPIC-06 |

---

## Layer 2 — Integration Services

> External API adapters. Each adapter translates the external API response into an internal domain model.

| Module | Purpose | External System | Linked Epic |
|---|---|---|---|
| Apollo.io Client | Contact enrichment: email, phone, job title, company data | Apollo.io REST API | EPIC-04 |
| Hunter.io Client | Email deliverability verification and domain search | Hunter.io REST API | EPIC-04 |
| Proxycurl Client | LinkedIn profile enrichment for high-value leads | Proxycurl REST API | EPIC-04 |
| SendGrid Client | Transactional and campaign email delivery + event webhooks | SendGrid API v3 | EPIC-06 |
| Twilio Client | WhatsApp outreach via Twilio Conversations API | Twilio API | EPIC-12 |
| n8n Webhook Client | Trigger multi-step email and WhatsApp sequences | n8n REST webhook | EPIC-10 |
| OpenAI / Anthropic Client | LLM completions (outreach generation), embeddings (matching) | OpenAI API, Anthropic API | EPIC-03, EPIC-05 |
| MLflow Client | Experiment tracking, model registry, metric logging | MLflow REST API | EPIC-13 |

---

## Layer 1 — Core Data & Master Data

> Persistent domain entities. The source of truth for all platform data.

| Module | Description | Key Entities | Linked Epic |
|---|---|---|---|
| Lead Master Data | Buyer company records from trade directories; deduplicated by email domain | `Lead`, `LeadStatus`, `LeadSource` | EPIC-02 |
| Inventory Catalog | Shivam Jewels' diamonds and jewelry; availability flag; carat, cut, price | `Inventory`, `ItemCategory`, `ItemStatus` | EPIC-01, EPIC-03 |
| Contact Data | Enriched buyer contacts at each lead company | `Contact`, `ContactSource` | EPIC-04 |
| Outreach Messages | AI-generated email and WhatsApp drafts with approval workflow | `OutreachMessage`, `OutreachStatus`, `Channel` | EPIC-05 |
| CRM Activity Log | Append-only audit trail of all events in a lead's lifecycle | `CRMActivity`, `ActivityType` | EPIC-07 |
| User & Role Config | Platform users, role assignments, encrypted API keys, feature flags | `User`, `Role`, `Permission`, `APIKeyConfig` | EPIC-11 |

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
| Inventory Matching Service (L3) | Inventory Catalog (L1) | Upper → Lower |
| Outreach Service (L3) | SendGrid Client (L2), Outreach Messages (L1), CRM Logger (L4) | Cross-layer |
| All Reporting Modules (L6) | All L1 data, L4 workflow logs | Read-only consumers |

---

## Actor–Module Matrix (Summary)

> Legend: ✅ Full access, 👁 Read-only, ✍ Create/trigger, 🔒 Approve, ❌ No access

| Module | admin | manager | rep | system |
|---|---|---|---|---|
| Lead Master Data | ✅ | 👁 | 👁 (assigned) | ✍ |
| Inventory Catalog | ✅ | 👁 | 👁 | 👁 |
| Contact Data | ✅ | 👁 | 👁 (assigned) | ✍ |
| Outreach Messages | ✅ | 👁 + 🔒 | 👁 (assigned) | ✍ |
| CRM Activity Log | 👁 | 👁 | 👁 (own) | ✍ (append) |
| User & Role Config | ✅ | ❌ | ❌ | ❌ |
| Lead Pipeline Workflow | ✍ | ❌ | ✍ (assigned) | ✍ |
| Enrichment Workflow | ✍ | ❌ | ✍ (assigned) | ✍ |
| Outreach Campaign | ✍ | ❌ | ❌ | ✍ |
| Streamlit Dashboard | 👁 | 👁 | 👁 | ❌ |
| Manager Review UI | 👁 + 🔒 | 👁 + 🔒 | ❌ | ❌ |
| Admin Panel | ✅ | ❌ | ❌ | ❌ |
| All Reporting | 👁 (global) | 👁 (global) | 👁 (own) | ❌ |

---

## Out of Scope — Version 1 (Phase 0 through Phase 6)

| Excluded Feature | Reason |
|---|---|
| Buyer-facing self-service portal | Deferred to Phase 3+ — complexity out of v1 scope |
| Direct ERP/accounting integration (Tally, SAP, QuickBooks) | Not required for lead automation |
| Mobile application (iOS or Android) | Web-first; mobile deferred |
| Multi-tenant / white-label mode | Single-tenant for Shivam Jewels only |
| Real-time chat between rep and buyer | Async outreach is sufficient for v1 |
| Automated voice calling (voice AI / IVR) | Out of scope |
| Inventory procurement / purchase order management | Separate system responsibility |
| Diamond grading lab integrations (GIA, IGI) | Inventory data entered manually or via import |
| Marketplace listing (IndiaMART, JewelryStreet) | Separate channel strategy |

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-03-18 | Initial Functional Landscape — 7 layers, 35 modules, 5 actors |
