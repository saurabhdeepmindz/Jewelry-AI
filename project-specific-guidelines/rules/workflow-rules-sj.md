# Workflow Rules — n8n, LangGraph, Celery

This file covers all three workflow layers in the Jewelry AI platform:
- **n8n** — External workflow automation (email sequences, WhatsApp, webhook triggers)
- **LangGraph** — Internal AI agent state machines (lead pipeline, follow-up logic)
- **Celery** — Background task queue (async jobs, scheduled scraping, bulk operations)

---

## Layer Responsibilities

| Layer | Purpose | Triggered By | Use When |
|---|---|---|---|
| **Celery** | Async background tasks, scheduled jobs | FastAPI endpoints, Celery Beat | CPU/IO work, bulk processing, scheduled scraping |
| **LangGraph** | AI-driven multi-step state machines | Celery tasks | Multi-step reasoning, conditional branching, LLM chains |
| **n8n** | External system orchestration, timed sequences | FastAPI webhooks, LangGraph nodes | Email sequences, delays, WhatsApp, CRM sync |

**Rule:** Never use n8n for business logic — only for external system orchestration.
**Rule:** Never use LangGraph for simple CRUD — only for AI reasoning workflows.
**Rule:** Never use Celery for LLM calls without LangGraph — LangGraph handles retries and state.

---

## Part 1 — n8n Workflow Rules

### Workflow Naming Convention

```
[Domain]_[Action]_[Trigger]
```

Examples:
- `Lead_OutreachSequence_Webhook`
- `Lead_FollowUp_Schedule`
- `Contact_WelcomeEmail_Event`

### Workflow Structure Rules

Every n8n workflow MUST have:
1. **Trigger node** — Webhook, Schedule, or Manual
2. **Input validation node** — Check required fields before processing
3. **Error handling branch** — Every path must handle failure explicitly
4. **Final status update node** — Call FastAPI to log outcome in CRM

```
[Webhook Trigger]
      │
[Validate Input]
      │
[Process Steps]
      │
  ┌───┴───────────┐
  │ Success       │ Failure
  │               │
[Log CRM: sent]  [Log CRM: failed]
[Set next step]  [Alert sales rep]
```

### Webhook Design

n8n webhooks called from FastAPI MUST:
- Include `trace_id` in the payload for correlation
- Use `POST` method only (no GET webhooks for data mutations)
- Authenticate via a shared `X-Webhook-Secret` header

```python
# src/integrations/n8n_client.py — calling n8n from FastAPI

async def trigger_outreach_sequence(self, lead_id: str, contact_email: str, trace_id: str) -> dict:
    """
    Trigger the n8n outreach email sequence for a qualified lead.

    Args:
        lead_id (str): UUID of the lead to start sequence for.
        contact_email (str): Verified email address to send to.
        trace_id (str): Request correlation ID for log tracing.

    Returns:
        dict: n8n execution ID for tracking.
    """
    payload = {
        "lead_id": lead_id,
        "contact_email": contact_email,
        "trace_id": trace_id,
        "triggered_at": datetime.utcnow().isoformat(),
    }
    return await self._post(settings.N8N_WEBHOOK_OUTREACH, payload)
```

### Credential Management

All credentials in n8n MUST use **n8n Credential Store** — never hardcoded in node parameters:

| Credential | n8n Credential Type |
|---|---|
| SendGrid | "SendGrid API" |
| Twilio (WhatsApp) | "Twilio API" |
| Jewelry AI FastAPI | "Header Auth" (X-Webhook-Secret) |

Never enter API keys directly in HTTP Request nodes — always reference credential by name.

### Email Sequence Workflow Design

The 3-step outreach sequence follows this pattern:

```
[Webhook: Lead Qualified]
         │
[Step 1: Send Email] ──► [Log CRM: email_sent step=1]
         │
[Wait: 5 days]
         │
[Check: Lead replied?] ──Yes──► [Log CRM: replied, STOP sequence]
         │ No
[Step 2: Follow-up Email] ──► [Log CRM: email_sent step=2]
         │
[Wait: 5 days]
         │
[Check: Lead replied?] ──Yes──► [Log CRM: replied, STOP sequence]
         │ No
[Step 3: Final Touchpoint] ──► [Log CRM: email_sent step=3]
         │
[Mark: Sequence Complete]
```

**Rule:** Always check lead reply status before sending the next step — never send step 2 if lead has already replied.

