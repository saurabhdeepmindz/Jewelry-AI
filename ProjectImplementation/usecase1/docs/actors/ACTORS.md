# Actor Index — Jewelry AI Lead Automation Platform

**Version:** 1.0
**Status:** Approved
**Stage:** 1.2 — Discovery
**Created:** 2026-03-18
**Rules reference:** `rules/actor-roles-rules.md`
**Generic rules:** `best-practices_rule_set_code/docs/rules/actor-roles-rules.md`

---

## Actor Index

| Actor Label | Type | Authentication | Data Scope | Phase Available | Description |
|---|---|---|---|---|---|
| `admin` | Administrative | JWT (username/password) | Global — all records | Phase 0 | Full platform access; manages users, API keys, and system config |
| `manager` | Supervisory | JWT (username/password) | Global read | Phase 2 | Approves outreach, monitors pipeline, views all reports |
| `rep` | Primary Human | JWT (username/password) | Own — assigned leads only | Phase 1 | Uploads leads, triggers enrichment, views assigned pipeline |
| `system` | System Actor | Internal service token | Global | Phase 0 | Automated Celery workers, LangGraph pipeline, event handlers |
| `buyer` | External | OAuth / Magic Link (future) | Own — own inquiries only | Phase 3+ | Self-service portal (out of scope for v1) |

---

## Actor Definitions

### admin

**Type:** Administrative
**Phase:** Available from Phase 0

The system administrator has unrestricted access to the entire platform. They configure integrations, manage user accounts and roles, rotate API keys, and can override any lead status or system setting.

**Core responsibilities:**
- Create, assign roles to, and deactivate platform users
- Configure and rotate all external API keys (Apollo, Hunter, SendGrid, OpenAI, etc.)
- Monitor system health, pipeline stats, and audit logs
- Enable/disable feature flags (e.g., `HUMAN_REVIEW_REQUIRED`)

---

### manager

**Type:** Supervisory
**Phase:** Available from Phase 2

The sales manager oversees the lead pipeline, approves or rejects AI-generated outreach drafts, and tracks team and campaign performance.

**Core responsibilities:**
- Review AI-generated outreach drafts and approve or reject them before sending
- Monitor pipeline funnel: ingested → matched → enriched → outreach sent
- Reassign leads between reps
- Review outreach performance: open rates, reply rates, click rates

---

### rep

**Type:** Primary Human
**Phase:** Available from Phase 1

The sales representative is the daily operator. They upload trade lists, trigger enrichment for their assigned leads, and monitor the outreach queue.

**Core responsibilities:**
- Upload CSV trade directory files (GMTs, Jewelry Book of Trade, Hill Lists, Rapid Lists)
- Trigger contact enrichment for assigned eligible leads
- View outreach drafts queued for manager approval
- Log manual notes against their leads

---

### system

**Type:** System Actor
**Phase:** Available from Phase 0

Represents all automated background processes — no human interaction. Celery workers, LangGraph nodes, Celery Beat schedulers, and event-driven handlers all operate under this actor.

**Core responsibilities:**
- Run the full lead pipeline: match → enrich → score → draft outreach
- Execute Celery task queues (ingestion, enrichment, outreach, ml)
- Append CRM activity records on every lead state transition
- Retry failed API calls with exponential backoff

> **Important:** The `system` actor authenticates via an internal service token, never a JWT. Background tasks receive this token via Celery task context.

---

### buyer *(Phase 3+ — Out of Scope for v1)*

**Type:** External
**Phase:** Phase 3+ only

An external jewelry buyer who will eventually have access to a self-service portal to browse inventory and submit inquiries. **Do not implement any buyer-facing routes, auth flows, or permissions in Phase 0–2.**

---

## Role → Permission Summary

| Role | Key Permissions | Data Scope |
|---|---|---|
| `ROLE_ADMIN` | `leads:*`, `inventory:*`, `outreach:*`, `users:*`, `config:*`, `reports:read` | Global |
| `ROLE_MANAGER` | `leads:read`, `leads:assign`, `outreach:read`, `outreach:approve`, `reports:read` | Global read |
| `ROLE_REP` | `leads:read`, `leads:ingest`, `enrichment:trigger`, `outreach:read`, `crm:create` | Assigned only |
| `ROLE_SYSTEM` | `leads:create,update`, `contacts:create,update`, `outreach:create`, `crm:create`, `integrations:invoke` | Global |
| `ROLE_BUYER` *(Phase 3+)* | `inventory:read` (public), `inquiry:create`, `inquiry:read` | Own only |

