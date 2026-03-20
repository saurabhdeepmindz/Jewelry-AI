# Synthetic Data Rules — Demo & Testing

## Purpose

Synthetic data serves two distinct purposes:
1. **Demo data** — Realistic, curated datasets for client demonstrations (POC)
2. **Test fixtures** — Deterministic, minimal datasets for automated tests

These are DIFFERENT and must NEVER be mixed. Demo data lives in `scripts/seed_demo_data.py`. Test fixtures live in `tests/factories/`.

---

## Demo Data Requirements

### Characteristics of Good Demo Data

- **Realistic** — Company names, contact names, and email patterns match real jewelry industry profiles
- **Diverse** — Multiple countries, lead sources, statuses, match outcomes
- **Curated** — Pre-selected to tell a compelling story in the demo flow
- **Deterministic** — Same seed script produces identical data every time
- **Safe** — No real company names, no real email addresses, no real phone numbers

### Volume for POC Demo

| Entity | Count | Notes |
|---|---|---|
| Inventory items | 25 | 5 shapes × 5 carat ranges, mix of GIA/IGI cert |
| Leads | 50 | Mix of sources, statuses, match outcomes |
| Eligible leads (matched) | 20 | Ready for enrichment demo |
| Enriched contacts | 10 | With realistic names, titles, verified emails |
| Outreach drafts | 5 | 2 sent, 2 draft pending review, 1 opened |
| CRM activity events | ~150 | Full timeline for 10 leads |

---

## Demo Company Name Patterns

Use fictional but realistic jewelry trade company names:

```python
# scripts/seed_demo_data.py — company name patterns

DEMO_COMPANIES = [
    # USA
    {"company": "Pristine Diamonds LLC", "city": "New York", "country": "USA", "domain": "pristinediamonds.example.com"},
    {"company": "Luxe Gem Trading Co.", "city": "Los Angeles", "country": "USA", "domain": "luxegemtrading.example.com"},
    {"company": "Madison Avenue Jewelers", "city": "New York", "country": "USA", "domain": "madisonjewelers.example.com"},
    {"company": "Pacific Gems International", "city": "San Francisco", "country": "USA", "domain": "pacificgems.example.com"},
    # Europe
    {"company": "Antwerp Diamond Exchange BV", "city": "Antwerp", "country": "Belgium", "domain": "adexchange.example.com"},
    {"company": "Milano Gioielleria SRL", "city": "Milan", "country": "Italy", "domain": "milanogioielli.example.com"},
    {"company": "London Fine Gems Ltd", "city": "London", "country": "UK", "domain": "londonfingems.example.com"},
    # Asia
    {"company": "Mumbai Diamond Traders Pvt Ltd", "city": "Mumbai", "country": "India", "domain": "mumbaidiamond.example.com"},
    {"company": "Hong Kong Gem House Ltd", "city": "Hong Kong", "country": "HK", "domain": "hkgemhouse.example.com"},
    {"company": "Tokyo Diamond Trading KK", "city": "Tokyo", "country": "Japan", "domain": "tokyodiamond.example.com"},
]
```

**Rules for demo company names:**
- Always append `.example.com` to domains — RFC 2606 reserved, never routes to real site
- Company names must be clearly fictional (not real registered businesses)
- Use `.example.com`, `.test`, or `.invalid` TLDs — never `.com`, `.co`, `.io` alone

---

## Demo Contact Name Patterns

```python
DEMO_CONTACTS = [
    {"name": "Sarah Mitchell", "title": "Head Buyer", "email": "s.mitchell@pristinediamonds.example.com"},
    {"name": "James Chen", "title": "Procurement Director", "email": "j.chen@pacificgems.example.com"},
    {"name": "Elena Rossi", "title": "Senior Gemologist", "email": "e.rossi@milanogioielli.example.com"},
    {"name": "Rahul Kapoor", "title": "Diamond Sourcing Manager", "email": "r.kapoor@mumbaidiamond.example.com"},
    {"name": "David Goldstein", "title": "VP Procurement", "email": "d.goldstein@luxegemtrading.example.com"},
]
```

**Rules for demo contacts:**
- Always use `.example.com` email domains — never real email addresses
- Phone numbers: use `+1-555-xxx-xxxx` format (555 is reserved for fictional use in USA)
- LinkedIn URLs: use `https://linkedin.example.com/in/` prefix
- Names should represent gender/cultural diversity matching the company's geography

---

## Demo Inventory Data