### Error Handling in n8n

Every n8n HTTP Request node MUST have an error output connected:

```
[HTTP Request: Send Email]
  ├── Success ──► [Log CRM: sent]
  └── Error   ──► [Log CRM: failed] ──► [Alert: Slack/Email to sales rep]
```

Use n8n's "Continue on Fail" sparingly — only for non-critical steps.

### n8n Workflow Export & Version Control

- Export all workflows as JSON via n8n CLI: `n8n export:workflow --all`
- Store exported JSON in `infra/n8n-workflows/` directory (committed to git)
- Use descriptive workflow names — never leave workflows named "My workflow 1"
- Tag workflows: `production`, `staging`, `dev` using n8n Tags

---

## Part 2 — LangGraph Workflow Rules

### When to Use LangGraph

Use LangGraph when a process requires:
- Conditional branching based on AI reasoning or data
- Multiple sequential LLM calls with shared state
- Retry/recovery logic with state persistence
- Human-in-the-loop approval gates

Do NOT use LangGraph for simple if/else logic — that belongs in the service layer.

### State Design (TypedDict)

Every workflow has exactly one typed state object. Fields are append-only across nodes.

```python
# src/agents/workflows/lead_pipeline.py

from typing import TypedDict, Annotated
import operator

class LeadPipelineState(TypedDict):
    # Input (set at entry point, never modified)
    lead_id: str

    # Set by match_inventory_node
    is_eligible: bool
    matched_inventory_ids: list[str]

    # Set by enrich_contact_node
    contact_enriched: bool
    enrichment_source: str | None

    # Set by score_lead_node
    lead_score: float | None

    # Set by generate_outreach_node
    message_id: str | None
    requires_review: bool

    # Error tracking
    failed_step: str | None
    error_message: str | None
    retry_count: int
```

### Node Design Rules

```python
# Each node:
# 1. Has a single responsibility
# 2. Receives full state, returns partial state dict
# 3. Logs entry and exit
# 4. Never raises — catches errors and stores in state

async def enrich_contact_node(state: LeadPipelineState) -> dict:
    """
    Node: Enrich lead with buyer contact details via Apollo.io.

    On success: sets contact_enriched=True, enrichment_source.
    On failure: sets contact_enriched=False, failed_step, error_message.
    Never raises — error stored in state for conditional routing.
    """
    logger.info("Enrichment node start", extra={"lead_id": state["lead_id"]})
    try:
        contact = await enrichment_service.enrich_lead(state["lead_id"])
        logger.info("Enrichment node complete", extra={"lead_id": state["lead_id"]})
        return {
            "contact_enriched": True,
            "enrichment_source": contact.enrichment_source,
        }
    except IntegrationException as exc:
        logger.warning("Enrichment failed", extra={"lead_id": state["lead_id"], "error": str(exc)})
        return {
            "contact_enriched": False,
            "failed_step": "enrich_contact",
            "error_message": str(exc),
        }
```

### Graph Construction Rules

```python
# Explicit entry point, explicit END, all edges documented
workflow = StateGraph(LeadPipelineState)

# Register all nodes
workflow.add_node("match_inventory", match_inventory_node)
workflow.add_node("enrich_contact", enrich_contact_node)
workflow.add_node("score_lead", score_lead_node)
workflow.add_node("generate_outreach", generate_outreach_node)
workflow.add_node("log_crm", log_crm_node)
workflow.add_node("mark_not_eligible", mark_not_eligible_node)
workflow.add_node("handle_error", handle_error_node)

# Entry point is always explicit
workflow.set_entry_point("match_inventory")

# Conditional edges use named router functions — not inline lambdas
workflow.add_conditional_edges("match_inventory", route_after_match)
workflow.add_conditional_edges("enrich_contact", route_after_enrichment)

# Terminal edges
workflow.add_edge("score_lead", "generate_outreach")
workflow.add_edge("generate_outreach", "log_crm")
workflow.add_edge("log_crm", END)
workflow.add_edge("mark_not_eligible", END)
workflow.add_edge("handle_error", END)

# Named router functions — not inline lambdas
def route_after_match(state: LeadPipelineState) -> str:
    """Route after inventory match: eligible leads proceed, others end."""
    if state.get("failed_step"):
        return "handle_error"
    return "enrich_contact" if state["is_eligible"] else "mark_not_eligible"

lead_pipeline = workflow.compile()
```

### Human-in-the-Loop Gate

