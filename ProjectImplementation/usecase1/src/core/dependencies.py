"""Shared FastAPI dependency providers.

These are injected via FastAPI's Depends() mechanism.
Route-level dependencies (per-service) live in src/api/dependencies.py.
"""
from src.db.session import get_async_session

# Re-export for convenience — routers can import get_db from here
get_db = get_async_session