```python
DEMO_INVENTORY = [
    # Round Brilliant Cut — high match probability
    {"sku": "DEMO-RBC-050-G-VS1", "shape": "RBC", "carat_weight": 0.50, "color_grade": "G", "clarity_grade": "VS1", "cut_grade": "Excellent", "certification": "GIA", "price_usd": 1200},
    {"sku": "DEMO-RBC-102-D-IF",  "shape": "RBC", "carat_weight": 1.02, "color_grade": "D", "clarity_grade": "IF",  "cut_grade": "Excellent", "certification": "GIA", "price_usd": 8500},
    {"sku": "DEMO-RBC-152-F-VVS2","shape": "RBC", "carat_weight": 1.52, "color_grade": "F", "clarity_grade": "VVS2","cut_grade": "Very Good","certification": "GIA", "price_usd": 12000},
    # Princess Cut
    {"sku": "DEMO-PRI-075-H-VS2", "shape": "princess", "carat_weight": 0.75, "color_grade": "H", "clarity_grade": "VS2", "cut_grade": "Excellent", "certification": "IGI", "price_usd": 2800},
    # Oval
    {"sku": "DEMO-OVL-200-E-VVS1","shape": "oval",    "carat_weight": 2.00, "color_grade": "E", "clarity_grade": "VVS1","cut_grade": "Excellent","certification": "GIA", "price_usd": 22000},
]
```

---

## Demo Script — Seed Procedure

```python
# scripts/seed_demo_data.py

"""
Seed demo data for Jewelry AI POC demonstration.

Run with: python scripts/seed_demo_data.py
Safe to run multiple times — uses upsert to prevent duplicates.

WARNING: Only run against development/staging databases.
         Never run against production.
"""

import asyncio
import sys

async def seed_all() -> None:
    """Seed complete demo dataset in dependency order."""

    # Safety check — never seed production
    if settings.APP_ENV == "production":
        print("ERROR: Refusing to seed demo data in production environment.")
        sys.exit(1)

    print("Seeding demo data for Jewelry AI POC...")
    await seed_inventory()
    await seed_leads()
    await seed_contacts()
    await seed_outreach_messages()
    await seed_crm_activity()
    print("Done. Demo data ready.")

if __name__ == "__main__":
    asyncio.run(seed_all())
```

**Rules:**
- Safety guard: check `APP_ENV != "production"` before seeding — hard stop if production
- Use `INSERT ... ON CONFLICT DO NOTHING` — safe to re-run
- All seed data uses `DEMO-` SKU prefix and `.example.com` domains — easily identifiable
- Document the expected demo flow the seed data supports

---

## Demo Lead Statuses Distribution

Pre-seed leads at different pipeline stages to showcase the full funnel in demos:

| Status | Count | Purpose in Demo |
|---|---|---|
| `ingested` (not yet matched) | 10 | Show "leads waiting to be processed" |
| `matched` (eligible) | 8 | Show inventory matching result |
| `enriched` (contact found) | 12 | Show contact enrichment result |
| `contacted` | 12 | Show outreach sent |
| `responded` | 5 | Show positive engagement |
| `not_eligible` (match miss) | 3 | Show system correctly filtering |

---

## Test Factory Rules (Automated Tests)

Test factories are separate from demo seed data — they generate minimal, deterministic data for automated tests only.

```python
# tests/factories/lead_factory.py

import uuid
from datetime import datetime, timezone
from src.domain.lead import Lead, LeadStatus, MatchStatus


def build_lead(**overrides) -> Lead:
    """
    Build a minimal valid Lead domain object for testing.

    All fields have safe defaults. Override only what the test cares about.

    Args:
        **overrides: Any Lead field to override from defaults.

    Returns:
        Lead: A valid Lead domain object with test defaults.
    """
    defaults = {
        "id": uuid.uuid4(),
        "company_name": "Test Company Ltd",
        "domain": "testcompany.example.com",
        "country": "USA",
        "source": "manual",
        "status": LeadStatus.INGESTED,
        "match_status": MatchStatus.PENDING,
        "score": None,
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    return Lead(**{**defaults, **overrides})


def build_eligible_lead(**overrides) -> Lead:
    """Build a Lead already marked as eligible — skips matching step in tests."""
    return build_lead(status=LeadStatus.MATCHED, match_status=MatchStatus.ELIGIBLE, **overrides)


def build_enriched_lead(**overrides) -> Lead:
    """Build a Lead in enriched state — skips matching and enrichment in tests."""
    return build_lead(status=LeadStatus.ENRICHED, match_status=MatchStatus.ELIGIBLE, **overrides)
```

**Test factory rules:**
- Factory functions return domain objects, not DB models
- All defaults use `.example.com` domains and clearly test-flavored names
- Never use real company names, emails, or phone numbers even in tests
- Factory functions accept `**overrides` — test only the specific field being tested

---

## Data Anonymization Rules

When using any real-world data as inspiration for synthetic data:
- Replace all company names with fictional variants
- Replace all personal names with random realistic names
- Replace all emails with `@example.com` variants
- Replace all phone numbers with `+1-555-` format
- Replace all LinkedIn URLs with `linkedin.example.com`
- Randomize exact numeric values (carat, price) while keeping plausible ranges

---

## Do Not

- Use real company names from trade directories in demo or test data
- Use real personal names of individuals (even publicly known buyers)
- Use `.com`, `.co`, or real TLD email addresses in ANY seed or test data
- Commit demo seed data with real API responses (Apollo, Hunter outputs)
- Mix demo seed scripts with test fixtures
- Run `seed_demo_data.py` without the production environment guard
