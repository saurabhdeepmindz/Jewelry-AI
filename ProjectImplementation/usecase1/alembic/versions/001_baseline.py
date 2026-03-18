"""Baseline — enable extensions, empty schema.

Revision ID: 001
Revises: None
Create Date: 2026-03-19

This is the baseline migration. It enables the PostgreSQL extensions required
by the platform. All table migrations follow in subsequent revisions.
"""
from collections.abc import Sequence

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pgvector for embedding-based inventory matching
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    # Enable uuid-ossp for gen_random_uuid() (available by default in PG13+)
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')


def downgrade() -> None:
    # Keep extensions on downgrade — removing them would break other objects
    pass
