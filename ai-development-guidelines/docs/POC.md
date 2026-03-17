# POC — Phase 0: Local Demo Build

## Overview

Phase 0 is the **Proof of Concept** — a fully functional, locally deployable version of the Jewelry AI platform that demonstrates the core end-to-end lead automation story. It runs entirely on a developer laptop via Docker Compose and can be demo-ed to Shivam Jewels stakeholders within 2–3 weeks of development.

**Goal:** Show the complete pipeline from CSV upload → inventory match → contact enrichment → AI-drafted outreach → dashboard — with zero manual steps in between.

---

## POC Scope

### In Scope

| Feature | Notes |
|---|---|
| Lead upload via CSV/Excel | Streamlit file uploader |
| Lead validation & deduplication | Rule-based, Pydantic schemas |
| Inventory upload via CSV | Pre-seeded demo inventory |
| Rule-based inventory matching | Configurable carat/shape/cert rules |
| Contact enrichment (Apollo.io) | Single lead + batch trigger |
| Email verification (Hunter.io) | Post-enrichment auto-verify |
| Lead scoring (rule-based proxy) | Simple weighted score, no ML model yet |
| AI outreach email generation | GPT-4o via LangChain |
| Human review gate | Review draft before sending |
| Email sending via SendGrid | Real send in demo mode |
| CRM activity timeline | Per-lead full event history |
| Streamlit dashboard | Funnel chart, lead table, outreach queue |
| PostgreSQL + pgvector | Full schema, Alembic migrations |
| Redis + Celery | Async enrichment and outreach jobs |
| Docker Compose local deployment | One command: `make up` |
| Synthetic demo data seed | `python scripts/seed_demo_data.py` |

### Out of Scope (POC)

| Feature | Phase |
|---|---|
| Live web scraping | Phase 3 |
| WhatsApp outreach | Phase 2 |
| ML lead scoring model | Phase 5 |
| Fine-tuned jewelry LLM | Phase 7 |
| n8n multi-step email sequences | Phase 4 |
| LangGraph full pipeline automation | Phase 4 |
| LinkedIn enrichment (Proxycurl) | Phase 3 |
| Multi-user auth with RBAC | Phase 6 |
| Analytics with date filters | Phase 6 |

---

## POC Architecture (Simplified)

```
┌─────────────────────────────────────────────────────────┐
│                   DEVELOPER LAPTOP                       │
│                                                         │
│  ┌────────────────┐  ┌────────────────┐                 │
│  │   Streamlit    │  │    FastAPI     │                 │
│  │   :8501        │  │    :8000       │                 │
│  └────────────────┘  └──────┬─────┬──┘                 │
│                             │     │                     │
│  ┌────────────────┐  ┌──────▼──┐  ▼                    │
│  │  PostgreSQL    │  │  Celery │  External APIs         │
│  │  :5432         │  │  Worker │  Apollo.io             │
│  │  + pgvector    │  └─────────┘  Hunter.io             │
│  └────────────────┘               OpenAI                │
│  ┌────────────────┐               SendGrid              │
│  │    Redis       │                                     │
│  │    :6379       │                                     │
│  └────────────────┘                                     │
└─────────────────────────────────────────────────────────┘
```

---

## POC Demo Flow (15-Minute Script)

### Act 1: Lead Ingestion (3 min)

1. Open Streamlit UI at `http://localhost:8501`
2. Navigate to **Leads** page
3. Upload `demo_leads.csv` (50 rows from `scripts/demo_data/`)
4. Show ingestion summary: "42 accepted, 5 duplicates detected, 3 rejected (missing company name)"
5. Show lead table with all 42 leads in `ingested` status

### Act 2: Inventory Matching (2 min)

1. Click **"Run Inventory Match"** on the leads table
2. Refresh — show 22 leads marked `eligible` (green), 20 `not_eligible` (red)
3. Click on an eligible lead — show the 2–3 matched inventory items (SKU, carat, GIA cert)
4. Point out: "This matching happened in under 2 seconds for all 42 leads"

### Act 3: Contact Enrichment (3 min)

1. Select 3 eligible leads
2. Click **"Enrich Contacts"**
3. Show Celery job progress bar
4. After ~10 seconds: leads show buyer name, title, verified email, phone
5. Show the enrichment source badge (Apollo.io)
6. Highlight: "This used to take 20–30 minutes per lead on LinkedIn"

### Act 4: AI Outreach Generation (4 min)

1. Click **"Generate Outreach"** on an enriched lead
2. Show the AI-generated email with:
   - Buyer name personalization
   - Reference to specific matched diamond (carat, GIA cert)
   - Professional tone
