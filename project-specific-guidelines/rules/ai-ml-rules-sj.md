# AI / ML Rules — LangChain, LangGraph, LLM, Celery, MLflow

## LLM Provider Rules

### Model Selection

Always choose the cheapest model that meets the quality requirement:

| Task | Model | Rationale |
|---|---|---|
| Lead classification, eligibility flag | `gpt-4o-mini` / `claude-haiku-4-5` | Simple classification — use cheapest |
| Outreach email generation | `gpt-4o` / `claude-sonnet-4-6` | Quality matters — use capable model |
| Fine-tuned jewelry model | `ft:gpt-4o-mini:org:jewelry-v1` | Domain-specific — use fine-tuned |
| Agent reasoning (enrichment, scoring) | `claude-sonnet-4-6` | Complex multi-step reasoning |
| Complex architectural decisions | `claude-opus-4-6` | Reserved for max reasoning tasks |

Never use Opus for routine generation tasks. Cost scales 10–20x vs Sonnet.

### Token Budget Rules

```python
# src/agents/outreach_agent.py

# CORRECT: explicit token caps per task
OUTREACH_MAX_TOKENS = 800       # Email body — never more
CLASSIFICATION_MAX_TOKENS = 100  # Yes/No classification — tight cap
ENRICHMENT_MAX_TOKENS = 400      # Reasoning over enrichment data

# WRONG: uncapped tokens — cost will balloon
response = await client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    # max_tokens not set — dangerous
)
```

### LLM Client Usage

Never instantiate LLM clients directly in services or routers. Always use LangChain wrappers:

```python
# CORRECT: LangChain-wrapped client, injected via DI
from langchain_openai import ChatOpenAI

def get_outreach_llm() -> ChatOpenAI:
    """Provide configured LLM for outreach generation tasks."""
    return ChatOpenAI(
        model="gpt-4o",
        max_tokens=OUTREACH_MAX_TOKENS,
        temperature=0.7,
        api_key=settings.OPENAI_API_KEY,
    )

# WRONG: raw OpenAI client in service code
import openai
client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
```

---

## LangChain Rules

### Chain Composition

All LangChain chains MUST be composed from small, independently testable steps:

```python
# src/agents/outreach_agent.py

from langchain_core.runnables import RunnableLambda
from langchain_core.prompts import ChatPromptTemplate

# Each step is a named, testable unit
prepare_context_step = RunnableLambda(prepare_lead_context)
build_prompt_step = ChatPromptTemplate.from_messages([
    ("system", OUTREACH_SYSTEM_PROMPT),
    ("human", OUTREACH_USER_PROMPT),
])
generate_step = get_outreach_llm()
parse_output_step = RunnableLambda(parse_email_output)

# Composed pipeline — readable, debuggable
outreach_chain = (
    prepare_context_step
    | build_prompt_step
    | generate_step
    | parse_output_step
)
```

### Prompt Management Rules

- All system prompts are constants defined at module level — never inline in chain calls
- Prompts include explicit jewelry domain context (4Cs, GIA grading, trade vocabulary)
- Prompts specify output format explicitly (JSON schema or structured text)
- Version prompts: when changing a prompt, log the change in git commit message

```python
# CORRECT: named constant, version-tracked in git
OUTREACH_SYSTEM_PROMPT = """
You are a senior sales executive at Shivam Jewels, a premium diamond wholesaler.
Write personalized, professional outreach emails to jewelry buyers.
Tone: warm, authoritative, concise. Maximum 150 words.
Reference specific diamonds from inventory. End with a clear call to action.
Output format: JSON with keys 'subject' and 'body'.
"""

# WRONG: inline prompt — not trackable
chain = prompt_template | llm  # where prompt_template has inline text
```

### Fallback Chains

All LLM chains in production MUST have a fallback:

```python
from langchain_anthropic import ChatAnthropic

primary_llm = ChatOpenAI(model="gpt-4o", ...)
fallback_llm = ChatAnthropic(model="claude-sonnet-4-6", ...)

# Automatic fallback if primary provider fails
outreach_llm = primary_llm.with_fallbacks([fallback_llm])
```

---

## LangGraph Rules

### State Design

Every LangGraph workflow MUST use a typed `TypedDict` state:

```python
# CORRECT: fully typed state
from typing import TypedDict

class LeadPipelineState(TypedDict):
    lead_id: str
    is_eligible: bool
    contact_enriched: bool
    enrichment_source: str | None
    outreach_sent: bool
    message_id: str | None
    error: str | None
    retry_count: int

# WRONG: untyped dict state — makes debugging impossible
state = {"lead_id": "...", "status": "..."}
```

### Node Responsibility

Each LangGraph node MUST have exactly one responsibility:

```python
# CORRECT: single-responsibility nodes
async def match_inventory_node(state: LeadPipelineState) -> LeadPipelineState:
    """Match lead against inventory. Updates is_eligible only."""
    ...

async def enrich_contact_node(state: LeadPipelineState) -> LeadPipelineState:
    """Enrich contact data. Updates contact_enriched only."""
    ...

# WRONG: node doing too much
async def process_lead_node(state):
    # match + enrich + score + generate outreach all in one — untestable
    ...
```

