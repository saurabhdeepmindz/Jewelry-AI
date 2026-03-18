# Product Requirements Document (PRD) — Jewelry AI Lead Automation Platform

**Version:** 1.0
**Status:** Approved
**Stage:** 2.2 — Requirements
**Created:** 2026-03-18
**Input:** ideas.md, FUNCTIONAL_LANDSCAPE.md, ACTORS.md, rules/epic-rules.md

---

## 1. Product Vision

> Empower Shivam Jewels to convert trade directory data into qualified, outreached buyer relationships — automatically, consistently, and at scale — so that the sales team focuses on closing, not prospecting.

---

## 2. User Personas

### Persona 1: The Sales Rep (Ravi)
- **Role:** `rep`
- **Goal:** Process as many leads as possible without manual research
- **Pain today:** Spends most of the day on LinkedIn research and email drafting; leads get stale
- **Value from platform:** Uploads a CSV in the morning; by afternoon, eligible leads are enriched and outreach drafts are ready for review

### Persona 2: The Sales Manager (Priya)
- **Role:** `manager`
- **Goal:** Maintain quality of outreach and visibility of pipeline
- **Pain today:** No visibility into what reps are doing; outreach quality is inconsistent
- **Value from platform:** One-click approval of AI drafts; real-time pipeline funnel; outreach performance metrics

### Persona 3: The Platform Admin (IT/Ops)
- **Role:** `admin`
- **Goal:** Keep the platform running; manage users and API keys
- **Pain today:** No centralised config management; secrets scattered
- **Value from platform:** Admin panel for key rotation, user management, feature flags

---

## 3. Functional Requirements

### FR-01: Lead Ingestion
- The system shall accept CSV/Excel uploads containing raw buyer company records
- Required fields: `company_name`, `source`; optional: `domain`, `email`, `phone`, `country`, `city`
- The system shall deduplicate leads by `email_domain` — no two leads share the same domain
- Invalid rows shall be flagged with per-row error messages without blocking valid rows
- A `rep` may upload; the `system` may ingest via API

### FR-02: Inventory Matching
- The system shall compare each ingested lead against available inventory items
- Match criteria: stone type, shape, carat range, price tier, availability flag
- An eligible lead must match at least one `is_available=true` inventory item
- Leads failing the match shall be marked `NOT_ELIGIBLE` and excluded from enrichment
- Matching shall use rule-based logic (Phase 1) extended with pgvector semantic similarity (Phase 1 / EPIC-03)

### FR-03: Contact Enrichment
- The system shall automatically enrich eligible leads using a cascade: Apollo.io → Hunter.io → Proxycurl
- Enrichment shall persist: `full_name`, `title`, `email`, `email_verified`, `phone`, `linkedin_url`
- All API responses shall be cached in Redis for 7 days — no re-enrichment of already-enriched leads
- Enrichment shall run asynchronously via Celery; the API returns a `job_id` for status polling
- Failed enrichment (all providers exhausted) shall be logged to CRM and the lead flagged for manual review

### FR-04: Lead Scoring
- The system shall score every enriched lead on a 0–100 scale using an XGBoost classifier
- Score predicts conversion likelihood based on: company profile, match quality, contact seniority, email verified, source type
- Scores shall be stored on the `Lead` record and updated after each enrichment
- Leads shall be categorised into tiers: High (70–100), Medium (40–69), Low (0–39)
- The outreach queue shall be sorted by score descending

### FR-05: AI Outreach Generation
- The system shall generate a personalised email draft for each scored, enriched lead
- Each draft shall reference the matched inventory SKUs by name, carat, and shape
- Drafts shall be generated via LangChain using OpenAI GPT-4o with a strict system prompt
- Generated drafts shall be stored as `OutreachMessage` with `status=pending_review`
- The system shall not send any message without explicit approval (when `HUMAN_REVIEW_REQUIRED=true`)

### FR-06: Manager Review & Approval
- A `manager` or `admin` shall be able to approve or reject any `pending_review` outreach message
- Rejection shall require a reason; the reason is logged to CRM
- On approval: `status` transitions to `approved` and the Outreach Service sends immediately
- The Manager Review UI shall list all pending drafts with lead details and matched inventory context

### FR-07: Email Delivery & Tracking
- Approved messages shall be sent via SendGrid transactional API
- The `sendgrid_message_id` shall be stored on the `OutreachMessage` record
- The system shall receive and process SendGrid webhooks: `open`, `click`, `reply`, `bounce`
- Each webhook event shall update the `OutreachMessage` record and append a `CRMActivity` row

### FR-08: CRM Activity Logging
- Every lead state transition shall automatically create an immutable `CRMActivity` record
- Required events to log: `lead_ingested`, `lead_matched`, `lead_enriched`, `lead_scored`, `outreach_drafted`, `outreach_approved`, `outreach_rejected`, `email_sent`, `email_opened`, `email_replied`, `email_bounced`
- No actor — including `admin` — may update or delete a `crm_activity` row
- A `rep` may create manual notes (`activity_type=manual_note`) against their own leads