---

## Data Scoping Rules

| Role | Leads | Contacts | Outreach Messages | CRM Log | Reports |
|---|---|---|---|---|---|
| `admin` | All | All | All | All (read) | Global |
| `manager` | All (read) | All | All (read + approve) | All (read) | Global |
| `rep` | Assigned only | Assigned only | Assigned only (read) | Own only | Own only |
| `system` | All | All | Create only | Append only | N/A |
| `buyer` | None | None | None | None | Own inquiries |

---

## Actor–Module Matrix

> Legend: ✅ Full access, 👁 Read-only, ✍ Create/trigger, 🔒 Approve only, ❌ No access

| Module | admin | manager | rep | system |
|---|---|---|---|---|
| Lead Master Data | ✅ | 👁 | 👁 (assigned) | ✍ |
| Inventory Catalog | ✅ | 👁 | 👁 | 👁 |
| Contact Data | ✅ | 👁 | 👁 (assigned) | ✍ |
| Outreach Messages | ✅ | 👁 + 🔒 | 👁 (assigned) | ✍ |
| CRM Activity Log | 👁 | 👁 | 👁 (own) | ✍ (append only) |
| User & Role Config | ✅ | ❌ | ❌ | ❌ |
| Lead Pipeline Workflow | ✍ | ❌ | ✍ (assigned) | ✍ |
| Enrichment Workflow | ✍ | ❌ | ✍ (assigned) | ✍ |
| Outreach Campaign Workflow | ✍ | ❌ | ❌ | ✍ |
| Streamlit Dashboard | 👁 | 👁 | 👁 | ❌ |
| Manager Review UI | 👁 + 🔒 | 👁 + 🔒 | ❌ | ❌ |
| Admin Panel | ✅ | ❌ | ❌ | ❌ |
| Pipeline Funnel Dashboard | 👁 (global) | 👁 (global) | 👁 (own) | ❌ |
| Outreach Performance Report | 👁 (global) | 👁 (global) | 👁 (own) | ❌ |
| Lead Scoring Distribution | 👁 (global) | 👁 (global) | 👁 (own) | ❌ |
| Audit Log Viewer | 👁 | ❌ | ❌ | ❌ |

---

## User Story Labels

Use these exact labels in all user stories in `agile/stories/`:

| User Story Label | Maps To Role | Example |
|---|---|---|
| `admin` | `ROLE_ADMIN` | "As an **admin**, I want to rotate the Apollo.io API key…" |
| `manager` | `ROLE_MANAGER` | "As a **manager**, I want to approve the outreach draft…" |
| `rep` | `ROLE_REP` | "As a **rep**, I want to upload a CSV of trade leads…" |
| `system` | `ROLE_SYSTEM` | "As the **system**, I want to enrich leads automatically…" |
| `buyer` | `ROLE_BUYER` | "As a **buyer**, I want to browse available diamonds…" *(Phase 3+ only)* |

---

## Key RBAC Business Rules

1. **Outreach approval gate:** `outreach:approve` is held exclusively by `manager` and `admin`. No `OutreachMessage` transitions from `pending_review` → `approved` without this permission.
2. **Rep data isolation:** All repository queries for `ROLE_REP` filter by `assigned_to = current_user.id` at the service layer — UI filtering alone is not sufficient.
3. **CRM immutability:** Only `ROLE_SYSTEM` may `crm:create`. No role — including `admin` — may update or delete `crm_activity` rows.
4. **Config write is admin-only:** Only `ROLE_ADMIN` writes to system configuration, including enabling/disabling `HUMAN_REVIEW_REQUIRED`.
5. **system actor has no JWT:** Background tasks authenticate via an internal service token in Celery task context.
6. **buyer is Phase 3+:** Do not implement buyer authentication, routes, or permissions before Phase 3. Gate any buyer feature behind a feature flag.

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-03-18 | Initial Actor Index — 5 actors, RBAC summary, permission matrix, data scoping |
