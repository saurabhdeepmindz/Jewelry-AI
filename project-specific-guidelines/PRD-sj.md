# Product Requirements Document (PRD) — Jewelry AI Platform

## Document Info

| Field | Value |
|---|---|
| Product | Jewelry AI — Lead Automation Platform |
| Client | Shivam Jewels |
| Version | 0.1 (POC) |
| Date | 2026-03-17 |
| Status | Draft |

---

## 1. Problem Statement

Shivam Jewels' sales team manually processes raw lead lists from multiple trade directories, enriches them via LinkedIn, matches them against live inventory, and manually sends outreach. This process is:
- **Slow**: Days from list acquisition to first contact
- **Inconsistent**: Quality depends on individual sales rep effort
- **Unscalable**: Cannot process more than ~20–30 leads per day per rep
- **Poorly tracked**: CRM is always outdated; no follow-up automation

---

## 2. Goals

1. Reduce time from lead list to first outreach from days to **minutes**.
2. Eliminate manual contact research (LinkedIn, email finding).
3. Ensure CRM is **always up-to-date** with zero manual entry.
4. Enable **inventory-aware personalization** in outreach messages.
5. Score leads to prioritize high-conversion prospects.

---

## 3. Functional Landscape

### 3.1 Lead Management
- Ingest leads from uploaded files (CSV/Excel) and automated scrapers
- Validate, deduplicate, and normalize lead data
- Store leads with full audit trail

### 3.2 Inventory Matching
- Maintain Shivam Jewels' live diamond/jewelry inventory
- Auto-flag leads as Eligible / Not Eligible based on configurable match rules
- Support rule logic: carat range, cut type (RBC, Princess, etc.), certification, price band

### 3.3 Contact Enrichment
- Auto-find buyer name, title, email, phone from Apollo.io / Hunter.io
- LinkedIn profile enrichment via Proxycurl
- Verify email deliverability before outreach

### 3.4 Outreach Automation
- Generate personalized email content using LLM (referencing specific inventory items)
- Multi-step email sequences (Day 1, Day 5, Day 10)
- WhatsApp outreach via Twilio (Phase 2)
- Human-review gate before first send (configurable)

### 3.5 CRM & Activity Logging
- Auto-log every lead event: ingested, matched, enriched, outreach sent, responded
- Track email opens, clicks, replies (SendGrid webhooks)
- Assign follow-up tasks to sales reps based on engagement

### 3.6 Lead Scoring
- ML model scoring leads 0–100 based on: company size, geo, product match quality, past engagement
- Score surfaced in dashboard and used to prioritize outreach queue

### 3.7 Analytics Dashboard
- Pipeline funnel: Ingested → Matched → Enriched → Contacted → Responded
- Top performing lead sources
- Outreach performance: open rate, reply rate, conversion rate
- Inventory match distribution by cut/carat

---

## 4. Epics

### Epic 1: Lead Ingestion & Data Pipeline
> Enable the system to accept, validate, and store raw lead data from multiple sources.

**User Stories:**

- **US-1.1** — As a sales manager, I want to upload a CSV/Excel file of leads so that the system can process them automatically.
- **US-1.2** — As the system, I want to validate all uploaded leads against a defined schema so that only clean data enters the pipeline.
- **US-1.3** — As the system, I want to deduplicate leads by email and company name so that the same buyer is not contacted twice.
- **US-1.4** — As a sales manager, I want to see a summary of ingestion results (accepted, rejected, duplicates) after each upload.
- **US-1.5** — As the system, I want to scrape leads from GMTs and trade directories on a configurable schedule so that new leads are added without manual effort.

---

### Epic 2: Inventory Management & Match Engine
> Maintain live inventory and automatically flag which leads are eligible for outreach.

**User Stories:**

- **US-2.1** — As an inventory manager, I want to upload and manage Shivam Jewels' current diamond/jewelry inventory in the system.
- **US-2.2** — As the system, I want to auto-match each ingested lead against inventory based on rules (carat range, cut, shape) and flag as Eligible / Not Eligible.
- **US-2.3** — As a sales manager, I want to configure inventory match rules (e.g., min carat 0.5, RBC only) without developer intervention.
- **US-2.4** — As a sales manager, I want to see which inventory items a lead was matched against so I can personalize outreach.

