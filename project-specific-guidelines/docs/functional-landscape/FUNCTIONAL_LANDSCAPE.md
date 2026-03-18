# Functional Landscape — Jewelry AI Platform

**Version:** 1.0
**Status:** Approved
**Owner:** Principal Architect
**Created:** 2026-03-18
**Updated:** 2026-03-18

> **Rules reference:** `project-specific-guidelines/rules/functional-landscape-rules.md`
> Generic rules: `best-practices_rule_set_code/docs/rules/functional-landscape-rules.md`

---

## System Purpose

The Jewelry AI Platform transforms raw trade directory lists into enriched, scored, and outreached buyer relationships for Shivam Jewels — with zero manual data entry. The system automates the full lead lifecycle: ingest → match → enrich → score → generate personalised AI outreach → send and track.

---

## Actors

| Actor | Type | Primary Interaction Layer |
|---|---|---|
| `admin` | Administrative | All layers — config, monitoring, user management |
| `manager` | Supervisory | Layer 5 (Review UI), Layer 6 (Reporting) |
| `rep` | Primary Human | Layer 5 (Dashboard), Layer 4 (trigger workflows) |
| `system` | System Actor | Layers 3, 4, 7 (automated pipeline) |
| `buyer` | External (Phase 3+) | Layer 5 (future self-service portal) |

> Full definitions: `project-specific-guidelines/docs/actors/ACTORS.md`

---

## Layer 7 — AI / Intelligence

| Module | Description | Priority | Linked Epic |
|---|---|---|---|
| Inventory Match Embedding | pgvector semantic similarity — matches lead buyer profile to available inventory | Critical | EPIC-03 |
| Outreach Generation Agent | LangChain LLM chain producing personalised emails referencing matched SKUs | Critical | EPIC-05 |
| Lead Scoring Agent | XGBoost model scoring leads 0–100 on conversion likelihood | High | EPIC-08 |
| Follow-Up Sequence Agent | LangGraph state machine — automated multi-touch follow-up (Day 1/4/7) | Medium | EPIC-10 |
| Jewelry LLM (Fine-Tuned) | Domain-fine-tuned model for superior outreach tone and relevance | Low | EPIC-05 (Phase 7) |

---

## Layer 6 — Reporting & Analytics

| Module | Description | Primary Actor | Linked Epic |
|---|---|---|---|
| Pipeline Funnel Dashboard | Lead counts at each stage: ingested → matched → enriched → outreach sent | `manager`, `admin` | EPIC-09 |
| Outreach Performance Report | Open rates, click rates, reply rates per campaign and rep | `manager` | EPIC-09 |
| Lead Source Quality Report | Conversion rate by trade directory source (GMT, Trade Book, etc.) | `manager`, `admin` | EPIC-09 |
| Lead Scoring Distribution | Score histogram; High / Medium / Low tier breakdown | `rep`, `manager` | EPIC-09 |
| Audit Log Viewer | Immutable CRM activity viewer — all lead events with timestamps | `admin` | EPIC-07 |

---

## Layer 5 — Applications & Portals

| Module | Description | Actor(s) | Linked Epic |
|---|---|---|---|
| Streamlit Dashboard | Main rep UI: lead list, enrichment status, match results, outreach queue | `rep`, `manager` | EPIC-09 |
| Manager Review UI | Approve or reject AI-generated outreach drafts before sending | `manager` | EPIC-05 |
| Admin Panel | User management, API key config, system feature flags | `admin` | EPIC-11 |
| Buyer Self-Service Portal | Browse inventory, submit inquiries (Phase 3+ — out of scope for v1) | `buyer` | Future |

---

## Layer 4 — Workflows & Transactions

| Module | Description | Priority | Linked Epic |
|---|---|---|---|
| Lead Pipeline Workflow | LangGraph state machine: ingest → match → enrich → score → queue outreach | Critical | EPIC-10 |
| Enrichment Workflow | Celery task chain — async enrichment with retry and exponential backoff | Critical | EPIC-04 |
| Outreach Campaign Workflow | n8n multi-step sequence — Day 1 intro, Day 4 follow-up, Day 7 final | High | EPIC-10 |
| CRM Activity Logger | Event-driven — appends immutable activity records on every lead state change | High | EPIC-07 |

