"""Display formatters for Streamlit UI output.

All functions are pure (no side effects) and return strings.
"""
from __future__ import annotations

from datetime import UTC, datetime

from src.ui.utils.constants import (
    DATE_FORMAT,
    DATETIME_FORMAT,
    ENRICHMENT_SOURCE_LABELS,
    LEAD_SOURCE_LABELS,
    STATUS_COLOR,
    STATUS_EMOJI,
    STATUS_LABELS,
)


def format_carat(value: float | int | None) -> str:
    """Format carat weight to exactly 2 decimal places (GIA standard).

    >>> format_carat(1.5)
    '1.50 ct'
    >>> format_carat(None)
    '—'
    """
    if value is None:
        return "—"
    return f"{float(value):.2f} ct"


def format_currency(value: float | int | None, currency: str = "USD") -> str:
    """Format a monetary value with thousands separator.

    >>> format_currency(12500)
    '$12,500'
    >>> format_currency(None)
    '—'
    """
    if value is None:
        return "—"
    if currency == "USD":
        return f"${float(value):,.0f}"
    return f"{float(value):,.0f} {currency}"


def format_datetime(value: str | datetime | None) -> str:
    """Format an ISO-8601 datetime string or datetime object for display.

    >>> format_datetime("2024-01-15T09:30:00Z")
    '15 Jan 2024, 09:30'
    >>> format_datetime(None)
    '—'
    """
    if value is None:
        return "—"
    if isinstance(value, str):
        try:
            # Handle Z suffix and offset-aware strings
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    else:
        dt = value
    # Convert to local-naive for display
    if dt.tzinfo is not None:
        dt = dt.astimezone(tz=None).replace(tzinfo=None)
    return dt.strftime(DATETIME_FORMAT)


def format_date(value: str | datetime | None) -> str:
    """Format an ISO date string for display.

    >>> format_date("2024-01-15")
    '15 Jan 2024'
    """
    if value is None:
        return "—"
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    else:
        dt = value
    if dt.tzinfo is not None:
        dt = dt.astimezone(tz=None).replace(tzinfo=None)
    return dt.strftime(DATE_FORMAT)


def relative_time(value: str | datetime | None) -> str:
    """Return a human-readable relative time string (e.g., '3 hours ago').

    Falls back to formatted datetime if value is too old or None.
    """
    if value is None:
        return "—"
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    else:
        dt = value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    now = datetime.now(tz=UTC)
    delta = now - dt
    seconds = int(delta.total_seconds())

    if seconds < 60:
        return "just now"
    if seconds < 3600:
        m = seconds // 60
        return f"{m} minute{'s' if m != 1 else ''} ago"
    if seconds < 86400:
        h = seconds // 3600
        return f"{h} hour{'s' if h != 1 else ''} ago"
    if seconds < 604800:
        d = seconds // 86400
        return f"{d} day{'s' if d != 1 else ''} ago"
    return format_datetime(dt)


def status_badge(status: str) -> str:
    """Return a text badge string combining emoji + label.

    >>> status_badge("completed")
    '✅ Completed'
    """
    emoji = STATUS_EMOJI.get(status, "•")
    label = STATUS_LABELS.get(status, status.title())
    return f"{emoji} {label}"


def status_color(status: str) -> str:
    """Return the hex color string for a given status."""
    return STATUS_COLOR.get(status, "#808080")


def format_enrichment_source(source: str | None) -> str:
    """Return human-readable enrichment source name."""
    if source is None:
        return "—"
    return ENRICHMENT_SOURCE_LABELS.get(source, source.title())


def format_lead_source(source: str | None) -> str:
    """Return human-readable lead source label."""
    if source is None:
        return "—"
    return LEAD_SOURCE_LABELS.get(source, source.replace("_", " ").title())


def format_score(score: float | None) -> str:
    """Format a 0-100 lead score.

    >>> format_score(87.5)
    '87.5 / 100'
    >>> format_score(None)
    'Not scored'
    """
    if score is None:
        return "Not scored"
    return f"{score:.1f} / 100"


def score_color(score: float | None) -> str:
    """Return a hex color based on score tier."""
    if score is None:
        return "#808080"
    if score >= 75:
        return "#27AE60"  # green
    if score >= 50:
        return "#F5A623"  # amber
    return "#E74C3C"  # red
