"""WF-Outreach — Outreach Review Page.

Displays outreach messages in 'pending_review' status for human approval or rejection.

Layout:
  - Title: "Outreach Review"
  - Fetch messages with status "pending_review" from the API
  - Display as a table: Company (lead_id), Contact (contact_id), Subject, Step, Created
  - Clicking a row expands to show full email body
  - Two action buttons: "Approve & Send" and "Reject" (with reason input)
  - Success/error banners via error_banner component

Session-state keys (all prefixed 'outreach_'):
  outreach_selected_id       : str | None — currently selected message ID
  outreach_reject_input      : str        — rejection reason text
  outreach_action_result     : str | None — last action result message
  outreach_action_error      : str | None — last action error message
"""
from __future__ import annotations

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


# ------------------------------------------------------------------
# Session-state initialisation
# ------------------------------------------------------------------

def _init_state() -> None:
    defaults: dict[str, object] = {
        "outreach_selected_id": None,
        "outreach_reject_input": "",
        "outreach_action_result": None,
        "outreach_action_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _clear_action_state() -> None:
    st.session_state["outreach_action_result"] = None
    st.session_state["outreach_action_error"] = None


# ------------------------------------------------------------------
# API helpers
# ------------------------------------------------------------------

def _fetch_pending_messages() -> list[dict[str, Any]]:
    """Fetch messages with status=pending_review from the backend."""
    client = get_api_client()
    try:
        response = client._get("/api/v1/outreach/messages", params={"status": "pending_review", "page_size": 50})
        data = response.get("data", [])
        if isinstance(data, list):
            return data
        return []
    except APIError as exc:
        show_api_error(exc)
        return []
    except Exception as exc:
        show_error("Could not load outreach messages", detail=str(exc))
        return []


def _fetch_message(message_id: str) -> dict[str, Any] | None:
    """Fetch a single message by ID."""
    client = get_api_client()
    try:
        response = client._get(f"/api/v1/outreach/messages/{message_id}")
        return response.get("data")
    except APIError as exc:
        show_api_error(exc)
        return None
    except Exception as exc:
        show_error("Could not load message", detail=str(exc))
        return None


def _approve_message(message_id: str) -> bool:
    """Call the approve endpoint. Returns True on success."""
    client = get_api_client()
    try:
        client._post(f"/api/v1/outreach/messages/{message_id}/approve")
        return True
    except APIError as exc:
        st.session_state["outreach_action_error"] = f"HTTP {exc.status_code}: {exc.detail}"
        return False
    except Exception as exc:
        st.session_state["outreach_action_error"] = str(exc)
        return False


def _reject_message(message_id: str, reason: str) -> bool:
    """Call the reject endpoint with a reason. Returns True on success."""
    client = get_api_client()
    try:
        client._post(
            f"/api/v1/outreach/messages/{message_id}/reject",
            json={"reason": reason},
        )
        return True
    except APIError as exc:
        st.session_state["outreach_action_error"] = f"HTTP {exc.status_code}: {exc.detail}"
        return False
    except Exception as exc:
        st.session_state["outreach_action_error"] = str(exc)
        return False


# ------------------------------------------------------------------
# Table rendering
# ------------------------------------------------------------------

def _render_messages_table(messages: list[dict[str, Any]]) -> None:
    """Render the messages list and handle row selection."""
    if not messages:
        show_info("No messages are pending review at this time.")
        return

    rows = []
    for m in messages:
        rows.append({
            "ID": m.get("id", ""),
            "Lead ID": str(m.get("lead_id", ""))[:8] + "...",
            "Contact ID": str(m.get("contact_id", "") or "—")[:8] + ("..." if m.get("contact_id") else ""),
            "Subject": m.get("subject") or "(no subject)",
            "Step": m.get("sequence_step", 1),
            "Created": m.get("created_at", "")[:19].replace("T", " ") if m.get("created_at") else "—",
        })

    # Display table
    st.dataframe(
        [{k: v for k, v in row.items() if k != "ID"} for row in rows],
        use_container_width=True,
        hide_index=True,
    )

    # Message selector
    message_ids = [m.get("id", "") for m in messages]
    subjects = [m.get("subject") or f"(no subject) — {m.get('id', '')[:8]}" for m in messages]
    options = dict(zip(subjects, message_ids))

    selected_label = st.selectbox(
        "Select a message to review",
        options=list(options.keys()),
        key="outreach_message_select",
        index=None,
        placeholder="Choose a message...",
    )

    if selected_label and options.get(selected_label):
        st.session_state["outreach_selected_id"] = options[selected_label]
        _clear_action_state()


# ------------------------------------------------------------------
# Message detail + actions
# ------------------------------------------------------------------

def _render_message_detail(message_id: str) -> None:
    """Show the full email body and approve/reject actions."""
    message = _fetch_message(message_id)
    if message is None:
        return

    st.divider()
    st.subheader("Email Preview")

    col_meta, col_actions = st.columns([3, 1])

    with col_meta:
        st.write(f"**Subject:** {message.get('subject') or '(no subject)'}")
        st.write(f"**Lead ID:** `{message.get('lead_id')}`")
        st.write(f"**Contact ID:** `{message.get('contact_id') or 'N/A'}`")
        st.write(f"**Channel:** {message.get('channel', 'email').upper()}")
        st.write(f"**Sequence Step:** {message.get('sequence_step', 1)}")
        st.write(f"**Status:** {message.get('status', '')}")

    with col_actions:
        st.write("**Actions**")

        # Approve button
        if st.button("Approve & Send", type="primary", use_container_width=True):
            _clear_action_state()
            success = _approve_message(message_id)
            if success:
                st.session_state["outreach_action_result"] = "Message approved and sent successfully."
                st.session_state["outreach_selected_id"] = None
            st.rerun()

        # Reject section
        st.write("")
        reject_reason = st.text_area(
            "Rejection reason",
            key="outreach_reject_input_field",
            placeholder="Enter reason for rejection...",
            height=80,
        )
        if st.button("Reject", type="secondary", use_container_width=True):
            if not reject_reason.strip():
                show_warning("Please enter a rejection reason before rejecting.")
            else:
                _clear_action_state()
                success = _reject_message(message_id, reject_reason.strip())
                if success:
                    st.session_state["outreach_action_result"] = "Message rejected."
                    st.session_state["outreach_selected_id"] = None
                st.rerun()

    # Email body preview
    st.write("**Email Body:**")
    body = message.get("body", "")
    if body:
        st.components.v1.html(body, height=400, scrolling=True)
    else:
        show_info("No email body available.")

    # Back button
    if st.button("← Back to list"):
        st.session_state["outreach_selected_id"] = None
        _clear_action_state()
        st.rerun()


# ------------------------------------------------------------------
# Main page
# ------------------------------------------------------------------

def main() -> None:
    _init_state()

    st.title("Outreach Review")
    st.caption("Review AI-generated outreach emails before they are sent to prospects.")

    # Show action result banners
    action_result: str | None = st.session_state.get("outreach_action_result")
    action_error: str | None = st.session_state.get("outreach_action_error")

    if action_result:
        show_success(action_result)
    if action_error:
        show_error("Action failed", detail=action_error)

    selected_id: str | None = st.session_state.get("outreach_selected_id")

    if selected_id:
        # Show detail view for selected message
        _render_message_detail(selected_id)
    else:
        # Show the pending review list
        col_title, col_refresh = st.columns([4, 1])
        with col_title:
            st.subheader("Pending Review")
        with col_refresh:
            if st.button("Refresh", use_container_width=True):
                _clear_action_state()
                st.rerun()

        messages = _fetch_pending_messages()
        _render_messages_table(messages)

        # Trigger detail view if a message was just selected
        new_selected: str | None = st.session_state.get("outreach_selected_id")
        if new_selected:
            st.rerun()


main()
