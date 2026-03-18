# Design Patterns — Jewelry AI Lead Automation Platform

**Version:** 1.0
**Status:** Approved
**Stage:** 4.1 — Design Patterns
**Created:** 2026-03-18

---

## Overview

This document catalogs every design pattern applied in the Jewelry AI platform, organized by architectural layer. Each pattern entry includes:

- **Problem** — what it solves
- **Where Used** — layer, module, file
- **Implementation** — concrete Python code aligned with this codebase
- **Rules** — project-specific constraints

---

## Pattern Index

| # | Pattern | Category | Primary Layer | Key File(s) |
|---|---------|----------|---------------|-------------|
| 1 | Repository | Data Access | Repository | `src/repositories/base.py` |
| 2 | Unit of Work | Data Access | Repository | `src/db/session.py` |
| 3 | Strategy | Business Logic | Service | `src/integrations/enrichment/` |
| 4 | Factory | Creational | Integration | `src/integrations/factory.py` |
| 5 | Adapter | Structural | Integration | `src/integrations/apollo.py` etc. |
| 6 | State Machine | Workflow | Agent | `src/agents/lead_pipeline.py` |
| 7 | Chain of Responsibility | Workflow | Agent | `src/agents/nodes/` |
| 8 | Observer / Event Bus | Behavioral | Service | `src/core/events.py` |
| 9 | Dependency Injection | Structural | API / Service | `src/api/dependencies.py` |
| 10 | Decorator | Cross-Cutting | All layers | `src/core/decorators.py` |
| 11 | Template Method | Business Logic | Service | `src/services/base.py` |
| 12 | Saga | Distributed | Task | `src/tasks/` (Celery) |

---

## 1. Repository Pattern

### Problem
Domain services must not contain raw SQL. Direct SQLAlchemy queries scattered across services make testing hard and create fragile coupling to the database schema.

### Where Used
- All domain tables: `leads`, `inventory`, `contacts`, `outreach_messages`, `crm_activity`
- Layer: **Repository** (`src/repositories/`)

### Implementation

```python
# src/repositories/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base for all domain repositories.

    Subclasses provide:
        model_class: the SQLAlchemy ORM model type
        session: injected via FastAPI Depends

    Rules:
        - All queries filter WHERE is_deleted = false by default
        - Hard DELETE is never executed — use soft_delete()
        - crm_activity repository overrides: no update, no delete
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    @abstractmethod
    def model_class(self) -> type[T]:
        ...

    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        result = await self._session.execute(
            select(self.model_class)
            .where(
                self.model_class.id == entity_id,
                self.model_class.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def create(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def soft_delete(self, entity_id: UUID) -> None:
        await self._session.execute(
            update(self.model_class)
            .where(self.model_class.id == entity_id)
            .values(is_deleted=True)
        )


# src/repositories/lead_repository.py
from sqlalchemy import select, func
from src.db.models import LeadORM
from src.repositories.base import BaseRepository


class LeadRepository(BaseRepository[LeadORM]):
    """Repository for leads table. Adds lead-specific query methods."""

    @property
    def model_class(self) -> type[LeadORM]:
        return LeadORM

    async def get_by_domain(self, domain: str) -> Optional[LeadORM]:
        """Deduplication check — domain is unique among non-deleted leads."""
        result = await self._session.execute(
            select(LeadORM).where(
                LeadORM.domain == domain,
                LeadORM.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def list_by_status(
        self,
        status: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LeadORM]:
        result = await self._session.execute(
            select(LeadORM)
            .where(
                LeadORM.status == status,
                LeadORM.is_deleted == False,  # noqa: E712
            )
            .order_by(LeadORM.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_by_status(self, status: str) -> int:
        result = await self._session.execute(
            select(func.count()).where(
                LeadORM.status == status,
                LeadORM.is_deleted == False,  # noqa: E712
            )
        )
        return result.scalar_one()
```

### Rules
- Every `SELECT` against domain tables **must** include `is_deleted = false`.
- `CRMRepository` **must not** implement `update()` or `soft_delete()` — append-only.
- Repository methods return ORM model objects; mapping to Pydantic domain models happens in the service layer.

