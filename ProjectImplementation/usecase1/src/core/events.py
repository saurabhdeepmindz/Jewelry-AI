"""In-process async event bus for domain events.

Used to decouple services from side effects (CRM logging, Celery task dispatch).
Services emit events; listeners handle the side effects independently.

Usage:
    from src.core.events import publish, subscribe

    # Register a handler (at startup)
    subscribe("lead.ingested", crm_service.log_lead_ingested)

    # Emit from a service
    await publish("lead.ingested", lead_id=str(lead.id), company=lead.company_name)
"""
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

# Handler type: async callable that accepts keyword arguments
EventHandler = Callable[..., Awaitable[None]]

_handlers: dict[str, list[EventHandler]] = defaultdict(list)


def subscribe(event_name: str, handler: EventHandler) -> None:
    """Register an async handler for a named event.

    Multiple handlers can be registered for the same event.
    Handlers are called in registration order.
    """
    _handlers[event_name].append(handler)


async def publish(event_name: str, **payload: Any) -> None:
    """Publish an event to all registered handlers.

    All handlers are called sequentially and awaited.
    Exceptions in handlers propagate to the caller.
    """
    for handler in _handlers.get(event_name, []):
        await handler(**payload)


def clear_handlers(event_name: str | None = None) -> None:
    """Remove handlers — used in tests to reset state between tests."""
    if event_name:
        _handlers.pop(event_name, None)
    else:
        _handlers.clear()
