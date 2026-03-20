# Execution Plan — Jewelry AI Platform SDLC

## Methodology

**Incremental, Phase-gated delivery** using agile sprints (2-week sprints).
Each phase has a working, demonstrable deliverable before proceeding.
AI-assisted development using Claude Code with TDD workflow throughout.

---

## Phase 0 — Foundation Setup (Week 1–2)

### Goals
- Working dev environment
- Project skeleton with all boilerplate
- CI/CD baseline

### Tasks
- [ ] Initialize Python project with `pyproject.toml` (ruff, mypy, pytest, isort)
- [ ] Set up Docker Compose: FastAPI, Streamlit, PostgreSQL, Redis
- [ ] Create Alembic migration setup and baseline migration
- [ ] Configure `.env.example` with all required variables
- [ ] Set up `pre-commit` hooks (ruff, mypy, pytest)
- [ ] Create project folder structure per `Architecture.md`
- [ ] Write `Makefile` with common dev commands
- [ ] Set up MLflow locally
- [ ] Set up n8n locally

### Deliverable
Running `docker-compose up` starts all services with no errors. FastAPI health endpoint returns 200.

---

## Phase 1 — Lead Ingestion & Inventory (Week 3–4)

### Goals
POC of core data pipeline: upload leads, match to inventory, view results.

### Tasks
- [ ] `src/domain/lead.py` — Lead Pydantic model with validators
- [ ] `src/domain/inventory.py` — Inventory Pydantic model
- [ ] `src/db/` — SQLAlchemy models for `leads`, `inventory`, `lead_inventory_matches`
- [ ] `src/repositories/lead_repository.py` — CRUD for leads
- [ ] `src/repositories/inventory_repository.py` — CRUD for inventory
- [ ] `src/services/lead_ingestion_service.py` — Validate, deduplicate, persist
- [ ] `src/services/inventory_match_service.py` — Rule-based matching engine
- [ ] `src/api/routers/leads.py` — Upload, list, detail endpoints
- [ ] `src/api/routers/inventory.py` — Upload, list, match-rules endpoints
- [ ] `src/ui/pages/leads.py` — Streamlit: upload form + leads table
- [ ] `src/ui/pages/inventory.py` — Streamlit: inventory view + match status

### TDD Requirement
- Unit tests for all service methods (80%+ coverage)
- Integration tests for all API endpoints

### Deliverable
Upload a CSV of leads → see them matched against inventory → Eligible/Not Eligible flags visible in Streamlit UI.

---

## Phase 2 — Contact Enrichment (Week 5–6)

### Goals
Automatically find buyer contact details for eligible leads.

### Tasks
- [ ] `src/domain/contact.py` — Contact model
- [ ] `src/integrations/apollo_client.py` — Apollo.io adapter
- [ ] `src/integrations/hunter_client.py` — Hunter.io adapter
- [ ] `src/agents/enrichment_agent.py` — LangChain tool-use agent
- [ ] `src/services/enrichment_service.py` — Strategy pattern with Apollo/Hunter
- [ ] `src/tasks/enrichment_tasks.py` — Celery async enrichment task
- [ ] `src/api/routers/enrichment.py` — Trigger enrichment endpoint
- [ ] `src/ui/pages/leads.py` — Show enriched contact details

### Deliverable
Click "Enrich" on an eligible lead → contact name, email, phone populated automatically.

---

## Phase 3 — Outreach Generation & Sending (Week 7–8)

### Goals
LLM-generated personalized emails sent to enriched leads.

### Tasks
- [ ] `src/domain/outreach.py` — OutreachMessage model
- [ ] `src/integrations/sendgrid_client.py` — SendGrid adapter
- [ ] `src/agents/outreach_agent.py` — LangChain LLM chain for email generation
- [ ] `src/services/outreach_service.py` — Generate + send + log
- [ ] `src/tasks/outreach_tasks.py` — Celery outreach sequence task
- [ ] `src/api/routers/outreach.py` — Generate, review, send endpoints
- [ ] `src/ui/pages/outreach.py` — Draft review + send UI
- [ ] SendGrid webhook handler for opens/clicks/replies

### Deliverable
Full flow: eligible lead → enriched → AI-drafted email reviewed → sent → opens tracked in dashboard.

---

## Phase 4 — LangGraph Workflow Automation (Week 9–10)

### Goals
Full end-to-end pipeline orchestrated by LangGraph state machine.