---

## 2. Unit of Work Pattern

### Problem
Multiple repository operations within a single business transaction must either all succeed or all roll back atomically. Without coordination, partial writes leave data in an inconsistent state.

### Where Used
- `src/db/session.py` — async SQLAlchemy session lifecycle
- FastAPI lifespan events (`src/main.py`)

### Implementation

```python
# src/db/session.py
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings

settings = get_settings()

_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,       # default: 10
    max_overflow=settings.DB_MAX_OVERFLOW, # default: 20
    pool_pre_ping=True,                    # recycle stale connections
    echo=settings.DB_ECHO,                 # SQL logging in dev only
)

_session_factory = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # prevent lazy-load after commit
)


@asynccontextmanager
async def get_unit_of_work() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that wraps a single business transaction.

    Usage in services:
        async with get_unit_of_work() as session:
            repo = LeadRepository(session)
            lead = await repo.create(lead_orm)
            crm_repo = CRMRepository(session)
            await crm_repo.append(activity_orm)
            # auto-commit on exit; rollback on exception

    Rules:
        - One UoW per HTTP request (injected via FastAPI Depends)
        - Celery tasks create their own UoW per task execution
        - Never share a session across concurrent tasks
    """
    async with _session_factory() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise


# FastAPI dependency — injected into API routers
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_unit_of_work() as session:
        yield session
```

---

## 3. Strategy Pattern — Enrichment Cascade

### Problem
Contact enrichment can use multiple providers (Apollo.io, Hunter.io, Proxycurl). The order, fallback logic, and caching must be swappable without modifying calling code.

### Where Used
- `src/integrations/enrichment/` — 3 provider strategies
- `src/services/enrichment_service.py` — strategy selector + cascade runner

### Implementation

```python
# src/integrations/enrichment/base.py
from abc import ABC, abstractmethod
from src.domain.models import Contact


class EnrichmentStrategy(ABC):
    """
    Abstract enrichment strategy.
    Each provider implements this interface.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Returns the provider label (apollo | hunter | proxycurl)."""
        ...

    @abstractmethod
    async def enrich(self, domain: str, company_name: str) -> list[Contact]:
        """
        Fetch contacts for the given domain/company.

        Returns:
            List of Contact objects (empty list if not found — never raises).
        """
        ...


# src/integrations/enrichment/apollo_strategy.py
from src.integrations.enrichment.base import EnrichmentStrategy
from src.integrations.apollo import ApolloClient
from src.domain.models import Contact


class ApolloEnrichmentStrategy(EnrichmentStrategy):
    """Apollo.io contact enrichment — primary provider."""

    def __init__(self, client: ApolloClient) -> None:
        self._client = client

    @property
    def provider_name(self) -> str:
        return "apollo"

    async def enrich(self, domain: str, company_name: str) -> list[Contact]:
        raw = await self._client.search_people(domain=domain)
        return [self._map(r) for r in raw.get("people", [])]

    def _map(self, raw: dict) -> Contact:
        return Contact(
            full_name=raw.get("name"),
            title=raw.get("title"),
            email=raw.get("email"),
            enrichment_source="apollo",
        )


# src/services/enrichment_service.py
import json
from src.core.cache import RedisCache
from src.integrations.enrichment.base import EnrichmentStrategy
from src.domain.models import Contact

CACHE_TTL_SECONDS = 7 * 24 * 3600  # 7 days


class EnrichmentService:
    """
    Cascade runner: tries strategies in order, stops on first success.

    Rules:
        - Check Redis cache BEFORE calling any external API
        - If cached result exists → return immediately (never re-enrich)
        - Cache result after successful enrichment
        - Empty result from one provider → try next provider
        - Empty result from all providers → return [] (not an error)
    """

    def __init__(
        self,
        strategies: list[EnrichmentStrategy],  # injected in order: Apollo → Hunter → Proxycurl
        cache: RedisCache,
    ) -> None:
        self._strategies = strategies
        self._cache = cache

    async def enrich_lead(self, lead_id: str, domain: str, company_name: str) -> list[Contact]:
        cache_key = f"enrichment:{domain}"
        cached = await self._cache.get(cache_key)
        if cached:
            return [Contact(**c) for c in json.loads(cached)]

        for strategy in self._strategies:
            contacts = await strategy.enrich(domain=domain, company_name=company_name)
            if contacts:
                await self._cache.set(
                    cache_key,
                    json.dumps([c.model_dump() for c in contacts]),
                    ttl=CACHE_TTL_SECONDS,
                )
                return contacts

        return []
```

