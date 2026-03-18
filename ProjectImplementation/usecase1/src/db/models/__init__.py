"""ORM model registry.

Import all ORM models here so that:
  1. Alembic autogenerate can detect all tables via Base.metadata
  2. A single import in alembic/env.py registers everything

Add each new model import here as it is created in later increments:
  from src.db.models.lead_model import LeadORM       # Increment 1
  from src.db.models.inventory_model import InventoryORM  # Increment 2
  ...
"""
# Models will be imported here incrementally as they are built