```python
# Use LangGraph interrupt for human approval
from langgraph.checkpoint.memory import MemorySaver

# Compile with checkpointer for resumable workflows
memory = MemorySaver()
approvable_pipeline = workflow.compile(
    checkpointer=memory,
    interrupt_before=["generate_outreach"]  # Pause before sending
)

# Resume after human approval
thread_config = {"configurable": {"thread_id": lead_id}}
approved_pipeline.invoke(None, config=thread_config)  # Resume from checkpoint
```

---

## Part 3 — Celery Task Rules

### Task Registration and Naming

```python
# Task names use dot-notation: app.domain.action
@celery_app.task(name="jewelry_ai.enrichment.enrich_lead", bind=True, ...)
def enrich_lead_task(self, lead_id: str) -> dict:
    ...

# Queues map to domains — keeps workloads isolated
CELERY_TASK_ROUTES = {
    "jewelry_ai.ingestion.*": {"queue": "ingestion"},
    "jewelry_ai.enrichment.*": {"queue": "enrichment"},
    "jewelry_ai.outreach.*": {"queue": "outreach"},
    "jewelry_ai.ml.*": {"queue": "ml"},
}
```

### Scheduled Tasks (Celery Beat)

```python
# src/tasks/celery_app.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Scrape new leads nightly at 2am
    "nightly-lead-scrape": {
        "task": "jewelry_ai.ingestion.scrape_all_sources",
        "schedule": crontab(hour=2, minute=0),
    },
    # Re-score stale leads weekly
    "weekly-lead-rescore": {
        "task": "jewelry_ai.ml.rescore_all_leads",
        "schedule": crontab(day_of_week=1, hour=3),  # Monday 3am
    },
    # Send sequence step 2 for leads due today
    "daily-sequence-step-trigger": {
        "task": "jewelry_ai.outreach.trigger_due_sequence_steps",
        "schedule": crontab(hour=9, minute=0),  # 9am daily
    },
}
```

### Task Observability

Every Celery task MUST log:
- Task start: task ID, input parameters (no PII)
- Task completion: duration, result summary
- Task failure: exception type, retry count

```python
@celery_app.task(bind=True, name="jewelry_ai.enrichment.enrich_lead")
def enrich_lead_task(self, lead_id: str) -> dict:
    import time
    start = time.time()
    logger.info("Task started", extra={"task_id": self.request.id, "lead_id": lead_id})
    try:
        result = asyncio.run(_enrich_lead(lead_id))
        duration = time.time() - start
        logger.info(
            "Task completed",
            extra={"task_id": self.request.id, "lead_id": lead_id, "duration_ms": int(duration * 1000)}
        )
        return result
    except Exception as exc:
        logger.error(
            "Task failed",
            extra={"task_id": self.request.id, "lead_id": lead_id, "retry": self.request.retries, "error": str(exc)}
        )
        raise self.retry(exc=exc)
```

---

## Workflow Integration Map

```
FastAPI Endpoint (POST /enrichment/{lead_id})
          │
          ▼
Celery Task: enrich_lead_task (queue: enrichment)
          │
          ▼
LangGraph: enrichment_workflow
  ├── Node: validate_lead
  ├── Node: enrich_via_apollo  ──► Apollo.io API
  ├── Node: verify_email       ──► Hunter.io API
  ├── Node: score_lead         ──► ML Model
  ├── Node: generate_outreach  ──► LLM (OpenAI / Anthropic)
  │                [HUMAN REVIEW GATE if HUMAN_REVIEW_REQUIRED=true]
  └── Node: log_crm            ──► PostgreSQL
          │
          ▼ (if auto-send enabled)
n8n Webhook: Lead_OutreachSequence_Webhook
  ├── Step 1: Send Email       ──► SendGrid
  ├── Wait 5 days
  ├── Step 2: Follow-up
  └── Step 3: Final touchpoint
```

---

## Do Not

- Put business logic in n8n workflows — only orchestration and system calls
- Use n8n to query the database directly — only via FastAPI endpoints
- Create LangGraph nodes with more than one responsibility
- Use inline lambdas as LangGraph conditional edge routers — use named functions
- Run Celery tasks that depend on other task outputs using `chain` with `revoke` logic — use a parent LangGraph workflow instead
- Schedule Celery Beat tasks with intervals shorter than 5 minutes without rate-limit guards
- Use n8n's built-in data storage for lead data — always persist via FastAPI
