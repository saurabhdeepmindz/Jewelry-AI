# Actor Index — Jewelry AI Platform

> **Rules reference:** `project-specific-guidelines/rules/actor-roles-rules.md`
> Generic rules: `best-practices_rule_set_code/docs/rules/actor-roles-rules.md`
> **Updated:** 2026-03-18

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

## Role → Permission Summary

| Role | Key Permissions | Data Scope |
|---|---|---|
| `ROLE_ADMIN` | `leads:*`, `inventory:*`, `outreach:*`, `users:*`, `config:*`, `reports:read` | Global |
| `ROLE_MANAGER` | `leads:read`, `leads:assign`, `outreach:read`, `outreach:approve`, `reports:read` | Global read |
| `ROLE_REP` | `leads:read`, `leads:ingest`, `enrichment:trigger`, `outreach:read`, `crm:create` | Assigned only |
| `ROLE_SYSTEM` | `leads:create,update`, `contacts:create,update`, `outreach:create`, `crm:create`, `integrations:invoke` | Global |
| `ROLE_BUYER` (Phase 3+) | `inventory:read` (public catalogue), `inquiry:create`, `inquiry:read` | Own only |

---

## Actor–Module Matrix (Summary)

> Full matrix in `project-specific-guidelines/rules/functional-landscape-rules.md`
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

## User Story Actor Labels

Use these exact labels in all user stories:

| User Story Label | Maps To Role | Example |
|---|---|---|
| `admin` | `ROLE_ADMIN` | "As an **admin**, I want to rotate the Apollo.io API key…" |
| `manager` | `ROLE_MANAGER` | "As a **manager**, I want to approve the outreach draft…" |
| `rep` | `ROLE_REP` | "As a **rep**, I want to upload a CSV of trade leads…" |
| `system` | `ROLE_SYSTEM` | "As the **system**, I want to enrich leads automatically…" |
| `buyer` | `ROLE_BUYER` | "As a **buyer**, I want to browse available diamonds…" (Phase 3+) |

---

## Key RBAC Business Rules

1. **Outreach approval gate:** `outreach:approve` is held exclusively by `manager` and `admin`. No `OutreachMessage` status transitions from `pending_review` to `approved` without this permission.
2. **Rep data isolation:** All repository queries for `ROLE_REP` are filtered by `assigned_to = current_user.id` at the service layer — not just the UI.
3. **CRM immutability:** Only `ROLE_SYSTEM` can `crm:create`. No role may update or delete CRM activity rows.
4. **Config write:** Only `ROLE_ADMIN` may write to system configuration — including enabling/disabling `HUMAN_REVIEW_REQUIRED`.
5. **`buyer` is Phase 3+:** Do not implement buyer authentication, routes, or permissions in Phase 0–2. Any feature referencing `buyer` must be gated behind a feature flag.