### Tasks
- [ ] `src/agents/workflows/lead_pipeline.py` — Full LangGraph pipeline
- [ ] `src/agents/workflows/follow_up_workflow.py` — Follow-up state machine
- [ ] `src/core/events.py` — Event bus implementation
- [ ] Wire event bus: LeadIngested → trigger pipeline automatically
- [ ] `src/integrations/n8n_client.py` — Trigger n8n workflows for sequences
- [ ] n8n workflow: 3-step email sequence with delays
- [ ] CRM auto-logging via event handlers

### Deliverable
Upload CSV → zero clicks → leads matched, enriched, email drafted, queued for review automatically.

---

## Phase 5 — Lead Scoring ML Model (Week 11–12)

### Goals
ML-based lead scoring to prioritize high-value prospects.

### Tasks
- [ ] `src/ml/lead_scorer.py` — XGBoost scoring model
- [ ] `src/ml/fine_tuning/prepare_dataset.py` — Feature engineering pipeline
- [ ] Seed dataset with synthetic/historical CRM data
- [ ] Train baseline model, log to MLflow
- [ ] Integrate scoring into lead pipeline (post-enrichment)
- [ ] `src/ui/pages/analytics.py` — Lead scoring distribution chart

### Deliverable
Each enriched lead has a 0–100 score visible in the UI. Leads sorted by score in the outreach queue.

---

## Phase 6 — Analytics Dashboard & Polish (Week 13–14)

### Goals
Full analytics visibility + production-readiness for POC demo.

### Tasks
- [ ] Pipeline funnel chart (Streamlit + Plotly)
- [ ] Outreach performance metrics (open/reply/click rates)
- [ ] Lead source quality comparison
- [ ] End-to-end integration tests (pytest + httpx)
- [ ] Performance testing: 100-lead batch under 5 minutes
- [ ] Security review: secrets audit, input validation check
- [ ] Documentation: API docs, README, deployment guide

### Deliverable
Complete, demo-ready POC showing full pipeline with analytics.

---

## Phase 7 — Fine-Tuned Jewelry LLM (Week 15–18)

### Goals
Jewelry-domain fine-tuned model for superior outreach quality.

### Tasks
- [ ] Curate fine-tuning dataset: jewelry trade emails, catalog descriptions, buyer responses
- [ ] Prepare JSONL training data (system/user/assistant format)
- [ ] Fine-tune via OpenAI Fine-tune API or Unsloth (local)
- [ ] Evaluate: BLEU score + human evaluation on 50 samples
- [ ] A/B test: base GPT-4o vs fine-tuned model
- [ ] Deploy fine-tuned model to outreach agent

---

## Phase 8 — Live Scraping & Production Hardening (Week 19–22)

### Goals
Remove manual file upload dependency; full scraping automation.

### Tasks
- [ ] `src/scrapers/gmt_scraper.py` — GMT scraper with Scrapy/BeautifulSoup
- [ ] `src/scrapers/trade_book_scraper.py`
- [ ] Celery Beat: scheduled scraping every 24 hours
- [ ] Anti-bot evasion: rotating user agents, delays
- [ ] Alert system: email/Slack on pipeline failures
- [ ] WhatsApp outreach via Twilio (n8n workflow)
- [ ] Production Docker hardening (non-root user, health checks)

---

## SDLC Standards Applied Throughout

| Practice | Tool / Approach |
|---|---|
| Version Control | Git with conventional commits |
| Branching | Feature branches, squash merges to main |
| Code Review | PR required before merge (self-review for solo dev) |
| Testing | TDD: tests written before implementation |
| Coverage | Minimum 80%, enforced by pytest-cov in CI |
| Static Analysis | ruff (lint + format), mypy (types) |
| Dependency Management | `pyproject.toml` + pip-tools |
| Secrets | `.env` only, never committed; `.env.example` maintained |
| Documentation | Docstrings on all public methods |
| AI Assistance | Claude Code for code generation, review, and planning |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Apollo.io credit exhaustion | Medium | High | Cache all enrichment results; rate limit carefully |
| LLM cost overrun | Medium | Medium | Token budgets per lead; use Haiku for classification |
| Scraper blocks by trade sites | High | Medium | Respect robots.txt; add delays; use proxies if needed |
| PostgreSQL data loss | Low | High | Daily backup to local file; pgdump cron |
| Fine-tuning overfitting | Medium | Medium | Validation set 20%; early stopping in MLflow |
