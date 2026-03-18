"""Celery application factory and queue configuration.

Architecture.md §8 — Celery Task Architecture.

Queues:
  ingestion  — bulk CSV processing
  enrichment — Apollo/Hunter API calls (rate-limited, retried)
  outreach   — LLM email generation and SendGrid delivery
  ml         — XGBoost scoring and model retraining
"""
from celery import Celery

from src.core.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "jewelry_ai",
    broker=_settings.REDIS_URL,
    backend=_settings.REDIS_URL,
    include=[
        "src.tasks.ingestion_tasks",
        "src.tasks.enrichment_tasks",
        "src.tasks.outreach_tasks",
        "src.tasks.ml_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,           # Re-queue task if worker crashes mid-execution
    worker_prefetch_multiplier=1,  # One task at a time per worker for fairness
    task_routes={
        "src.tasks.ingestion_tasks.*":  {"queue": "ingestion"},
        "src.tasks.enrichment_tasks.*": {"queue": "enrichment"},
        "src.tasks.outreach_tasks.*":   {"queue": "outreach"},
        "src.tasks.ml_tasks.*":         {"queue": "ml"},
    },
    # Retry defaults — individual tasks can override
    task_default_retry_delay=30,   # 30 seconds between retries
    task_max_retries=3,
)