---

## Layer 3 — Business Services

| Module | Description | Priority | Linked Epic |
|---|---|---|---|
| Lead Ingestion Service | Validate, deduplicate (by email domain), and persist leads from CSV or API | Critical | EPIC-02 |
| Inventory Matching Service | Rule-based + embedding match: category, carat range, price tier, availability | Critical | EPIC-03 |
| Contact Enrichment Service | Orchestrate Apollo → Hunter → Proxycurl with cache and credit management | Critical | EPIC-04 |
| Lead Scoring Service | Feature extraction + XGBoost inference; writes score to lead record | High | EPIC-08 |
| Outreach Service | Generate draft → route for human review → send via SendGrid → track events | Critical | EPIC-05, EPIC-06 |

---

## Layer 2 — Integration Services

| Module | Description | External System | Linked Epic |
|---|---|---|---|
| Apollo.io Client | Contact enrichment: email, phone, job title, company data | Apollo.io REST API | EPIC-04 |
| Hunter.io Client | Email deliverability verification and domain search | Hunter.io REST API | EPIC-04 |
| Proxycurl Client | LinkedIn profile enrichment for high-value leads | Proxycurl REST API | EPIC-04 |
| SendGrid Client | Transactional and campaign email delivery + event webhooks | SendGrid API v3 | EPIC-06 |
| Twilio Client | WhatsApp outreach via Twilio Conversations API | Twilio API | EPIC-12 |
| n8n Webhook Client | Trigger multi-step email and WhatsApp sequences | n8n REST webhook | EPIC-10 |
| OpenAI Client | LLM completions (outreach), embeddings (matching) | OpenAI API | EPIC-03, EPIC-05 |
| Anthropic Client | Fallback LLM for reasoning agents | Anthropic API | EPIC-05 |
| MLflow Client | Experiment tracking, model registry, metric logging | MLflow REST API | EPIC-13 |

---

## Layer 1 — Core Data & Master Data

| Module | Description | Key Entities | Linked Epic |
|---|---|---|---|
| Lead Master Data | Buyer company records from trade directories; deduplicated by email domain | `Lead`, `LeadStatus`, `LeadSource` | EPIC-02 |
| Inventory Catalog | Shivam Jewels' diamonds and jewelry; availability flag; carat, cut, price | `Inventory`, `ItemCategory`, `ItemStatus` | EPIC-01, EPIC-03 |
| Contact Data | Enriched buyer contacts at each lead company | `Contact`, `ContactSource` | EPIC-04 |
| Outreach Messages | AI-generated email and WhatsApp drafts with approval status | `OutreachMessage`, `OutreachStatus`, `Channel` | EPIC-05 |
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
| Enrichment Workflow (L4) | Contact Enrichment Service (L3), Apollo/Hunter/Proxycurl Clients (L2) | Upper → Lower |
| Contact Enrichment Service (L3) | Apollo.io Client, Hunter.io Client, Proxycurl Client (L2) | Upper → Lower |
| Inventory Matching Service (L3) | Inventory Catalog (L1) | Upper → Lower |
| Outreach Service (L3) | SendGrid Client (L2), Outreach Messages (L1), CRM Activity Logger (L4) | Cross-layer event |
| All Reporting Modules (L6) | All L1 data, L4 workflow logs | Read-only consumers |

---

## Out of Scope (Version 1 — Phase 0 through Phase 6)

The following functional areas are explicitly out of scope:

- Buyer-facing self-service portal (deferred to Phase 3+)
- Direct ERP/accounting integration (Tally, SAP, QuickBooks)
- Mobile application (iOS or Android)
- Multi-tenant / white-label mode for other jewelers
- Real-time chat between rep and buyer
- Automated voice calling (voice AI / IVR)
- Inventory procurement / purchase order management
- Diamond grading lab integrations (GIA, IGI)
- Marketplace listing (IndiaMART, JewelryStreet)

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-03-18 | Initial Functional Landscape — 7 layers, 35 modules, 5 actors |
