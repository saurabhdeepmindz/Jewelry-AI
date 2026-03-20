# UI Wireframe Rules — Jewelry AI Platform

> **Extends:** `best-practices_rule_set_code/docs/rules/ui-wireframe-rules.md`
> **Adds:** Jewelry AI screen catalog, actor-screen mapping, API field bindings, Streamlit implementation notes

---

## Screen Catalog — Jewelry AI

| ID | Screen Name | Epic | Stories | Actors | Status |
|---|---|---|---|---|---|
| WF-000 | Screen Index | — | — | All | ✅ Created |
| WF-001 | Login | EPIC-11 | US-039 | All (public) | ✅ Created |
| WF-002 | Lead Pipeline Dashboard | EPIC-09 | US-032 | rep, manager, admin | ✅ Created |
| WF-003 | Lead Detail View | EPIC-09 | US-033 | rep, manager, admin | ✅ Created |
| WF-004 | Outreach Review Queue | EPIC-09 | US-034 | manager, admin | ✅ Created |
| WF-005 | Analytics Funnel | EPIC-09 | US-035 | manager, admin (rep: own data) | ✅ Created |
| WF-006 | Admin — User Management | EPIC-11 | US-041 | admin | ✅ Created |
| WF-007 | CSV Upload | EPIC-02 | US-006 | rep, manager, admin | ✅ Created |

---

## Actor → Screen Access Matrix

| Screen | admin | manager | rep | system |
|---|---|---|---|---|
| Login | ✅ | ✅ | ✅ | — |
| Lead Pipeline Dashboard | ✅ (all) | ✅ (all) | ✅ (own only) | — |
| Lead Detail View | ✅ | ✅ | ✅ (own only) | — |
| Outreach Review Queue | ✅ | ✅ | ❌ | — |
| Analytics Funnel | ✅ (all) | ✅ (all) | ✅ (own only) | — |
| Admin — User Management | ✅ | ❌ | ❌ | — |
| CSV Upload | ✅ | ✅ | ✅ | — |

---

## Jewelry AI Colour Palette (Grayscale Wireframe)

Following generic rules — grayscale only. The production Streamlit app will use:
- Streamlit default dark/light theme
- Plotly charts with greyscale for wireframes, actual colour in production

Wireframe annotation colour scheme:
- `#212121` — headers, primary text
- `#424242` — primary action buttons, table headers
- `#757575` — secondary text, labels, annotations
- `#bdbdbd` — borders, dividers
- `#e0e0e0` — background of table headers, disabled states
- `#f5f5f5` — page background, sidebar background
- `#ffffff` — card/panel backgrounds

---

## API Field Bindings — Per Screen

### WF-002: Lead Pipeline Dashboard
| UI Element | API Source | Endpoint |
|---|---|---|
| Company Name | `Lead.company_name` | `GET /api/v1/leads` |
| Domain | `Lead.domain` | `GET /api/v1/leads` |
| Country | `Lead.country` | `GET /api/v1/leads` |
| Status badge | `Lead.status` (enum) | `GET /api/v1/leads` |
| Score | `Lead.score` (nullable) | `GET /api/v1/leads` |
| Source | `Lead.source` (enum) | `GET /api/v1/leads` |
| Match Status | `Lead.match_status` | `GET /api/v1/leads` |
| Status filter | → `?status=` query param | — |
| Pagination | `total`, `page`, `limit` in response | — |

### WF-003: Lead Detail View
| UI Element | API Source | Endpoint |
|---|---|---|
| Company info | `Lead.*` | `GET /api/v1/leads/{lead_id}` |
| Contacts | `Contact.*` | `GET /api/v1/leads/{lead_id}/contacts` |
| Matched inventory | `Match.*` + `Inventory.*` | `GET /api/v1/leads/{lead_id}/matches` |
| CRM Timeline | `CRMActivity.*` (newest first) | `GET /api/v1/leads/{lead_id}/activities` |
| Activity timestamp | `CRMActivity.created_at` (relative) | — |

### WF-004: Outreach Review Queue
| UI Element | API Source | Endpoint |
|---|---|---|
| Lead company | `OutreachMessage.lead.company_name` | `GET /api/v1/outreach?status=pending_review` |
| Contact name | `OutreachMessage.contact.name` | Same |
| Email subject | `OutreachMessage.subject` | Same |
| Email body | `OutreachMessage.body` | Same |
| Sequence step | `OutreachMessage.sequence_step` | Same |
| Approve action | → `POST /api/v1/outreach/{id}/approve` | — |
| Reject action | → `POST /api/v1/outreach/{id}/reject` + `{reason}` | — |

### WF-005: Analytics Funnel
| UI Element | API Source | Endpoint |
|---|---|---|
| Stage counts | `{stage: count}` object | `GET /api/v1/analytics/funnel` |
| Date range filter | → `?from=&to=` query params | — |

### WF-006: Admin — User Management
| UI Element | API Source | Endpoint |
|---|---|---|
| Users table | `User.*` | `GET /api/v1/admin/users` |
| Create user | `{username, email, password, role}` | `POST /api/v1/admin/users` |
| Deactivate user | `{is_active: false}` | `PATCH /api/v1/admin/users/{id}` |

---

## Streamlit Implementation Notes

These wireframes describe the **visual layout** of Streamlit pages. When implementing:

- Each wireframe screen maps to one file in `src/ui/pages/`
- Navigation bar is implemented in `src/ui/app.py` (Streamlit `st.sidebar`)
- Charts use Plotly — the wireframe shows placeholder boxes with chart type annotation
- All form validation shown in wireframes is **UI-level only** — backend also validates
- Role enforcement: check `st.session_state["role"]` to show/hide elements
- Empty states are `st.info("...")` calls
- Toast notifications are `st.success()` / `st.error()` calls

---

## Wireframe Storage Location

```
project-specific-guidelines/docs/wireframes/
├── WF-000-screen-index.html
├── WF-001-login.html
├── WF-002-lead-pipeline-dashboard.html
├── WF-003-lead-detail-view.html
├── WF-004-outreach-review-queue.html
├── WF-005-analytics-funnel.html
├── WF-006-admin-users.html
└── WF-007-csv-upload.html
```

---

## Definition of Done — Jewelry AI Wireframes

In addition to the generic DoD, Jewelry AI wireframes must:

- [ ] Show correct actor access badge (rep / manager / admin)
- [ ] Every data field annotated with its API source field name
- [ ] Empty state shown for all lists and charts
- [ ] Business rules visible (e.g., "Outreach requires HUMAN_REVIEW_REQUIRED=true to show here")
- [ ] Streamlit-specific implementation note in header comment
- [ ] Navigation sidebar reflects Streamlit sidebar pattern
- [ ] CRM Activity timeline shown newest-first per US-033 AC1
- [ ] Manager-only screens show redirect message for rep access attempt
