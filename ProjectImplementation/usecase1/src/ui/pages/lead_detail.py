"""WF-003 — Lead Detail View.

Layout (two-column):
  LEFT COLUMN:
    - Lead header card: company name, domain, status badge, source
    - Lead score (colour-coded)
    - Company info: website, industry, employee count, created date
    - Contacts table (with Enrich button if empty)
    - Enrichment polling overlay when an enrichment job is in flight

  RIGHT COLUMN:
    - Inventory matches table (carat always 2 dp)
    - CRM activity timeline (newest-first)

Navigation:
  Accessed from the sidebar. Lead ID is passed via st.query_params["lead_id"].
  If no lead_id is present, a search/select input is shown instead.

Session-state keys (all prefixed 'detail_'):
  detail_lead_id              : str | None
  detail_enrich_job_id        : str | None
  detail_enrich_state         : "idle" | "polling" | "done" | "failed"
  detail_enrich_poll_count    : int
  detail_enrich_error         : str | None
"""
from __future__ import annotations

import time
from typing import Any

import streamlit as st

from src.ui.api_client import APIError, get_api_client
from src.ui.components.error_banner import (
    show_api_error,
    show_error,
    show_info,
    show_success,
    show_warning,
)
from src.ui.utils.constants import POLL_INTERVAL_SECONDS, POLL_MAX_ATTEMPTS
from src.ui.utils.formatters import (
    format_carat,
    format_currency,
    format_datetime,
    format_enrichment_source,
    format_lead_source,
    format_score,
    relative_time,
    score_color,
    status_badge,
)

# ------------------------------------------------------------------
# Session-state initialisation
# ------------------------------------------------------------------

