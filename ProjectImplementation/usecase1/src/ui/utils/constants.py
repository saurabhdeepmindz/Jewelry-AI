"""UI-layer constants: status colors, display labels, polling config."""
from __future__ import annotations

# ------------------------------------------------------------------
# Job / Lead status display
# ------------------------------------------------------------------

STATUS_LABELS: dict[str, str] = {
    "queued": "Queued",
    "processing": "Processing",
    "completed": "Completed",
    "failed": "Failed",
    "ingested": "Ingested",
    "matched": "Matched",
    "enriched": "Enriched",
    "outreached": "Outreached",
    "not_eligible": "Not Eligible",
}

STATUS_EMOJI: dict[str, str] = {
    "queued": "🕐",
    "processing": "⚙️",
    "completed": "✅",
    "failed": "❌",
    "ingested": "📥",
    "matched": "🔗",
    "enriched": "🔍",
    "outreached": "📧",
    "not_eligible": "🚫",
}

STATUS_COLOR: dict[str, str] = {
    "queued": "#808080",
    "processing": "#F5A623",
    "completed": "#27AE60",
    "failed": "#E74C3C",
    "ingested": "#3498DB",
    "matched": "#9B59B6",
    "enriched": "#1ABC9C",
    "outreached": "#2ECC71",
    "not_eligible": "#95A5A6",
}

# ------------------------------------------------------------------
# Enrichment source labels
# ------------------------------------------------------------------

ENRICHMENT_SOURCE_LABELS: dict[str, str] = {
    "apollo": "Apollo.io",
    "hunter": "Hunter.io",
    "proxycurl": "Proxycurl",
    "manual": "Manual",
}

# ------------------------------------------------------------------
# Lead source labels
# ------------------------------------------------------------------

LEAD_SOURCE_LABELS: dict[str, str] = {
    "CSV_UPLOAD": "CSV Upload",
    "GMT": "GMT Directory",
    "JEWELRY_BOOK": "Jewelry Book",
    "HILL_LIST": "Hill List",
    "RAPID_LIST": "Rapid List",
    "MANUAL": "Manual Entry",
}

# ------------------------------------------------------------------
# Polling config
# ------------------------------------------------------------------

POLL_INTERVAL_SECONDS = 2
POLL_MAX_ATTEMPTS = 60  # 2 min timeout

# ------------------------------------------------------------------
# Pagination defaults
# ------------------------------------------------------------------

DEFAULT_PAGE_SIZE = 20

# ------------------------------------------------------------------
# Date/time format
# ------------------------------------------------------------------

DATETIME_FORMAT = "%d %b %Y, %H:%M"
DATE_FORMAT = "%d %b %Y"