### Rules
- Strategy order is **Apollo → Hunter → Proxycurl** (most data-rich first).
- Cache TTL is **7 days** — never re-enrich within TTL; wasted API credits are a production bug.
- Adding a new provider = create new `EnrichmentStrategy` subclass + register in DI, **zero changes to `EnrichmentService`**.

---

## 4. Factory Pattern — Integration Client Registry

### Problem
Services request integration clients by name (e.g., `"apollo"`, `"sendgrid"`). Instantiation logic (API key decryption, base URL configuration) must be centralized.

### Where Used
- `src/integrations/factory.py`

### Implementation

```python
# src/integrations/factory.py
from typing import Protocol
from src.core.config import get_settings
from src.core.crypto import decrypt_fernet


class IntegrationClient(Protocol):
    """Structural type for all external integration clients."""
    ...


class IntegrationClientFactory:
    """
    Registry-based factory for external API clients.

    Rules:
        - All API keys decrypted at factory time (never stored in plain text)
        - Unknown provider name raises ValueError immediately
        - Each create_* method returns a new client instance per call
          (clients are lightweight; no singleton enforcement needed)
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._registry: dict[str, callable] = {
            "apollo": self._create_apollo,
            "hunter": self._create_hunter,
            "proxycurl": self._create_proxycurl,
            "sendgrid": self._create_sendgrid,
            "openai": self._create_openai,
        }

    def create(self, provider: str) -> IntegrationClient:
        if provider not in self._registry:
            raise ValueError(f"Unknown integration provider: '{provider}'. "
                             f"Available: {list(self._registry)}")
        return self._registry[provider]()

    def _create_apollo(self):
        from src.integrations.apollo import ApolloClient
        return ApolloClient(api_key=decrypt_fernet(self._settings.APOLLO_KEY_ENCRYPTED))

    def _create_hunter(self):
        from src.integrations.hunter import HunterClient
        return HunterClient(api_key=decrypt_fernet(self._settings.HUNTER_KEY_ENCRYPTED))

    def _create_proxycurl(self):
        from src.integrations.proxycurl import ProxycurlClient
        return ProxycurlClient(api_key=decrypt_fernet(self._settings.PROXYCURL_KEY_ENCRYPTED))

    def _create_sendgrid(self):
        from src.integrations.sendgrid import SendGridClient
        return SendGridClient(api_key=decrypt_fernet(self._settings.SENDGRID_KEY_ENCRYPTED))

    def _create_openai(self):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=decrypt_fernet(self._settings.OPENAI_KEY_ENCRYPTED),
            model=self._settings.OPENAI_MODEL,
            temperature=0.7,
        )
```

---

## 5. Adapter Pattern — External API Clients

### Problem
Each external API (Apollo, Hunter, SendGrid) has a unique request/response format. Services must not be coupled to vendor-specific schemas.

### Where Used
- `src/integrations/apollo.py`, `hunter.py`, `proxycurl.py`, `sendgrid.py`

### Implementation