---

### Epic 3: Contact Enrichment
> Automatically discover buyer contact details for each eligible lead.

**User Stories:**

- **US-3.1** — As the system, I want to query Apollo.io to find buyer name, email, phone, and title for each eligible lead.
- **US-3.2** — As the system, I want to verify email deliverability via Hunter.io before sending any outreach.
- **US-3.3** — As the system, I want to enrich buyer profiles with LinkedIn data (company size, buyer tenure) to improve scoring.
- **US-3.4** — As a sales rep, I want to view the enriched contact details for a lead and edit them if incorrect.
- **US-3.5** — As the system, I want to handle enrichment API failures gracefully and retry with a secondary provider.

---

### Epic 4: Outreach Automation
> Generate and send personalized, inventory-aware outreach to qualified leads.

**User Stories:**

- **US-4.1** — As the system, I want to generate a personalized email for each eligible lead referencing specific matched inventory items using an LLM.
- **US-4.2** — As a sales manager, I want to review and approve AI-generated emails before they are sent (optional human-in-the-loop gate).
- **US-4.3** — As the system, I want to send outreach emails via SendGrid and track delivery, opens, and clicks.
- **US-4.4** — As the system, I want to execute a multi-step email sequence (Day 1, Day 5, Day 10) automatically.
- **US-4.5** — As a sales rep, I want to see which leads have responded to outreach and their response content.
- **US-4.6** — As a sales manager, I want to pause or cancel outreach for a specific lead at any time.

---

### Epic 5: CRM & Activity Logging
> Ensure complete, automatic logging of all lead activity with zero manual entry.

**User Stories:**

- **US-5.1** — As the system, I want to log every pipeline event (ingestion, match, enrichment, outreach, response) with timestamps automatically.
- **US-5.2** — As a sales manager, I want to view the complete activity timeline for any lead from a single screen.
- **US-5.3** — As the system, I want to auto-create follow-up tasks for sales reps when a lead replies or engages.
- **US-5.4** — As a sales manager, I want to export the full lead activity log to CSV for reporting.

---

### Epic 6: Lead Scoring & Prioritization
> Rank leads by conversion likelihood to optimize rep time.

**User Stories:**

- **US-6.1** — As the system, I want to score each lead 0–100 based on company profile, inventory match quality, and enrichment data.
- **US-6.2** — As a sales rep, I want to see leads sorted by score so I focus on the highest-priority prospects.
- **US-6.3** — As the system, I want to retrain the scoring model periodically using CRM outcome data.

---

### Epic 7: Analytics & Reporting
> Provide visibility into pipeline health, outreach performance, and conversion metrics.

**User Stories:**

- **US-7.1** — As a sales manager, I want a dashboard showing the full funnel from ingested leads to responses.
- **US-7.2** — As a sales manager, I want to see outreach performance metrics: open rate, reply rate, conversion rate.
- **US-7.3** — As a sales manager, I want to compare lead source quality to prioritize future list purchases.

---

## 5. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Lead processing time (upload to outreach ready) | < 5 minutes per batch of 100 |
| API response time (95th percentile) | < 500ms |
| System uptime (POC) | 99% during business hours |
| Data retention | 5 years (configurable) |
| Audit trail | 100% of pipeline events logged |
| GDPR compliance | Opt-out processing within 24 hours |

---

## 6. Constraints

- POC runs on local infrastructure (no cloud deployment)
- External API budgets: Apollo.io (500 credits/month), Hunter.io (500 lookups/month)
- LLM costs managed via token budgets per lead
- No real-time scraping in POC (file upload only)

---

## 7. Out of Scope (POC)

- WhatsApp automation (Phase 2)
- Fine-tuned jewelry LLM (Phase 3)
- Multi-tenant architecture
- Mobile application
- Real-time inventory sync from ERP
