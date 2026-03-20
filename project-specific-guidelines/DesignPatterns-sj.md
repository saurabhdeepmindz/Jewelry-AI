# Design Patterns — Jewelry AI Platform

## Overview

The following design patterns are applied throughout the Jewelry AI platform to ensure modularity, testability, and maintainability. Each pattern is described with its rationale, applicability, and a concrete code example from the project.

---

## 1. Repository Pattern

**Where Used**: All data access (`src/repositories/`)

**Rationale**: Decouples business logic from database implementation. Repositories can be swapped (PostgreSQL → MongoDB) or mocked in tests without touching service code.

```python
# src/repositories/base_repository.py

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar
from uuid import UUID

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository defining the standard data access interface.

    All concrete repositories must implement these methods,
    ensuring consistent CRUD operations across all entities.
    """

    @abstractmethod
    async def find_by_id(self, entity_id: UUID) -> Optional[T]:
        """Retrieve a single entity by its primary key."""
        ...

    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """Retrieve a paginated list of entities."""
        ...

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Persist a new entity and return it with assigned ID."""
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Persist changes to an existing entity."""
        ...

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Soft-delete an entity by ID. Returns True if deleted."""
        ...
```

---

## 2. Strategy Pattern

**Where Used**: Lead scoring, contact enrichment, outreach channel selection

**Rationale**: Different scoring algorithms (rule-based vs ML) and enrichment providers (Apollo vs Hunter) can be swapped at runtime via configuration without changing the calling code.

```python
# src/services/enrichment_service.py

from abc import ABC, abstractmethod
from src.domain.contact import Contact


class EnrichmentStrategy(ABC):
    """Abstract strategy for contact enrichment."""

    @abstractmethod
    async def enrich(self, company_name: str, domain: str) -> Contact:
        """
        Enrich a lead with contact details.

        Args:
            company_name (str): Name of the company to enrich.
            domain (str): Web domain of the company.

        Returns:
            Contact: Enriched contact with email, phone, title.
        """
        ...


class ApolloEnrichmentStrategy(EnrichmentStrategy):
    """Enrichment via Apollo.io API."""

    async def enrich(self, company_name: str, domain: str) -> Contact:
        # Apollo-specific implementation
        ...


class HunterEnrichmentStrategy(EnrichmentStrategy):
    """Enrichment via Hunter.io API."""

    async def enrich(self, company_name: str, domain: str) -> Contact:
        # Hunter-specific implementation
        ...


class EnrichmentService:
    """
    Context class that delegates enrichment to a configured strategy.
    Allows runtime switching between enrichment providers.
    """

    def __init__(self, strategy: EnrichmentStrategy) -> None:
        # Strategy is injected — service is provider-agnostic
        self._strategy = strategy

    async def enrich_lead(self, company_name: str, domain: str) -> Contact:
        return await self._strategy.enrich(company_name, domain)
```

---

## 3. Factory Pattern

**Where Used**: Agent creation (`src/agents/`), scraper instantiation (`src/scrapers/`)

**Rationale**: Centralizes object creation logic. Adding a new scraper type requires only a new class + a factory entry, not changes across the codebase.

```python
# src/scrapers/scraper_factory.py

from src.scrapers.base_scraper import BaseScraper
from src.scrapers.gmt_scraper import GmtScraper
from src.scrapers.trade_book_scraper import TradeBookScraper
from src.scrapers.rapid_list_scraper import RapidListScraper


class ScraperFactory:
    """
    Factory for instantiating lead source scrapers by source type.

    Centralizes scraper creation so new sources can be added
    without modifying calling code.
    """

    _registry: dict[str, type[BaseScraper]] = {
        "gmt": GmtScraper,
        "trade_book": TradeBookScraper,
        "rapid_list": RapidListScraper,
    }

    @classmethod
    def create(cls, source_type: str) -> BaseScraper:
        """
        Instantiate a scraper for the given source type.

        Args:
            source_type (str): Identifier for the lead source (e.g., "gmt").

        Returns:
            BaseScraper: Concrete scraper instance.

        Raises:
            ValueError: If source_type is not registered.
        """
        scraper_class = cls._registry.get(source_type)
        if not scraper_class:
            raise ValueError(f"Unknown scraper source type: {source_type}")
        return scraper_class()
```

---

## 4. Observer Pattern (Event-Driven)

**Where Used**: Post-ingestion triggers (enrichment, scoring, outreach scheduling)

**Rationale**: Decouples the lead ingestion pipeline from downstream processes. New consumers (e.g., Slack notification) can be added without modifying the ingestion service.

```python
# src/core/events.py

from dataclasses import dataclass
from typing import Callable, Awaitable
from uuid import UUID


@dataclass
class LeadIngestedEvent:
    """Event emitted when a new lead is successfully ingested."""
    lead_id: UUID
    source: str


class EventBus:
    """
    Simple in-process async event bus for domain events.

    Subscribers register handlers per event type.
    The bus is injected via dependency injection.
    """

    def __init__(self) -> None:
        # Map of event type to list of async handlers
        self._handlers: dict[type, list[Callable]] = {}

    def subscribe(self, event_type: type, handler: Callable[..., Awaitable]) -> None:
        """Register an async handler for a given event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: object) -> None:
        """Dispatch an event to all registered handlers."""
        for handler in self._handlers.get(type(event), []):
            await handler(event)
```

---

