# Actor & Roles Rules — Usecase 1: Jewelry AI Lead Automation

> **Extends:** `best-practices_rule_set_code/docs/rules/actor-roles-rules.md` (generic rules)
> **Purpose:** Defines all actors, roles, permissions, and data scoping for the Jewelry AI Lead Automation Platform.
> **Artifact to produce:** `docs/actors/ACTORS.md`

---

## Platform Actors

### Actor: admin

**Type:** Administrative
**Authentication:** Authenticated — username/password + JWT
**User Story Label:** `admin`
**Scope:** Full platform — all layers, all modules, all data

**Description:**
The system administrator manages platform configuration, user accounts, API key storage, and monitors overall system health. Has unrestricted access to all data and configuration.

**Responsibilities:**
- Create and manage user accounts and role assignments
- Configure and rotate integration API keys (Apollo, Hunter, SendGrid, etc.)
- Monitor pipeline health and audit logs
- Override any system setting or lead status

**Key Permissions:**

| Capability | Access Level | Notes |
|---|---|---|
| User Management | Full CRUD | Can create, assign roles, deactivate |
| API Key Management | Full CRUD | Stored encrypted; never exposed in UI |
| Lead Data | Full CRUD | Can view and edit all leads regardless of assignment |
| Inventory | Full CRUD | Can add, update, deactivate inventory items |
| Outreach Messages | Full CRUD + Approve | Can approve without manager review |
| CRM Activity Log | Read | Append-only — cannot delete |
| System Config | Full CRUD | Feature flags, HUMAN_REVIEW_REQUIRED, etc. |
| All Reports | Read | Global scope — all data |

**Data Scope:** Global — sees all records across all reps and managers.

---

### Actor: manager

**Type:** Supervisory
**Authentication:** Authenticated — username/password + JWT
**User Story Label:** `manager`
**Scope:** Lead management, outreach approval, pipeline reporting

**Description:**
The sales manager oversees the lead pipeline, reviews and approves AI-generated outreach messages before they are sent, and monitors team performance via the analytics dashboard.

**Responsibilities:**
- Review and approve or reject AI-generated outreach drafts
- Monitor pipeline funnel and outreach performance metrics
- Assign leads to sales representatives

**Key Permissions:**

| Capability | Access Level | Notes |
|---|---|---|
| Lead Data | Read | All leads; cannot create or delete |
| Outreach Messages | Read + Approve | Can approve/reject pending drafts |
| Contact Data | Read | All enriched contacts |
| CRM Activity Log | Read | All entries — global scope |
| Lead Assignment | Update | Can reassign leads to reps |
| All Reports & Dashboards | Read | Global scope |
| User Management | None | Admin-only |
| API Key Management | None | Admin-only |

**Data Scope:** Global read — sees all leads, contacts, outreach, and activity.

---

### Actor: rep

**Type:** Primary Human
**Authentication:** Authenticated — username/password + JWT
**User Story Label:** `rep`
**Scope:** Assigned leads — ingestion, enrichment trigger, outreach queue view

**Description:**
The sales representative works their assigned leads daily — uploading trade lists, triggering enrichment, and monitoring the outreach queue for their accounts.

**Responsibilities:**
- Upload CSV trade files to ingest new leads
- Trigger enrichment for eligible assigned leads
- View outreach drafts waiting for manager approval
- Log manual CRM notes against their leads

**Key Permissions:**

| Capability | Access Level | Notes |
|---|---|---|
| Lead Data | Read + Trigger | Assigned leads only; cannot delete |
| Lead Ingestion | Create | Can upload CSV; system assigns to them |
| Enrichment | Trigger | Assigned leads only |
| Outreach Messages | Read | Assigned leads only; cannot approve |
| Contact Data | Read | Assigned leads only |
| CRM Manual Notes | Create | Own leads only |
| Reports | Read | Own data only (own leads, own campaigns) |
| Inventory | Read | View only — cannot modify |

**Data Scope:** Own scope — sees only leads assigned to them and their own outreach activity.

---

### Actor: system

**Type:** System Actor
**Authentication:** Internal service token (not user-facing — no JWT)
**User Story Label:** `system`
**Scope:** All automated background processes and Celery tasks

**Description:**
Represents all automated processes that run without direct human initiation — Celery workers, LangGraph pipeline nodes, Celery Beat scheduled tasks, and event-driven handlers.