### FR-09: Streamlit Dashboard
- The Streamlit Dashboard shall display: lead list with filters (status, match_status, source, score tier), per-lead detail view, enrichment status, outreach queue, and basic pipeline counts
- `rep` sees only assigned leads; `manager` and `admin` see all leads
- Triggered actions (enrichment, outreach generation) shall call the FastAPI backend — Streamlit holds no business logic

### FR-10: Authentication & RBAC
- All API endpoints shall require a valid JWT token
- Roles: `ROLE_ADMIN`, `ROLE_MANAGER`, `ROLE_REP`, `ROLE_SYSTEM`
- Data scoping (rep isolation) shall be enforced at the repository layer, not just the UI
- JWT expiry: 24 hours; refresh token not required for v1

### FR-11: Workflow Automation (n8n)
- Day 4 and Day 7 follow-up emails shall be triggered via n8n webhook after an initial outreach is sent
- n8n workflows shall call the FastAPI `/api/v1/outreach/generate/{lead_id}` endpoint for each follow-up step
- If a lead has replied, subsequent sequence steps shall be cancelled

### FR-12: Admin Panel
- The Admin Panel shall provide: user creation and role assignment, API key management (encrypted at rest, masked in UI), feature flag toggles (`HUMAN_REVIEW_REQUIRED`, etc.), system health overview

---

## 4. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | API response time ≤ 200ms for read endpoints; async for all enrichment/generation |
| **Availability** | 99% uptime during business hours (India IST) |
| **Scalability** | Handle up to 500 leads per batch upload; up to 10,000 active leads total |
| **Security** | All API keys encrypted at rest; no secrets in source code; JWT auth on all endpoints; HTTPS only |
| **Observability** | Structured JSON logs with `trace_id`; Celery task status queryable via API |
| **Testability** | ≥ 80% code coverage; all services unit-testable via mocked dependencies |
| **Portability** | Runs fully in Docker Compose; no vendor lock-in for core services |
| **Data Integrity** | All DB writes use transactions; soft deletes only; CRM log is append-only and immutable |

---

## 5. Epic Catalog

### Phase 0

| Epic | Title | Priority | Goal |
|---|---|---|---|
| **EPIC-01** | Platform Foundation & Infrastructure | Critical | Working dev environment; all services running; health endpoint live |

### Phase 1

| Epic | Title | Priority | Goal |
|---|---|---|---|
| **EPIC-02** | Lead Ingestion & Deduplication | Critical | CSV upload → validated, deduplicated `Lead` records with `status=ingested` |
| **EPIC-03** | AI Inventory Matching Engine | Critical | Every ingested lead flagged `ELIGIBLE` or `NOT_ELIGIBLE` against inventory |
| **EPIC-04** | Contact Enrichment Pipeline | Critical | Enriched contact (email, phone, title) created for every eligible lead |
| **EPIC-05** | AI Outreach Generation & Review | Critical | Personalised email draft created, queued for manager review |

### Phase 2

| Epic | Title | Priority | Goal |
|---|---|---|---|
| **EPIC-06** | Email Delivery & Tracking | High | Approved messages sent via SendGrid; open/click/reply tracked |
| **EPIC-07** | CRM Activity & Audit Log | High | Every lead event automatically appended to immutable CRM log |
| **EPIC-08** | Lead Scoring & Prioritization | High | Every lead has a 0–100 score; outreach queue sorted by score |
| **EPIC-09** | Streamlit Dashboard & UI | High | Full ops dashboard: leads, enrichment status, outreach queue, analytics |
| **EPIC-10** | n8n Workflow Automation | High | Day 4 + Day 7 follow-up sequences triggered automatically |
| **EPIC-11** | Authentication & Role-Based Access | High | JWT auth; RBAC enforced at API layer; rep data isolation |

### Phase 3

| Epic | Title | Priority | Goal |
|---|---|---|---|
| **EPIC-12** | WhatsApp Outreach Channel | Medium | WhatsApp messages sent via Twilio for opted-in contacts |
| **EPIC-13** | MLflow Experiment Tracking | Medium | All ML training runs logged; models versioned and promoted via registry |

### Phase 4

| Epic | Title | Priority | Goal |
|---|---|---|---|
| **EPIC-14** | Performance, Caching & Scale | Medium | Redis caching layer; pgvector index tuning; load tested at 10k leads |
| **EPIC-15** | Observability, Monitoring & Alerting | Medium | Prometheus metrics; alert rules for pipeline failures |

---

## 6. User Story Summary (Top-Level, per Epic)

> Full user stories in `agile/stories/EPIC-<ID>/`. Below is the sprint-zero backlog headline list.

### EPIC-01: Platform Foundation
- As a **rep**, I want a working platform so that I can upload leads and see results
- As the **system**, I want all services to start cleanly so that the pipeline can run
- As an **admin**, I want a `/health` endpoint so that I can monitor system availability

### EPIC-02: Lead Ingestion
- As a **rep**, I want to upload a CSV of trade leads so that new leads enter the pipeline automatically
- As the **system**, I want to deduplicate leads by email domain so that no lead is processed twice
- As a **rep**, I want to see per-row validation errors so that I can fix my CSV without re-uploading everything