## 5. Dependency Injection (FastAPI Native)

**Where Used**: All API routers (`src/api/routers/`)

**Rationale**: Makes services testable by allowing mock injection in tests. Aligns with FastAPI's built-in DI system.

```python
# src/api/dependencies.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_async_session
from src.repositories.lead_repository import LeadRepository
from src.services.lead_ingestion_service import LeadIngestionService


async def get_lead_repository(
    session: AsyncSession = Depends(get_async_session)
) -> LeadRepository:
    """Provide a LeadRepository bound to the current DB session."""
    return LeadRepository(session)


async def get_lead_ingestion_service(
    repo: LeadRepository = Depends(get_lead_repository)
) -> LeadIngestionService:
    """Provide a LeadIngestionService with injected repository."""
    return LeadIngestionService(repo)
```

---

## 6. Chain of Responsibility (LangChain Pipeline)

**Where Used**: Lead enrichment and outreach generation pipelines (`src/agents/`)

**Rationale**: Each processing step (validate → enrich → score → draft outreach) is an independent, reusable chain link. Steps can be reordered or replaced without coupling.

```python
# src/agents/enrichment_agent.py

from langchain_core.runnables import RunnableLambda, RunnableSequence

# Each step is an isolated, testable unit
validate_step = RunnableLambda(validate_lead_data)
enrich_step = RunnableLambda(enrich_via_apollo)
score_step = RunnableLambda(compute_lead_score)
draft_step = RunnableLambda(draft_outreach_message)

# Compose into a pipeline — order is explicit and maintainable
enrichment_pipeline: RunnableSequence = (
    validate_step | enrich_step | score_step | draft_step
)
```

---

## 7. State Machine (LangGraph Workflows)

**Where Used**: Full lead automation workflow (`src/agents/workflows/lead_pipeline.py`)

**Rationale**: Complex multi-step workflows with branching (eligible/not eligible, enriched/failed) are modeled as explicit state machines. State transitions are auditable and resumable.

```python
# src/agents/workflows/lead_pipeline.py

from langgraph.graph import StateGraph, END
from typing import TypedDict


class LeadPipelineState(TypedDict):
    """Typed state object passed between all workflow nodes."""
    lead_id: str
    is_eligible: bool
    contact_enriched: bool
    outreach_sent: bool
    error: str | None


# Define the state graph
workflow = StateGraph(LeadPipelineState)

# Nodes represent discrete processing steps
workflow.add_node("match_inventory", match_inventory_node)
workflow.add_node("enrich_contact", enrich_contact_node)
workflow.add_node("send_outreach", send_outreach_node)
workflow.add_node("log_crm", log_crm_node)
workflow.add_node("mark_ineligible", mark_ineligible_node)

# Edges define the flow with conditional branching
workflow.set_entry_point("match_inventory")
workflow.add_conditional_edges(
    "match_inventory",
    lambda state: "enrich_contact" if state["is_eligible"] else "mark_ineligible"
)
workflow.add_edge("enrich_contact", "send_outreach")
workflow.add_edge("send_outreach", "log_crm")
workflow.add_edge("log_crm", END)
workflow.add_edge("mark_ineligible", END)

lead_pipeline = workflow.compile()
```

---

## 8. Adapter Pattern

**Where Used**: Third-party API integrations (`src/integrations/`)

**Rationale**: Wraps external APIs behind a consistent internal interface. Changing from Apollo.io to Clearbit only requires replacing the adapter, not modifying any service code.

```python
# src/integrations/apollo_client.py

import httpx
from src.domain.contact import Contact
from src.core.config import settings
from src.core.exceptions import ApolloAPIException


class ApolloClient:
    """
    Adapter wrapping the Apollo.io People Enrichment API.

    Translates Apollo's API response schema into the internal
    Contact domain model used across the platform.
    """

    BASE_URL = "https://api.apollo.io/v1"

    async def enrich_person(self, email: str) -> Contact:
        """
        Enrich a contact using Apollo.io's person enrichment endpoint.

        Args:
            email (str): Email address to enrich.

        Returns:
            Contact: Internal Contact domain object with enriched data.

        Raises:
            ApolloAPIException: If the API call fails or returns non-2xx.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/people/match",
                json={"email": email},
                headers={"X-Api-Key": settings.APOLLO_API_KEY}
            )
        if response.status_code != 200:
            raise ApolloAPIException(status=response.status_code, detail=response.text)

        # Map Apollo response to internal Contact model
        data = response.json().get("person", {})
        return Contact(
            name=data.get("name"),
            email=email,
            phone=data.get("phone_numbers", [{}])[0].get("raw_number"),
            title=data.get("title"),
            linkedin_url=data.get("linkedin_url"),
        )
```

---

## Pattern Summary

| Pattern | Location | Problem Solved |
|---|---|---|
| Repository | `src/repositories/` | Decouples data access from business logic |
| Strategy | `src/services/` | Swappable algorithms and providers |
| Factory | `src/scrapers/`, `src/agents/` | Centralized object creation |
| Observer | `src/core/events.py` | Decoupled event-driven side effects |
| Dependency Injection | `src/api/dependencies.py` | Testable, configurable service wiring |
| Chain of Responsibility | `src/agents/` | Composable LangChain processing pipelines |
| State Machine | `src/agents/workflows/` | Auditable multi-step automation workflows |
| Adapter | `src/integrations/` | Stable internal API over unstable external APIs |
