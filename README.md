# Jewelry AI — Lead Automation Platform

**Purpose:** AI-powered lead automation platform for Shivam Jewels — transforms raw trade directory CSVs into enriched, scored, and AI-outreached buyer relationships with zero manual intervention.

**Stack:** Python 3.11+, FastAPI, LangChain, LangGraph, PostgreSQL + pgvector, Redis, Celery, n8n, Streamlit

---

## Repository Layout

```
Jewelry-AI/
├── ProjectImplementation/
│   └── usecase1/                  ← Main application (FastAPI + Celery + Streamlit)
│       ├── src/                   ← Source code
│       ├── tests/                 ← Unit + integration tests
│       ├── alembic/               ← Database migrations
│       ├── docker-compose.yml     ← Local 8-service stack
│       └── README.md              ← Full setup and usage guide
│
├── best-practices_rule_set_code/  ← Generic & stack-specific engineering standards
│   ├── SKILLS-generic.md          ← Reusable workflow playbooks
│   ├── skills/SKILLS-python.md    ← Python/FastAPI workflow playbooks
│   └── docs/rules/                ← 23 rule files (-generic, -python, -nestjs)
│
├── project-specific-guidelines/   ← Jewelry AI specific decisions and overrides
│   ├── GUIDELINES_COMPLIANCE-sj.md ← Rules compliance tracker
│   ├── SKILLS-sj.md               ← SJ workflow playbooks
│   └── rules/ docs/               ← Project-specific rules and specs
│
├── archive/                       ← Read-only reference (do not edit)
│   └── ai-development-guidelines/ ← Superseded folder, kept for reference
│
└── CLAUDE.md                      ← Claude Code project guide (read first)
```

---

## Getting Started

All setup instructions, prerequisites, API usage, and troubleshooting are in:

**[ProjectImplementation/usecase1/README.md](ProjectImplementation/usecase1/README.md)**

---

## Windows Quick Reference

```powershell
# 1. Enter the usecase directory
cd ProjectImplementation\usecase1

# 2. Copy env template and fill in API keys
copy .env.example .env

# 3. Start all services
docker compose up --build -d

# 4. Run migrations
docker compose exec fastapi alembic upgrade head

# 5. Verify
curl.exe http://localhost:8000/health

# 6. Open Swagger UI
Start-Process http://localhost:8000/docs
```

> For full setup details including virtual environment, tests, and troubleshooting see [usecase1/README.md](ProjectImplementation/usecase1/README.md).

---

## Current Increment Status

| Increment | Feature | Status |
|---|---|---|
| 0 | Foundation — skeleton, config, health, CI | ✅ Complete |
| 1 | Lead ingestion — CSV upload, dedup, Celery, polling | ✅ Complete |
| 2 | Contact enrichment — Apollo, Hunter, cache | ✅ Complete |
| 3 | Streamlit UI — WF-007 upload, WF-003 lead detail | ✅ Complete |
| 4 | Inventory matching | ⬜ Next |
| 5 | AI outreach generation | ⬜ |
| 6 | Human review queue | ⬜ |
| 7 | Analytics & reporting | ⬜ |