### Error Nodes

Every workflow MUST define explicit error handling nodes:

```python
workflow.add_node("handle_enrichment_error", handle_enrichment_error_node)
workflow.add_conditional_edges(
    "enrich_contact",
    lambda s: "send_outreach" if s["contact_enriched"] else "handle_enrichment_error"
)
```

### State Immutability in Nodes

Never mutate the input state. Always return a new dict with spread:

```python
# CORRECT: return new state dict
async def match_inventory_node(state: LeadPipelineState) -> LeadPipelineState:
    result = await inventory_match_service.match(state["lead_id"])
    return {**state, "is_eligible": result.is_eligible}

# WRONG: mutating state dict
async def match_inventory_node(state: LeadPipelineState) -> LeadPipelineState:
    state["is_eligible"] = True  # mutation — forbidden
    return state
```

---

## Celery Task Rules

### Task Design

```python
# CORRECT: idempotent, bounded, with retry logic
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,      # 60 seconds between retries
    queue="enrichment",
    acks_late=True,               # Only ack after successful completion
    reject_on_worker_lost=True    # Re-queue if worker dies mid-task
)
def enrich_lead_task(self, lead_id: str) -> dict:
    """
    Enrichment task. Idempotent — safe to retry.
    Check if already enriched before calling API to avoid duplicate charges.
    """
    ...
```

### Task Queues

Use separate queues to isolate workload priorities:

| Queue | Tasks | Workers |
|---|---|---|
| `default` | General operations | 2 |
| `enrichment` | Apollo/Hunter API calls | 2 (rate-limited) |
| `outreach` | Email sending | 1 (rate-limited by SendGrid) |
| `ml` | Scoring, embedding generation | 1 |
| `ingestion` | File parsing, batch import | 1 |

### Idempotency

All Celery tasks MUST be idempotent — safe to retry without side effects:

```python
async def enrich_lead_task(self, lead_id: str) -> dict:
    # Check if already enriched — avoid duplicate API call + charge
    lead = await lead_repo.find_by_id(lead_id)
    if lead.status == LeadStatus.ENRICHED:
        logger.info("Lead already enriched, skipping", extra={"lead_id": lead_id})
        return {"status": "skipped", "lead_id": lead_id}
    # proceed with enrichment
    ...
```

### Never Block Event Loop in Tasks

Celery tasks run in a thread pool, not an async event loop. Use `asyncio.run()` to call async code:

```python
# CORRECT: bridge async code from sync Celery task
def enrich_lead_task(self, lead_id: str) -> dict:
    import asyncio
    return asyncio.run(_async_enrich_lead(lead_id))

async def _async_enrich_lead(lead_id: str) -> dict:
    ...  # async implementation

# WRONG: calling async functions without bridge
def enrich_lead_task(self, lead_id: str):
    await _async_enrich_lead(lead_id)  # SyntaxError in sync context
```

---

## ML Model Rules (Lead Scoring)

### MLflow Tracking

Every training run MUST log to MLflow:

```python
# src/ml/lead_scorer.py
import mlflow

with mlflow.start_run(run_name="lead_scorer_v1"):
    # Log all hyperparameters
    mlflow.log_params({
        "model_type": "XGBoostClassifier",
        "n_estimators": 300,
        "max_depth": 6,
        "learning_rate": 0.05,
        "train_size": len(X_train),
    })

    # Train model
    model.fit(X_train, y_train)

    # Log metrics
    mlflow.log_metrics({
        "auc_roc": roc_auc_score(y_val, model.predict_proba(X_val)[:, 1]),
        "precision": precision_score(y_val, model.predict(X_val)),
        "recall": recall_score(y_val, model.predict(X_val)),
    })

    # Log model artifact
    mlflow.sklearn.log_model(model, "lead_scorer")
```

### Model Deployment Gate

A model is ONLY deployed to production if:
- AUC-ROC ≥ 0.75 on validation set
- Precision ≥ 0.60 on positive class
- Evaluated on at least 200 samples

### Model Versioning

- Models are registered in MLflow Model Registry
- Each deployment references a specific MLflow run ID
- Current production model version stored in `inventory_match_rules` settings table
- Never load models from disk paths — always via MLflow model URI

---

## Fine-Tuning Rules

- Training data must be reviewed by a human before upload — no raw LLM outputs
- Dataset must include negative examples (bad outreach emails, wrong tone)
- Minimum dataset: 200 high-quality jewelry outreach examples
- Evaluation: compare fine-tuned model vs base on 50 held-out examples (human-graded)
- A/B test in production: route 20% of traffic to fine-tuned, 80% to base, measure reply rate
- Fine-tuned model ID stored in `settings` table — never hardcoded in source

---

## Do Not

- Call OpenAI/Anthropic APIs directly in service or repository code — always via LangChain
- Hardcode model names in service code — read from `settings`
- Log full LLM prompts or completions (may contain PII from lead data)
- Run LLM generation synchronously in FastAPI request-response cycle for large batches — use Celery
- Deploy an ML model without MLflow tracking and a coverage gate
- Use `temperature=0` for outreach generation — emails will be identical
- Disable LangGraph checkpointing in production — needed for resumable workflows
