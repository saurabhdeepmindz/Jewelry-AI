# Development Progress Tracker — Jewelry AI Platform

> **Updated:** 2026-03-20
> **Reference after every increment execution. Update status and commands immediately.**
> **Working directory for all commands:** `D:\SaurabhVerma\presales\Shivam-Jewels\Jewelry-AI\ProjectImplementation\usecase1\`

---

## How to Use This Document

1. Before starting an increment → read the **Next Steps** row for that phase
2. After completing an increment → mark ✅, fill in **Commit hash**, update **Last Updated**
3. If a command fails → note it in the **Issues / Notes** column
4. Always run commands from `ProjectImplementation/usecase1/` with venv activated

---

## Environment Startup (Run Every Session)

### Step 1 — Activate Virtual Environment (PowerShell)
```powershell
cd D:\SaurabhVerma\presales\Shivam-Jewels\Jewelry-AI\ProjectImplementation\usecase1
.\.venv\Scripts\Activate.ps1
```

### Step 2 — Start Docker Services
```powershell
docker compose up postgres redis celery -d
```
> Full stack (includes n8n, MLflow, Grafana):
> ```powershell
> docker compose up --build -d
> ```

### Step 3 — Start FastAPI (Terminal 1)
```powershell
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4 — Start Streamlit UI (Terminal 2 — separate window)
```powershell
streamlit run src/ui/app.py
```

### Verify Everything Is Running
```powershell
# FastAPI health check
curl http://localhost:8000/health

# Streamlit
# Open browser → http://localhost:8501
```

---

## API Keys & Integration Requirements

> Store all keys in `.env` file at `ProjectImplementation/usecase1/.env`
> Never commit `.env` — it is gitignored.