**Responsibilities:**
- Execute lead pipeline stages (match → enrich → score → queue for outreach)
- Process Celery task queues (ingestion, enrichment, outreach, ml)
- Fire CRM activity events on all state transitions
- Retry failed enrichment attempts with exponential backoff

**Key Permissions:**

| Capability | Access Level | Notes |
|---|---|---|
| Lead Data | Create, Update | Cannot delete — soft deletes only via service calls |
| Contact Data | Create, Update | Via enrichment service |
| Outreach Messages | Create | Generates drafts; cannot approve/send directly |
| CRM Activity Log | Create | Append-only — never updates existing entries |
| Inventory | Read | For matching logic |
| Integration Clients | Invoke | Apollo, Hunter, SendGrid, etc. via service layer |

**Data Scope:** Global — system processes all records regardless of rep assignment.

---

### Actor: buyer

**Type:** External / Primary Human — **Phase 3+ only**
**Authentication:** OAuth or magic link (future)
**User Story Label:** `buyer`
**Scope:** Self-service portal — inventory browsing, inquiry submission

**Description:**
An external jewelry buyer who, in a future phase, will have access to a self-service portal to browse available inventory and submit inquiries. **Not in scope for Phase 0–2.**

**Key Permissions (Phase 3+):**

| Capability | Access Level | Notes |
|---|---|---|
| Inventory | Read | Public catalogue only |
| Inquiry Submission | Create | Own inquiries only |
| Own Inquiry Status | Read | Own records only |
| Any Internal Data | None | Strictly isolated from internal platform |

**Data Scope:** Own — sees only their own inquiries and public inventory.

> **Rule:** Do NOT implement buyer-facing routes, authentication, or permissions in Phase 0–2. Any feature referencing `buyer` must be gated behind a feature flag.

---

## Role Definitions

### ROLE_ADMIN
```
leads:*          — full CRUD on all lead records
inventory:*      — full CRUD on inventory
contacts:read    — all enriched contacts
outreach:*       — full CRUD + approve
crm:read         — all CRM activity (read-only)
users:*          — full user management
config:*         — all system configuration
reports:read     — global scope
```

### ROLE_MANAGER
```
leads:read              — all leads
leads:assign            — reassign to reps
contacts:read           — all contacts
outreach:read           — all outreach
outreach:approve        — approve/reject pending drafts
crm:read                — all CRM activity
reports:read            — global scope
```

### ROLE_REP
```
leads:read              — assigned leads only
leads:ingest            — upload CSV
enrichment:trigger      — assigned leads only
outreach:read           — assigned leads only
contacts:read           — assigned leads only
crm:create              — own manual notes only
reports:read            — own data only
inventory:read          — view only
```

### ROLE_SYSTEM
```
leads:create,update     — pipeline automation
contacts:create,update  — enrichment
outreach:create         — draft generation only (no approve/send)
crm:create              — event-driven logging only
inventory:read          — matching logic
integrations:invoke     — all Layer 2 clients
```

---

## Data Scoping Rules

| Role | Leads | Contacts | Outreach | CRM Log | Reports |
|---|---|---|---|---|---|
| `admin` | All | All | All | All (read) | Global |
| `manager` | All (read) | All | All (read + approve) | All (read) | Global |
| `rep` | Assigned only | Assigned only | Assigned only (read) | Own only | Own only |
| `system` | All | All | Create only | Append only | N/A |
| `buyer` | None | None | None | None | Own inquiries |

---

## RBAC Business Rules

1. **Outreach approval is a hard gate:** No `OutreachMessage` may be sent unless explicitly approved by `manager` or `admin` — when `HUMAN_REVIEW_REQUIRED=true` (default).
2. **Rep scope enforced at API layer:** Reps are filtered by `assigned_to = current_user_id` in all repository queries — UI visibility alone is not sufficient.
3. **CRM log is write-once:** Only `ROLE_SYSTEM` can `crm:create`. No role — including `admin` — may update or delete CRM activity rows.
4. **Config write is admin-only:** Only `ROLE_ADMIN` may write to system configuration — including enabling/disabling `HUMAN_REVIEW_REQUIRED`.
5. **system actor has no JWT:** Background tasks authenticate via an internal service token passed through Celery task context, not a user JWT.
6. **buyer is Phase 3+:** Do not implement buyer authentication, routes, or permissions in Phase 0–2.