### EPIC-03: Inventory Matching
- As the **system**, I want to match each lead against available inventory so that only eligible leads proceed to enrichment
- As a **manager**, I want to see each lead's match result so that I can understand why a lead was or wasn't eligible
- As an **admin**, I want to configure match rules so that eligibility criteria can be adjusted without code changes

### EPIC-04: Contact Enrichment
- As the **system**, I want to enrich eligible leads via Apollo.io so that contacts have verified email and phone
- As the **system**, I want to fall back to Hunter.io if Apollo fails so that enrichment succeeds even when one provider is down
- As a **rep**, I want to see enrichment status per lead so that I know which leads are ready for outreach

### EPIC-05: AI Outreach Generation
- As the **system**, I want to generate a personalised outreach email for each enriched lead so that drafts are ready for manager review without manual writing
- As a **manager**, I want to approve or reject AI-generated drafts so that only quality-checked messages are sent
- As a **manager**, I want to see the matched inventory items next to each draft so that I can verify relevance before approving

### EPIC-06: Email Delivery & Tracking
- As the **system**, I want to send approved emails via SendGrid so that outreach is delivered reliably
- As the **system**, I want to receive open/click/reply webhooks so that engagement data is captured in the CRM

### EPIC-07: CRM Activity & Audit Log
- As an **admin**, I want to view the complete activity timeline for any lead so that I can audit every event
- As a **rep**, I want to log a manual note against a lead so that I can record calls or meetings

### EPIC-08: Lead Scoring
- As the **system**, I want to score every lead 0–100 so that the outreach queue prioritises the highest-value leads
- As a **manager**, I want to see the score distribution dashboard so that I understand the quality of the current pipeline

### EPIC-09: Streamlit Dashboard
- As a **rep**, I want to see all my assigned leads with their status and score so that I can manage my daily workflow in one place
- As a **manager**, I want to see the pipeline funnel chart so that I can identify bottlenecks

### EPIC-10: n8n Workflow Automation
- As the **system**, I want to trigger a Day 4 follow-up automatically so that no lead goes cold after the first email
- As the **system**, I want to stop the sequence if the lead has replied so that I don't over-contact engaged prospects

### EPIC-11: Authentication & RBAC
- As an **admin**, I want to create user accounts and assign roles so that platform access is controlled
- As a **rep**, I want to log in with my credentials so that I can access only my assigned leads

---

## 7. Out of Scope (v1)

| Feature | Deferred To |
|---|---|
| Buyer self-service portal | Phase 3+ |
| ERP/accounting integration (Tally, SAP) | Post v1 |
| Mobile app | Post v1 |
| Multi-tenancy | Post v1 |
| Real-time rep–buyer chat | Post v1 |
| Voice AI outreach | Post v1 |
| Diamond grading lab integrations (GIA, IGI) | Post v1 |
| Marketplace listing (IndiaMART) | Post v1 |

---

## 8. Success Criteria per Phase

| Phase | Success Criteria |
|---|---|
| Phase 0 | `docker compose up` starts all services; `GET /health` → `{"status":"ok"}` |
| Phase 1 | CSV upload → leads matched → contacts enriched → AI outreach draft created; visible in Streamlit |
| Phase 2 | Approved draft → sent via SendGrid → opens tracked → CRM updated → follow-up auto-triggered by n8n |
| Phase 3 | WhatsApp message sent for opted-in contacts; ML model versioned in MLflow |
| Phase 4 | 500-lead batch processed in < 10 minutes; all enrichment served from cache on re-run |

---

## 9. Constraints

- **Budget:** API credit costs must be managed; enrichment cache is mandatory, not optional
- **Timeline:** POC (Phase 0–1) target: 4 weeks; Full v1 (Phase 0–2) target: 14 weeks
- **Team:** Single developer with AI assistance (Claude Code)
- **Infrastructure:** Local development via Docker Compose; production deployment to a single VPS or cloud VM
- **Data privacy:** No buyer personal data stored beyond what is needed for outreach; data retained for 12 months maximum

---

## 10. Glossary

| Term | Definition |
|---|---|
| **Lead** | A jewelry buyer company record sourced from a trade directory |
| **Eligible Lead** | A lead whose buyer profile matches at least one available inventory item |
| **Enrichment** | The process of finding and verifying a buyer's contact details via external APIs |
| **Outreach Message** | An AI-generated email or WhatsApp message addressed to a specific buyer contact |
| **CRM Activity** | An immutable event record describing something that happened to a lead |
| **Inventory Match** | The association between a lead and one or more inventory items that match the buyer's needs |
| **Score** | A 0–100 numeric value predicting a lead's likelihood to convert to a sale |
| **Human Review Gate** | The mandatory manager approval step before an outreach message is sent |
| **SKU** | A unique identifier for an individual diamond or jewelry item in inventory |

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-03-18 | Initial PRD — 12 functional requirements, 15 epics, non-functional requirements, success criteria |