3. Edit 2 words to show human review capability
4. Click **"Send"**
5. Check email inbox — show the delivered email
6. Navigate to **Outreach** page — show sent status with timestamp

### Act 5: Dashboard (3 min)

1. Navigate to **Dashboard**
2. Show pipeline funnel: 42 ingested → 22 eligible → 15 enriched → 5 contacted
3. Show CRM timeline for one lead: ingested → matched → enriched → email sent
4. Show lead score distribution
5. Closing statement: "The entire pipeline from upload to sent email took under 5 minutes"

---

## POC Setup Instructions

### Prerequisites

| Tool | Version | Install |
|---|---|---|
| Docker Desktop | Latest | docker.com |
| Python | 3.11+ | python.org |
| Git | Any | git-scm.com |
| OpenAI API Key | — | platform.openai.com |
| Apollo.io API Key | — | apollo.io (free tier) |
| Hunter.io API Key | — | hunter.io (free tier) |
| SendGrid API Key | — | sendgrid.com (free tier) |

### Step-by-Step Setup

```bash
# 1. Clone repository
git clone https://github.com/saurabhdeepmindz/Jewelry-AI.git
cd Jewelry-AI

# 2. Copy and fill environment file
cp .env.example .env
# Open .env and fill in: OPENAI_API_KEY, APOLLO_API_KEY, HUNTER_API_KEY, SENDGRID_API_KEY

# 3. Start all services
make up
# Wait ~60 seconds for all containers to be healthy

# 4. Run database migrations
make migrate

# 5. Seed demo data
python scripts/seed_demo_data.py

# 6. Open Streamlit UI
open http://localhost:8501

# 7. Open API docs (optional)
open http://localhost:8000/docs
```

### Demo CSV File

A ready-to-use demo CSV is available at `scripts/demo_data/demo_leads.csv`. It contains 50 realistic synthetic leads pre-formatted for import.

---

## POC Limitations & Known Constraints

| Limitation | Reason | Full Solution |
|---|---|---|
| File upload only (no live scraping) | Scraper needs rate-limiting + proxy setup | Phase 3 |
| No email sequence automation | n8n workflows built in Phase 4 | Phase 4 |
| Rule-based scoring (not ML) | ML model needs training data | Phase 5 |
| Single user (no login screen) | Auth added in Phase 6 | Phase 6 |
| No WhatsApp | Twilio setup + Phase 2 | Phase 2 |
| SendGrid limited to 100 free emails/day | Free tier limit | Upgrade after POC |
| Apollo free tier: 50 credits/month | Budget constraint | Paid plan after POC |

---

## POC Success Criteria

The POC is considered complete when:

- [ ] `make up` starts all services with no errors on a fresh machine
- [ ] `make migrate` runs all Alembic migrations cleanly
- [ ] `python scripts/seed_demo_data.py` seeds 50 leads + 25 inventory items
- [ ] CSV upload of 50 leads completes in < 10 seconds
- [ ] Inventory matching of 50 leads completes in < 5 seconds
- [ ] Contact enrichment of 1 lead completes in < 30 seconds
- [ ] AI outreach email generated for enriched lead in < 15 seconds
- [ ] Email sent via SendGrid and received in inbox
- [ ] Streamlit dashboard shows correct funnel numbers
- [ ] CRM timeline shows all events for a lead
- [ ] Full demo flow (Acts 1–5) completable in 15 minutes

---

## POC Cost Estimate (Monthly)

Running locally with free tiers:

| Service | Free Tier | POC Usage | Cost |
|---|---|---|---|
| OpenAI (GPT-4o) | Pay as you go | ~200 emails × ~$0.01 | ~$2 |
| Apollo.io | 50 credits/month | 50 enrichments | $0 |
| Hunter.io | 25 lookups/month | 25 verifications | $0 |
| SendGrid | 100 emails/day | Demo sends | $0 |
| **Total** | | | **~$2–5/month** |

---

## Files Required for POC

```
scripts/
├── seed_demo_data.py            # Seeds 50 leads + 25 inventory items
├── demo_data/
│   ├── demo_leads.csv           # 50 synthetic leads for upload demo
│   └── demo_inventory.csv       # 25 synthetic inventory items
└── run_migrations.sh            # Alembic upgrade head wrapper
```

---

## Next Step After POC

Once POC is validated:
1. **Stakeholder demo** — walk through Acts 1–5 with Shivam Jewels team
2. **Feedback capture** — identify priority gaps (typically: more lead sources, better email quality)
3. **Phase 2 planning** — see [Plan.md](../Plan.md) for Phase 2 scope
4. **Infrastructure upgrade** — move from Docker Compose to production server (Phase 8)
