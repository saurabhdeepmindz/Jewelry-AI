"""Structured JSON logging with trace_id context propagation.

Every log line is a single-line JSON object containing:
  timestamp, level, service, module, message, trace_id

Usage:
    from src.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("Lead ingested %s", lead_id)

The trace_id context variable is populated by TraceIDMiddleware on each request.
"""
import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context variable — set by TraceIDMiddleware per request; empty string when no request context
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

_SERVICE_NAME = "jewelry-ai"


class JSONFormatter(logging.Formatter):
    """Formats LogRecord instances as single-line JSON with trace_id injection.

    Exported publicly so tests can instantiate it directly without
    calling configure_logging() (which replaces pytest's caplog handler).
    """

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": _SERVICE_NAME,
            "module": record.name,
            "message": record.getMessage(),
            "trace_id": trace_id_var.get("") or None,
        }
        # Attach extra fields if the caller passed extra={"key": val}
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            entry.update(extra)

        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str)


# Internal alias so existing imports like `from src.core.logging import _JSONFormatter` still work
_JSONFormatter = JSONFormatter


def configure_logging(log_level: str = "INFO") -> None:
    """Configure root logger to emit structured JSON to stdout.

    Call once at application startup (in src/main.py).
    NOTE: This replaces all existing handlers on the root logger.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Silence noisy third-party loggers in production
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Use __name__ to get proper module hierarchy."""
    return logging.getLogger(name)