def _init_state() -> None:
    defaults: dict[str, object] = {
        "detail_lead_id": None,
        "detail_enrich_job_id": None,
        "detail_enrich_state": "idle",
        "detail_enrich_poll_count": 0,
        "detail_enrich_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset_enrich() -> None:
    st.session_state["detail_enrich_job_id"] = None
    st.session_state["detail_enrich_state"] = "idle"
    st.session_state["detail_enrich_poll_count"] = 0
    st.session_state["detail_enrich_error"] = None


# ------------------------------------------------------------------
# Lead selector (when no lead_id in query params)
# ------------------------------------------------------------------

def _render_lead_selector() -> None:
    """Show a text input for entering a lead UUID directly."""
    st.subheader("Select a Lead")
    show_info("Enter a Lead ID to view its detail, or navigate here from the leads list.")

    lead_id_input = st.text_input(
        "Lead ID (UUID)",
        placeholder="e.g. 3fa85f64-5717-4562-b3fc-2c963f66afa6",
        key="detail_lead_id_input",
    )

    if st.button("Load Lead", type="primary"):
        if lead_id_input.strip():
            st.query_params["lead_id"] = lead_id_input.strip()
            st.session_state["detail_lead_id"] = lead_id_input.strip()
            st.rerun()
        else:
            show_warning("Please enter a valid Lead ID.")


# ------------------------------------------------------------------
# Lead header card
# ------------------------------------------------------------------

def _render_lead_header(lead: dict[str, Any]) -> None:
    badge = status_badge(lead.get("status", ""))
    score: float | None = lead.get("score")
    color = score_color(score)

    header_col, score_col = st.columns([3, 1])
    with header_col:
        st.markdown(f"## {lead.get('company_name', 'Unknown Company')}")
        st.markdown(f"🌐 `{lead.get('domain', '—')}`&nbsp;&nbsp;|&nbsp;&nbsp;{badge}")
        src = format_lead_source(lead.get("source"))
        created = format_datetime(lead.get("created_at"))
        st.caption(f"Source: {src} &nbsp;·&nbsp; Ingested: {created}")
    with score_col:
        score_label = format_score(score)
        st.markdown(
            f"""
            <div style="
                background:{color};
                color:white;
                border-radius:12px;
                padding:16px 20px;
                text-align:center;
                margin-top:4px;
            ">
                <div style="font-size:11px;opacity:0.85;margin-bottom:4px;">LEAD SCORE</div>
                <div style="font-size:28px;font-weight:700;">{score_label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ------------------------------------------------------------------
# Company info panel
# ------------------------------------------------------------------

def _render_company_info(lead: dict[str, Any]) -> None:
    with st.expander("Company Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Website**", lead.get("website") or "—")
            st.write("**Industry**", lead.get("industry") or "—")
        with col2:
            st.write("**Employees**", lead.get("employee_count") or "—")
            st.write("**Last enriched**", format_datetime(lead.get("enriched_at")))


# ------------------------------------------------------------------
# Contacts panel
# ------------------------------------------------------------------

def _handle_enrich_trigger(lead_id: str) -> None:
    """Trigger enrichment for a lead and start polling."""
    client = get_api_client()
    try:
        response = client.trigger_enrichment(lead_id)
        st.session_state["detail_enrich_job_id"] = response["job_id"]
        st.session_state["detail_enrich_state"] = "polling"
        st.session_state["detail_enrich_poll_count"] = 0
    except APIError as exc:
        st.session_state["detail_enrich_state"] = "failed"
        st.session_state["detail_enrich_error"] = f"HTTP {exc.status_code}: {exc.detail}"
    except Exception as exc:
        st.session_state["detail_enrich_state"] = "failed"
        st.session_state["detail_enrich_error"] = str(exc)
    st.rerun()


def _render_enrichment_polling() -> None:
    """Inline polling overlay for enrichment job."""
    job_id: str = st.session_state["detail_enrich_job_id"]
    poll_count: int = st.session_state["detail_enrich_poll_count"]
    if poll_count >= POLL_MAX_ATTEMPTS:
        st.session_state["detail_enrich_state"] = "failed"
        st.session_state["detail_enrich_error"] = "Enrichment timed out."
        st.rerun()
        return

    st.info(f"⚙️ Enriching contacts… ({poll_count * POLL_INTERVAL_SECONDS}s)")
    progress = st.progress(min(5 + poll_count * 3, 90))

    client = get_api_client()
    try:
        status_data = client.get_enrichment_job_status(job_id)
    except APIError as exc:
        st.session_state["detail_enrich_state"] = "failed"
        st.session_state["detail_enrich_error"] = f"HTTP {exc.status_code}: {exc.detail}"
        st.rerun()
        return
    except Exception as exc:
        st.session_state["detail_enrich_state"] = "failed"
        st.session_state["detail_enrich_error"] = str(exc)
        st.rerun()
        return

    job_status: str = status_data.get("status", "processing")

    if job_status == "completed":
        progress.progress(100)
        st.session_state["detail_enrich_state"] = "done"
        st.rerun()
        return

    if job_status == "failed":
        st.session_state["detail_enrich_state"] = "failed"
        st.session_state["detail_enrich_error"] = status_data.get("error", "Enrichment failed.")
        st.rerun()
        return

    st.session_state["detail_enrich_poll_count"] = poll_count + 1
    time.sleep(POLL_INTERVAL_SECONDS)
    st.rerun()


def _render_contacts(lead_id: str, contacts: list[dict[str, Any]]) -> None:
    st.subheader("Contacts")

    enrich_state: str = st.session_state["detail_enrich_state"]
    if enrich_state == "polling":
        _render_enrichment_polling()
        return

    if enrich_state == "failed":
        err: str = st.session_state.get("detail_enrich_error", "Unknown error")
        show_error("Enrichment failed", detail=err)
        if st.button("Retry enrichment"):
            _reset_enrich()
            st.rerun()
        return

    if enrich_state == "done":
        show_success("Enrichment complete! Contact details updated.")

    if not contacts:
        show_info("No contacts enriched yet for this lead.")
        if st.button("Enrich Contacts", type="primary", key="enrich_btn"):
            _handle_enrich_trigger(lead_id)
    else:
        rows = [
            {
                "Name": c.get("full_name") or "—",
                "Title": c.get("title") or "—",
                "Email": c.get("email") or "—",
                "Phone": c.get("phone") or "—",
                "Source": format_enrichment_source(c.get("enrichment_source")),
                "Enriched": format_datetime(c.get("enriched_at")),
            }
            for c in contacts
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

        if st.button("Re-enrich Contacts", key="reenrich_btn"):
            _handle_enrich_trigger(lead_id)


# ------------------------------------------------------------------
# Inventory matches panel
# ------------------------------------------------------------------

def _render_matches(matches: list[dict[str, Any]]) -> None:
    st.subheader("Inventory Matches")

    if not matches:
        show_warning("No inventory matches for this lead. Lead is not yet eligible for outreach.")
        return

    rows = [
        {
            "Shape": m.get("shape") or "—",
            "Carat": format_carat(m.get("carat")),
            "Colour": m.get("colour") or "—",
            "Clarity": m.get("clarity") or "—",
            "Cut": m.get("cut") or "—",
            "Price": format_currency(m.get("price_usd")),
            "Status": status_badge(m.get("status", "")),
        }
        for m in matches
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)


# ------------------------------------------------------------------
# CRM activity timeline
# ------------------------------------------------------------------

def _render_activities(activities: list[dict[str, Any]]) -> None:
    st.subheader("CRM Activity")

    if not activities:
        show_info("No CRM activity recorded yet.")
        return

    # Newest-first (API should already return this order, but sort defensively)
    sorted_activities = sorted(
        activities,
        key=lambda a: a.get("created_at", ""),
        reverse=True,
    )

    for activity in sorted_activities:
        event_type: str = activity.get("event_type", "")
        note: str = activity.get("note") or ""
        when: str = relative_time(activity.get("created_at"))

        icon_map: dict[str, str] = {
            "lead_ingested": "📥",
            "lead_matched": "🔗",
            "lead_enriched": "🔍",
            "outreach_sent": "📧",
            "outreach_replied": "💬",
            "lead_status_changed": "🔄",
        }
        icon = icon_map.get(event_type, "•")
        label = event_type.replace("_", " ").title()

        with st.container():
            col_icon, col_body = st.columns([1, 12])
            with col_icon:
                icon_html = f"<div style='font-size:20px;padding-top:4px'>{icon}</div>"
                st.markdown(icon_html, unsafe_allow_html=True)
            with col_body:
                span = f"<span style='color:#888;font-size:12px'>{when}</span>"
                body_html = f"**{label}** &nbsp; {span}"
                st.markdown(body_html, unsafe_allow_html=True)
                if note:
                    st.caption(note)
        st.divider()


# ------------------------------------------------------------------
# Main page
# ------------------------------------------------------------------

def main() -> None:
    _init_state()

    st.title("💎 Lead Detail")

    # Resolve lead_id from query params or session state
    query_lead_id = st.query_params.get("lead_id")
    if query_lead_id:
        st.session_state["detail_lead_id"] = query_lead_id

    lead_id: str | None = st.session_state.get("detail_lead_id")
    if not lead_id:
        _render_lead_selector()
        return

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    client = get_api_client()

    try:
        lead = client.get_lead(lead_id)
    except APIError as exc:
        show_api_error(exc)
        if st.button("← Back"):
            st.session_state["detail_lead_id"] = None
            st.query_params.clear()
            st.rerun()
        return
    except Exception as exc:
        show_error("Could not load lead", detail=str(exc))
        return

    # Load contacts, matches, activities in parallel is not possible with
    # synchronous httpx, so load sequentially (all fast, cached by browser).
    try:
        contacts = client.get_lead_contacts(lead_id)
    except APIError:
        contacts = []

    try:
        matches = client.get_lead_matches(lead_id)
    except APIError:
        matches = []

    try:
        activities = client.get_lead_activities(lead_id)
    except APIError:
        activities = []

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    # Back button
    if st.button("← Back to search"):
        st.session_state["detail_lead_id"] = None
        st.query_params.clear()
        _reset_enrich()
        st.rerun()

    st.divider()
    _render_lead_header(lead)
    st.divider()

    left_col, right_col = st.columns([5, 5])

    with left_col:
        _render_company_info(lead)
        st.divider()
        _render_contacts(lead_id, contacts)

    with right_col:
        _render_matches(matches)
        st.divider()
        _render_activities(activities)


main()