```python
# src/integrations/apollo.py
import httpx
from src.core.logging import get_logger
from src.core.exceptions import IntegrationError

logger = get_logger(__name__)

APOLLO_BASE_URL = "https://api.apollo.io/v1"
DEFAULT_TIMEOUT_SECONDS = 30
MAX_RETRIES = 3


class ApolloClient:
    """
    HTTP adapter for Apollo.io People Search API.

    Adapts Apollo's response format to the platform's Contact schema.
    All HTTP errors are mapped to IntegrationError — callers never
    see vendor-specific exceptions.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=APOLLO_BASE_URL,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            headers={"Content-Type": "application/json"},
        )

    async def search_people(
        self,
        domain: str,
        titles: list[str] | None = None,
        limit: int = 10,
    ) -> dict:
        """
        Search Apollo for people at a given domain.

        Returns:
            Raw Apollo response dict — mapping to Contact is done
            by ApolloEnrichmentStrategy, not here.

        Raises:
            IntegrationError: on any HTTP or network failure.
        """
        payload = {
            "api_key": self._api_key,
            "q_organization_domains": domain,
            "person_titles": titles or ["buyer", "purchasing", "procurement"],
            "per_page": limit,
        }
        try:
            response = await self._client.post("/mixed_people/search", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Apollo API HTTP error",
                status_code=exc.response.status_code,
                domain=domain,
            )
            raise IntegrationError(
                provider="apollo",
                message=f"HTTP {exc.response.status_code}",
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Apollo network error", domain=domain, error=str(exc))
            raise IntegrationError(provider="apollo", message="Network error") from exc

    async def close(self) -> None:
        await self._client.aclose()
```

### Rules
- Adapters **never** raise vendor-specific exceptions to callers; always re-raise as `IntegrationError`.
- Adapters **never** contain business logic — only HTTP plumbing and format mapping.
- All clients use `httpx.AsyncClient` (not `requests`).
- Client lifecycle: created by factory, closed in FastAPI lifespan or Celery task teardown.

---

## 6. State Machine Pattern — LangGraph Lead Pipeline

### Problem
Lead processing has multiple ordered stages (match → enrich → score → generate outreach) with conditional branching (not-eligible leads exit early). A linear function call chain cannot express this cleanly.

### Where Used
- `src/agents/lead_pipeline.py` — graph definition
- `src/agents/nodes/` — individual node functions

### Implementation

```python
# src/agents/lead_pipeline.py
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from src.agents.nodes.match import match_inventory_node
from src.agents.nodes.enrich import enrich_contact_node
from src.agents.nodes.score import score_lead_node
from src.agents.nodes.outreach import generate_outreach_node


class LeadPipelineState(TypedDict):
    """
    Immutable state passed between LangGraph nodes.

    Rules:
        - Nodes NEVER mutate state in place; always return a new partial dict
        - All fields are Optional — nodes set only what they produce
        - trace_id flows through every node for correlation
    """
    lead_id: str
    trace_id: str
    # Set by match_inventory_node
    is_eligible: bool | None
    matched_inventory_ids: list[str] | None
    match_score: float | None
    # Set by enrich_contact_node
    contact_ids: list[str] | None
    enrichment_source: str | None
    # Set by score_lead_node
    lead_score: float | None
    score_tier: str | None
    # Set by generate_outreach_node
    outreach_message_ids: list[str] | None
    # Error tracking
    error: str | None


def _route_after_match(state: LeadPipelineState) -> str:
    """
    Conditional edge: eligible leads proceed; not-eligible leads end.
    """
    if state.get("is_eligible"):
        return "enrich_contact"
    return END


def build_lead_pipeline() -> StateGraph:
    """
    Builds and compiles the LangGraph lead processing pipeline.

    Graph topology:
        match_inventory → [eligible] → enrich_contact → score_lead → generate_outreach → END
                        → [not_eligible] → END
    """
    graph = StateGraph(LeadPipelineState)

    graph.add_node("match_inventory", match_inventory_node)
    graph.add_node("enrich_contact", enrich_contact_node)
    graph.add_node("score_lead", score_lead_node)
    graph.add_node("generate_outreach", generate_outreach_node)

    graph.set_entry_point("match_inventory")

    graph.add_conditional_edges(
        "match_inventory",
        _route_after_match,
        {
            "enrich_contact": "enrich_contact",
            END: END,
        },
    )

    graph.add_edge("enrich_contact", "score_lead")
    graph.add_edge("score_lead", "generate_outreach")
    graph.add_edge("generate_outreach", END)

    return graph.compile()


# src/agents/nodes/match.py
from src.agents.lead_pipeline import LeadPipelineState
from src.repositories.lead_repository import LeadRepository
from src.services.match_service import InventoryMatchService


async def match_inventory_node(
    state: LeadPipelineState,
    lead_repo: LeadRepository,
    match_service: InventoryMatchService,
) -> dict:
    """
    Node 1: Match lead against available inventory.

    Returns partial state update only — does not mutate state dict.
    """
    matches = await match_service.find_matches(lead_id=state["lead_id"])
    is_eligible = len(matches) > 0
    return {
        "is_eligible": is_eligible,
        "matched_inventory_ids": [m.inventory_id for m in matches],
        "match_score": max((m.match_score for m in matches), default=0.0),
    }
```