| Service | Key Variable | Status | How to Get |
|---|---|---|---|
| **OpenAI** | `OPENAI_API_KEY` | ⚠️ Required now | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| **Anthropic** | `ANTHROPIC_API_KEY` | Optional (fallback LLM) | [console.anthropic.com](https://console.anthropic.com) |
| **Apollo.io** | `APOLLO_API_KEY` | ⚠️ Required (Phase 2) | [app.apollo.io → Settings → Integrations → API](https://app.apollo.io) — Free tier: 50 credits/month |
| **Hunter.io** | `HUNTER_API_KEY` | ⚠️ Required (Phase 2) | [hunter.io → Dashboard → API](https://hunter.io/api-keys) — Free tier: 25 requests/month |
| **Proxycurl** | `PROXYCURL_API_KEY` | ⚠️ Required (Phase 2 completion) | [nubela.co/proxycurl → Dashboard → API Key](https://nubela.co/proxycurl) — Pay-per-call, ~$0.01/profile. Buy minimum credits to test. |
| **SendGrid** | `SENDGRID_API_KEY` + `SENDGRID_FROM_EMAIL` | Required (Phase 3) | [app.sendgrid.com → Settings → API Keys](https://app.sendgrid.com) — Free tier: 100 emails/day |
| **Twilio** | `TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN` + `TWILIO_WHATSAPP_FROM` | Phase 4+ only | [console.twilio.com](https://console.twilio.com) |
| **n8n** | `N8N_WEBHOOK_URL` | Phase 4+ only | Local Docker: `http://localhost:5678` |
| **MLflow** | `MLFLOW_TRACKING_URI` | Default set | Local Docker: `http://localhost:5000` |

### Minimum .env for Current Development (Phases 0–2)
```env
APP_ENV=development
SECRET_KEY=dev-secret-change-in-prod

DATABASE_URL=postgresql+asyncpg://jewelry_user:jewelry_pass@localhost:5432/jewelry_db
REDIS_URL=redis://localhost:6379/0

OPENAI_API_KEY=sk-...
APOLLO_API_KEY=...
HUNTER_API_KEY=...
PROXYCURL_API_KEY=...

SENDGRID_API_KEY=SG....
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
```

---

## Phase Progress

### Phase 0 — Foundation Setup ✅ COMPLETE
| Increment | Description | Status | Commit |
|---|---|---|---|
| 0.1 | Docker Compose, pyproject.toml, folder skeleton | ✅ | `69abba4` |
| 0.2 | Config, logging, exceptions, health endpoints, CI | ✅ | `69abba4` |

**Execution Commands Used:**
```powershell
docker compose up --build -d
curl http://localhost:8000/health
```

---

### Phase 1 — Lead Ingestion ✅ COMPLETE
| Increment | Description | Status | Commit |
|---|---|---|---|
| 1.1 | Domain model, DB model, migration | ✅ | `9338fdb` |
| 1.2 | LeadRepository, IngestionService, deduplication | ✅ | `9338fdb` |
| 1.3 | Celery ingestion task, job polling | ✅ | `9338fdb` |
| 1.4 | `/leads` API router (upload, list, detail, job poll) | ✅ | `9338fdb` |
| 1.5 | Streamlit WF-007 upload page (5-state machine) | ✅ | `842caec` |
| 1.6 | Unit + integration tests (80%+ coverage) | ✅ | `9338fdb` |

**Execution Commands Used:**
```powershell
# Run migrations
docker compose exec fastapi alembic upgrade head

# Test CSV upload (PowerShell)
$form = @{ file = Get-Item ".\sample_leads.csv" }
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/leads/upload" -Method Post -Form $form

# Poll job status
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/leads/jobs/{job_id}" -Method Get

# Run tests
docker compose exec fastapi pytest tests/ --cov=src --cov-report=term-missing
```

---

### Phase 2 — Contact Enrichment ✅ COMPLETE (partial gaps remain)
| Increment | Description | Status | Commit |
|---|---|---|---|
| 2.1 | Contact domain model + DB model + migration | ✅ | `0f64fc5` |
| 2.2 | ContactRepository | ✅ | `0f64fc5` |
| 2.3 | ApolloClient (httpx async) | ✅ | `0f64fc5` |
| 2.4 | HunterClient (httpx async, verify + find) | ✅ | `0f64fc5` |
| 2.5 | EnrichmentService (Apollo → Hunter fallback) | ✅ | `0f64fc5` |
| 2.6 | Celery enrichment task | ✅ | `0f64fc5` |
| 2.7 | `/enrichment` API router | ✅ | `0f64fc5` |
| 2.8 | Streamlit WF-003 lead detail page | ✅ | `842caec` |
| 2.9 | Unit + integration tests | ✅ | `0f64fc5` |
| **2.10** | **ProxycurlClient (LinkedIn enrichment)** | ✅ | pending push |
| **2.11** | **EnrichmentAgent (LangChain tool-use, Apollo+Hunter+Proxycurl)** | ✅ | pending push |

**Execution Commands Used:**
```powershell
# Trigger enrichment for a lead
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/enrichment/{lead_id}" -Method Post

# Poll enrichment job
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/enrichment/jobs/{job_id}" -Method Get
```

**Keys Required:**
- `PROXYCURL_API_KEY` — get from nubela.co/proxycurl (needed for 2.10)
- `OPENAI_API_KEY` — for LangChain agent tool orchestration (needed for 2.11)

---

### Phase 3 — Outreach Generation & Sending ✅ COMPLETE
| Increment | Description | Status | Commit |
|---|---|---|---|
| 3.1 | OutreachMessage domain model + DB model | ✅ | pending push |
| 3.2 | OutreachRepository | ✅ | pending push |
| 3.3 | SendGridClient (transactional email via SDK) | ✅ | pending push |
| 3.4 | OutreachAgent (LangChain gpt-4o-mini, jewelry prompt) | ✅ | pending push |
| 3.5 | OutreachService (generate + approve/send + reject + webhook) | ✅ | pending push |
| 3.6 | Celery outreach task (queue: outreach) | ✅ | pending push |
| 3.7 | `/api/v1/outreach` router (8 endpoints) | ✅ | pending push |
| 3.8 | Streamlit Outreach Review UI + app.py nav | ✅ | pending push |
| 3.9 | Unit tests: service (10 cases) + router (12 cases) | ✅ | pending push |
| 3.10 | OutreachMessageFactory (test fixtures) | ✅ | pending push |

**Execution Commands:**
```powershell
# After starting services, generate outreach for a lead
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/outreach/generate/{lead_id}" -Method Post

# Poll job status
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/outreach/jobs/{job_id}" -Method Get

# List pending review messages
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/outreach/messages?status=pending_review" -Method Get

# Approve and send
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/outreach/messages/{id}/approve" -Method Post

# Reject with reason
$body = '{"reason": "Tone too formal"}'
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/outreach/messages/{id}/reject" -Method Post -Body $body -ContentType "application/json"
```

**Keys Required:**
- `SENDGRID_API_KEY` + `SENDGRID_FROM_EMAIL` — verify sender domain in SendGrid dashboard
- `OPENAI_API_KEY` — for gpt-4o-mini email generation

---

### Phase 4 — LangGraph Workflow Automation ❌ NOT STARTED
| Increment | Description | Status | Commit |
|---|---|---|---|
| 4.1 | LeadPipeline LangGraph state machine (ingest→match→enrich→draft) | ⬜ | — |
| 4.2 | FollowUpWorkflow LangGraph state machine | ⬜ | — |
| 4.3 | Event bus wiring (LeadIngested → trigger pipeline) | ⬜ | — |
| 4.4 | n8n client + 3-step email sequence webhook | ⬜ | — |
| 4.5 | CRM auto-logging via event handlers | ⬜ | — |

**Keys Required:**
- n8n running locally: `http://localhost:5678` (already in Docker Compose)
- `N8N_WEBHOOK_URL` — set after creating workflow in n8n UI

---

### Phase 5 — Lead Scoring ML Model ❌ NOT STARTED
| Increment | Description | Status | Commit |
|---|---|---|---|
| 5.1 | XGBoost lead scorer + feature engineering | ⬜ | — |
| 5.2 | Synthetic training dataset + seed script | ⬜ | — |
| 5.3 | MLflow experiment tracking integration | ⬜ | — |
| 5.4 | Scoring integrated into enrichment pipeline | ⬜ | — |
| 5.5 | Analytics UI — score distribution chart | ⬜ | — |

---

### Phase 6 — Analytics Dashboard & Polish ❌ NOT STARTED
| Increment | Description | Status | Commit |
|---|---|---|---|
| 6.1 | Pipeline funnel chart (Plotly) | ⬜ | — |
| 6.2 | Outreach performance metrics | ⬜ | — |
| 6.3 | End-to-end integration tests | ⬜ | — |
| 6.4 | Security review + secrets audit | ⬜ | — |
| 6.5 | Performance test: 100-lead batch | ⬜ | — |

---

### Phase 7 — Fine-Tuned Jewelry LLM ❌ NOT STARTED
### Phase 8 — Live Scraping & Production Hardening ❌ NOT STARTED

---

## Common Utility Commands (Windows PowerShell)

### Database
```powershell
# Run all pending migrations
docker compose exec fastapi alembic upgrade head

# Create new migration
docker compose exec fastapi alembic revision --autogenerate -m "description_here"

# Check migration history
docker compose exec fastapi alembic history
```

### Testing
```powershell
# Full test suite with coverage
docker compose exec fastapi pytest tests/ --cov=src --cov-report=term-missing

# Unit tests only
docker compose exec fastapi pytest tests/unit/ -v

# Integration tests only
docker compose exec fastapi pytest tests/integration/ -v

# Single test file
docker compose exec fastapi pytest tests/unit/services/test_enrichment_service.py -v

# With local venv (outside Docker)
pytest tests/ --cov=src --cov-report=term-missing
```

### Linting & Type Checking
```powershell
# Lint (ruff)
docker compose exec fastapi ruff check src tests

# Format check
docker compose exec fastapi ruff format --check src tests

# Type check (mypy)
docker compose exec fastapi mypy src
```

### Celery
```powershell
# Start worker (local venv)
celery -A src.tasks.celery_app worker --loglevel=info -Q ingestion,enrichment,outreach,ml

# Check active tasks
celery -A src.tasks.celery_app inspect active
```

### Git
```powershell
# Status
git status

# Stage specific files
git add src/integrations/proxycurl_client.py src/agents/enrichment_agent.py

# Commit
git commit -m "feat(phase2): add Proxycurl client and LangChain enrichment agent"

# Push
git push origin master
```

### Docker
```powershell
# View logs
docker compose logs fastapi --tail=50 -f
docker compose logs celery --tail=50 -f

# Restart a service
docker compose restart fastapi

# Stop all
docker compose down

# Full rebuild
docker compose up --build -d
```

---

## Issues Log

| Date | Phase | Issue | Resolution |
|---|---|---|---|
| 2026-03-20 | Phase 0 | `docker compose up postgres redis celery_worker -d` fails | Service is named `celery` not `celery_worker` — use `docker compose up postgres redis celery -d` |

---

## Next Increment to Execute

**Phase 3 — Migration:** Run Alembic migration to create `outreach_messages` table
```powershell
docker compose exec fastapi alembic revision --autogenerate -m "add_outreach_messages_table"
docker compose exec fastapi alembic upgrade head
```

**Phase 4 — Increment 4.1:** LangGraph `LeadPipeline` state machine

Pre-requisites for Phase 4:
- All Phase 3 services running and tested end-to-end
- n8n webhook URL configured: `N8N_WEBHOOK_URL=http://localhost:5678/webhook/...`
