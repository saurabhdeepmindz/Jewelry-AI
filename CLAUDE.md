# Jewelry AI — Claude Code Project Guide

## Project Overview

AI-powered lead automation platform for Shivam Jewels. Automates the full lifecycle from raw trade lead lists to personalized, inventory-aware outreach — with zero manual intervention.

**Tech Stack (POC):** Streamlit | FastAPI | LangChain | LangGraph | PostgreSQL | Celery | Redis | n8n

---

## Documentation Index

All detailed documentation lives in [`ai-development-guidelines/`](ai-development-guidelines/).

### Start Here

| Document | Purpose | Link |
|---|---|---|
| **Ideas & Approach** | Solution concepts, tech stack rationale, POC scope | [ideas.md](ai-development-guidelines/ideas.md) |
| **PRD** | Epics, user stories, functional landscape | [PRD.md](ai-development-guidelines/PRD.md) |
| **Execution Plan** | Phase-by-phase SDLC plan with tasks | [Plan.md](ai-development-guidelines/Plan.md) |

### Architecture & Design

| Document | Purpose | Link |
|---|---|---|
| **Architecture** | Project structure, logging strategy, exception handling | [Architecture.md](ai-development-guidelines/Architecture.md) |
| **HLD** | System diagram, deployment diagram, integration flow | [HLD.md](ai-development-guidelines/HLD.md) |
| **LLD** | DB schema, API endpoints, domain models, agent nodes | [LLD.md](ai-development-guidelines/LLD.md) |
| **Design Patterns** | Repository, Strategy, Factory, LangGraph, etc. | [DesignPatterns.md](ai-development-guidelines/DesignPatterns.md) |

### Standards & Rules

| Document | Purpose | Link |
|---|---|---|
| **Rules (Master)** | All rules index with non-negotiables | [Rules.md](ai-development-guidelines/Rules.md) |
| **Coding Standards** | Class boilerplate, docstrings, naming, type hints | [CodingStandards.md](ai-development-guidelines/CodingStandards.md) |
| Coding Style Rules | Immutability, async, file size | [rules/coding-style-rules.md](ai-development-guidelines/rules/coding-style-rules.md) |
| Security Rules | Secrets, validation, auth, rate limiting | [rules/security-rules.md](ai-development-guidelines/rules/security-rules.md) |
| Testing Rules | TDD, 80% coverage, test organization | [rules/testing-rules.md](ai-development-guidelines/rules/testing-rules.md) |
| API Design Rules | REST conventions, response format, status codes | [rules/api-design-rules.md](ai-development-guidelines/rules/api-design-rules.md) |
| Data Rules | DB conventions, migrations, soft deletes | [rules/data-rules.md](ai-development-guidelines/rules/data-rules.md) |

---

## Current Phase

**Phase 0 — Foundation Setup** (see [Plan.md](ai-development-guidelines/Plan.md))

Next steps:
1. Initialize Python project with `pyproject.toml`
2. Set up Docker Compose (FastAPI + Streamlit + PostgreSQL + Redis)
3. Create Alembic migration setup
4. Scaffold folder structure per [Architecture.md](ai-development-guidelines/Architecture.md)

---

## Key Conventions (Quick Reference)

- **Python 3.11+**, fully typed, `async` for all I/O
- **No mutation** of domain objects — always return new copies
- **Repository Pattern** for all DB access
- **Pydantic** for all validation (domain models + API schemas)
- **LangGraph** for multi-step agent workflows
- **Celery** for all background/async tasks
- **TDD** — write tests before implementation
- **Structured JSON logging** with `trace_id` on every log entry
- **Secrets in `.env` only** — never committed

---

## Requirements Source

[Requirements/Requirements.txt](Requirements/Requirements.txt)
