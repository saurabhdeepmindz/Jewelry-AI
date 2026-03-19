"""Route-level FastAPI dependency providers.

Grows with each increment:
  - Increment 0: get_db (re-exported from core.dependencies)
  - Increment 7: get_current_user, require_role
  - Later increments: get_lead_service, get_enrichment_service, etc.
"""


from src.db.session import get_async_session

# Re-export the DB session dependency for use in all routers
get_db = get_async_session