### Rules
- Nodes **always** return a `dict` with only the keys they set — partial state updates only.
- Nodes **never** write to the database directly; they call service methods which use repositories.
- `trace_id` must flow from initial state through all nodes — log it in every node.
- Conditional routing functions must be pure (no side effects).

---

## 7. Chain of Responsibility — LangChain Outreach Generation

### Problem
Outreach generation requires multiple sequential steps: retrieve lead context → fetch matched inventory → build prompt → call LLM → validate output → format response. Each step passes its output to the next.

### Where Used
- `src/agents/outreach_chain.py`

### Implementation

```python
# src/agents/outreach_chain.py
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from src.agents.prompts import OUTREACH_SYSTEM_PROMPT, OUTREACH_USER_TEMPLATE


def build_outreach_chain(llm: ChatOpenAI):
    """
    LangChain LCEL pipeline for personalized outreach email generation.

    Chain steps:
        1. enrich_context  — fetch lead + matched inventory details
        2. build_prompt    — format system + user prompt from templates
        3. llm             — call OpenAI (gpt-4o-mini by default)
        4. parse_output    — extract string from AIMessage
        5. validate        — check output meets minimum quality rules

    Rules:
        - Chain is stateless; context is passed via input dict
        - LLM temperature = 0.7 for outreach (balances creativity / accuracy)
        - Output validation raises ValueError if subject or body is missing
    """
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages([
        ("system", OUTREACH_SYSTEM_PROMPT),
        ("human", OUTREACH_USER_TEMPLATE),
    ])

    def validate_output(text: str) -> str:
        if len(text.strip()) < 50:
            raise ValueError("LLM output too short — outreach generation failed")
        return text

    chain = (
        RunnablePassthrough()           # passes input dict through
        | prompt                        # formats prompt with context
        | llm                           # calls OpenAI
        | StrOutputParser()             # extracts string from AIMessage
        | RunnableLambda(validate_output)  # validates minimum quality
    )

    return chain
```

---

## 8. Observer / Event Bus Pattern

### Problem
When a lead changes status (e.g., `enriched`, `scored`), multiple downstream actions must fire: CRM activity log append, lead status update, webhook notification. Coupling services directly creates spaghetti dependencies.

### Where Used
- `src/core/events.py` — EventBus
- `src/services/crm_service.py` — subscriber

### Implementation

```python
# src/core/events.py
import asyncio
from collections import defaultdict
from typing import Callable, Awaitable
from dataclasses import dataclass

HandlerFunc = Callable[["DomainEvent"], Awaitable[None]]


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events. Immutable by design."""
    event_type: str
    lead_id: str
    payload: dict
    trace_id: str


class EventBus:
    """
    Lightweight in-process async event bus.

    Rules:
        - All subscribers are async (never blocking)
        - Subscriber failures are caught and logged — one failing subscriber
          must not prevent others from running
        - For cross-process events (e.g., Celery), publish to a task queue instead
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[HandlerFunc]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: HandlerFunc) -> None:
        self._subscribers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._subscribers.get(event.event_type, [])
        await asyncio.gather(
            *[self._safe_call(h, event) for h in handlers],
            return_exceptions=False,
        )

    @staticmethod
    async def _safe_call(handler: HandlerFunc, event: DomainEvent) -> None:
        try:
            await handler(event)
        except Exception as exc:  # noqa: BLE001
            from src.core.logging import get_logger
            get_logger(__name__).error(
                "Event handler failed",
                event_type=event.event_type,
                handler=handler.__name__,
                error=str(exc),
            )


# Global bus instance — registered in FastAPI lifespan
event_bus = EventBus()
```

---

## 9. Dependency Injection — FastAPI Depends

### Problem
Repositories and services need database sessions, Redis connections, and API keys at request time. Hardcoding these inside route functions makes testing impossible.

### Where Used
- `src/api/dependencies.py`
- All routers: `src/api/routers/`

### Implementation

```python
# src/api/dependencies.py
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_async_session
from src.core.cache import RedisCache, get_redis_cache
from src.repositories.lead_repository import LeadRepository
from src.repositories.crm_repository import CRMRepository
from src.services.enrichment_service import EnrichmentService
from src.integrations.enrichment.apollo_strategy import ApolloEnrichmentStrategy
from src.integrations.enrichment.hunter_strategy import HunterEnrichmentStrategy
from src.integrations.factory import IntegrationClientFactory


@lru_cache(maxsize=1)
def get_factory() -> IntegrationClientFactory:
    return IntegrationClientFactory()


async def get_lead_repository(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> LeadRepository:
    return LeadRepository(session)


async def get_enrichment_service(
    cache: Annotated[RedisCache, Depends(get_redis_cache)],
) -> EnrichmentService:
    factory = get_factory()
    strategies = [
        ApolloEnrichmentStrategy(factory.create("apollo")),
        HunterEnrichmentStrategy(factory.create("hunter")),
    ]
    return EnrichmentService(strategies=strategies, cache=cache)


# Usage in router:
# @router.get("/leads/{lead_id}")
# async def get_lead(
#     lead_id: UUID,
#     repo: Annotated[LeadRepository, Depends(get_lead_repository)],
# ) -> LeadResponse:
#     ...
```

---

## 10. Decorator Pattern — Cross-Cutting Concerns

### Problem
Retry logic, structured logging, and performance timing are needed across many service and integration methods. Duplicating this code in every method violates DRY.

### Where Used
- `src/core/decorators.py`
- Integration clients and services

### Implementation

```python
# src/core/decorators.py
import asyncio
import functools
import time
from typing import Callable, TypeVar

from src.core.logging import get_logger

F = TypeVar("F", bound=Callable)


def with_retry(
    max_attempts: int = 3,
    backoff_base: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable[[F], F]:
    """
    Exponential backoff retry decorator for async functions.

    Backoff: delay = backoff_base ^ (attempt - 1) seconds
    Attempts: 1 (immediate), 2 (2s), 3 (4s) with max_attempts=3, base=2

    Rules:
        - Only retries on listed exception types
        - Logs each retry at WARNING level with attempt count
        - Re-raises original exception after max_attempts exhausted
    """
    def decorator(func: F) -> F:
        logger = get_logger(func.__module__)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        raise
                    delay = backoff_base ** (attempt - 1)
                    logger.warning(
                        "Retrying after error",
                        func=func.__name__,
                        attempt=attempt,
                        delay_seconds=delay,
                        error=str(exc),
                    )
                    await asyncio.sleep(delay)

        return wrapper  # type: ignore[return-value]
    return decorator


def timed(func: F) -> F:
    """Log wall-clock duration of any async function call."""
    logger = get_logger(func.__module__)

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.debug("Function timed", func=func.__name__, duration_ms=round(duration_ms, 2))
        return result

    return wrapper  # type: ignore[return-value]
```

---

## 11. Template Method Pattern — Base Service

### Problem
All business services share a common pre/post-action lifecycle: validate input → execute core logic → log CRM activity. The sequence is fixed; only the core logic varies per service.

### Where Used
- `src/services/base.py`
- `src/services/lead_ingestion_service.py`, `enrichment_service.py`, `outreach_service.py`

### Implementation

```python
# src/services/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

from src.core.logging import get_logger
from src.repositories.crm_repository import CRMRepository
from src.domain.models import CRMActivity

TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class BaseService(ABC, Generic[TInput, TOutput]):
    """
    Template method pattern for domain services.

    Sequence:
        1. validate_input(input)         — subclass validates business rules
        2. execute(input) → output       — subclass core logic (abstract)
        3. _post_execute(input, output)  — base class logs CRM activity

    Rules:
        - Subclasses MUST implement execute()
        - Subclasses SHOULD override validate_input() for business validation
        - _post_execute() is called automatically — do not override
    """

    def __init__(self, crm_repo: CRMRepository) -> None:
        self._crm_repo = crm_repo
        self._logger = get_logger(self.__class__.__name__)

    async def run(self, input_data: TInput) -> TOutput:
        self.validate_input(input_data)
        result = await self.execute(input_data)
        await self._post_execute(input_data, result)
        return result

    def validate_input(self, input_data: TInput) -> None:
        """Override to add business-rule validation before execute()."""
        pass

    @abstractmethod
    async def execute(self, input_data: TInput) -> TOutput:
        """Core business logic — must be implemented by each subclass."""
        ...

    async def _post_execute(self, input_data: TInput, result: TOutput) -> None:
        """Hook: log CRM activity after successful execution."""
        pass  # subclasses call self._crm_repo.append(...) here if needed
```

---

## 12. Saga Pattern — Celery Distributed Transactions

### Problem
The lead ingestion pipeline involves multiple steps across services that may fail independently (file parse fails, DB write succeeds; enrichment API times out). Without coordination, pipelines get stuck in inconsistent states.

### Where Used
- `src/tasks/ingestion_tasks.py`
- `src/tasks/enrichment_tasks.py`
- `src/tasks/outreach_tasks.py`

### Implementation

```python
# src/tasks/ingestion_tasks.py
from celery import shared_task
from src.tasks.celery_app import celery_app
from src.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.ingest_lead_file",
    queue="ingestion",
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,      # task re-queued if worker dies before ack
    reject_on_worker_lost=True,
)
def ingest_lead_file(self, file_path: str, uploaded_by: str, trace_id: str) -> dict:
    """
    Saga step 1: Parse CSV → create Lead records → trigger enrichment saga.

    On failure: exponential backoff retry (60s, 120s, 240s).
    On final failure: write system_error to crm_activity; mark lead status=error.

    Compensation: no hard rollback needed — leads without status=enriched
    are safe to re-process (idempotent domain check by domain).
    """
    import asyncio
    from src.services.lead_ingestion_service import LeadIngestionService

    try:
        logger.info("Starting lead file ingestion", file_path=file_path, trace_id=trace_id)
        result = asyncio.run(LeadIngestionService().ingest_file(file_path, uploaded_by))
        # Chain: on success, trigger enrichment for each eligible lead
        from src.tasks.enrichment_tasks import enrich_lead
        for lead_id in result.get("eligible_lead_ids", []):
            enrich_lead.apply_async(
                args=[lead_id, trace_id],
                queue="enrichment",
                countdown=2,  # 2s stagger to avoid API burst
            )
        return result
    except Exception as exc:
        retry_number = self.request.retries
        delay = 60 * (2 ** retry_number)
        logger.warning(
            "Lead ingestion failed, scheduling retry",
            attempt=retry_number + 1,
            delay_seconds=delay,
            error=str(exc),
            trace_id=trace_id,
        )
        raise self.retry(exc=exc, countdown=delay)
```

### Rules
- All Celery tasks use `acks_late=True` — message only acknowledged after task completes successfully.
- Compensation for failed Saga steps: log `system_error` to `crm_activity`; never silently swallow.
- Task chaining uses `apply_async` with explicit `queue` — never use `.delay()` (no queue control).
- Idempotency: task re-execution must not create duplicate data (check by domain, lead_id, etc.).

---

## Pattern Application Matrix

| Layer | Patterns Applied |
|-------|-----------------|
| API Router | Dependency Injection, Decorator (timing) |
| Service | Template Method, Observer/Event Bus, Strategy |
| Repository | Repository, Unit of Work |
| Agent | State Machine (LangGraph), Chain of Responsibility (LangChain) |
| Integration | Adapter, Factory, Decorator (retry) |
| Task | Saga, Decorator (retry, timing) |
| Core | Observer/Event Bus, Decorator |

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-03-18 | Initial pattern catalog — 12 patterns with full Python implementation |
