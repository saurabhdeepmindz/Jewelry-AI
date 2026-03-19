"""WF-007 — CSV Lead Upload screen.

States:
  1. SELECT   — file uploader widget (no file chosen yet)
  2. UPLOADING — file chosen, POST /api/v1/leads/upload in progress
  3. PROCESSING — polling GET /api/v1/leads/jobs/{job_id} every 2 s
  4. COMPLETED — results grid (created / skipped_duplicates / skipped_invalid / errors)
  5. FAILED    — error banner + retry button

Session-state keys used (all prefixed 'upload_'):
  upload_job_id        : str | None
  upload_state         : "select" | "uploading" | "processing" | "completed" | "failed"
  upload_result        : dict | None   (final job status payload)
  upload_error         : str | None    (user-facing error message)
  upload_poll_count    : int           (safety counter for the polling loop)
"""
from __future__ import annotations

import time
from typing import Any

import streamlit as st

from src.ui.api_client import APIError, get_api_client
from src.ui.components.error_banner import show_error, show_info, show_success
from src.ui.utils.constants import POLL_INTERVAL_SECONDS, POLL_MAX_ATTEMPTS

# ------------------------------------------------------------------
# Session-state initialisation
# ------------------------------------------------------------------

def _init_state() -> None:
    defaults: dict[str, object] = {
        "upload_job_id": None,
        "upload_state": "select",
        "upload_result": None,
        "upload_error": None,
        "upload_poll_count": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset() -> None:
    """Reset all upload state to initial values."""
    st.session_state["upload_job_id"] = None
    st.session_state["upload_state"] = "select"
    st.session_state["upload_result"] = None
    st.session_state["upload_error"] = None
    st.session_state["upload_poll_count"] = 0


# ------------------------------------------------------------------
# Sub-screens
# ------------------------------------------------------------------

def _render_select() -> None:
    """State 1 — file chooser."""
    st.subheader("Upload Lead CSV")
    show_info(
        "Upload a CSV file exported from your trade directory. "
        "Required columns: `company_name`, `domain`. "
        "Optional: `website`, `industry`, `employee_count`, `source`."
    )

    uploaded = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help="UTF-8 encoded CSV, max 10 MB",
        key="upload_file_widget",
    )

    if uploaded is not None:
        col_submit, col_cancel = st.columns([1, 4])
        with col_submit:
            if st.button("Upload", type="primary", use_container_width=True):
                _handle_upload(uploaded)
        with col_cancel:
            if st.button("Clear", use_container_width=True):
                st.rerun()


def _handle_upload(uploaded: Any) -> None:
    """Submit the file to the backend and transition to UPLOADING."""
    st.session_state["upload_state"] = "uploading"
    client = get_api_client()

    with st.spinner("Uploading…"):
        try:
            csv_bytes: bytes = uploaded.read()
            filename: str = getattr(uploaded, "name", "leads.csv")
            response = client.upload_leads_csv(csv_bytes, filename)
            job_id: str = response["job_id"]
            st.session_state["upload_job_id"] = job_id
            st.session_state["upload_state"] = "processing"
            st.session_state["upload_poll_count"] = 0
        except APIError as exc:
            st.session_state["upload_state"] = "failed"
            st.session_state["upload_error"] = f"HTTP {exc.status_code}: {exc.detail}"
        except Exception as exc:
            st.session_state["upload_state"] = "failed"
            st.session_state["upload_error"] = str(exc)

    st.rerun()


def _render_processing() -> None:
    """State 3 — polling loop with indeterminate progress bar (annotation A7)."""
    job_id: str = st.session_state["upload_job_id"]
    poll_count: int = st.session_state["upload_poll_count"]

    placeholder = st.empty()

    with placeholder.container():
        st.subheader("Processing…")
        st.caption(f"Job ID: `{job_id}`")
        progress_bar = st.progress(0, text="Importing leads, please wait…")

    # Safety gate: if already exceeded max attempts, mark failed
    if poll_count >= POLL_MAX_ATTEMPTS:
        st.session_state["upload_state"] = "failed"
        st.session_state["upload_error"] = "Job timed out after 2 minutes with no response."
        st.rerun()
        return

    client = get_api_client()
    try:
        status_data = client.get_ingestion_job_status(job_id)
    except APIError as exc:
        st.session_state["upload_state"] = "failed"
        st.session_state["upload_error"] = f"HTTP {exc.status_code}: {exc.detail}"
        st.rerun()
        return
    except Exception as exc:
        st.session_state["upload_state"] = "failed"
        st.session_state["upload_error"] = str(exc)
        st.rerun()
        return

    job_status: str = status_data.get("status", "processing")

    if job_status == "completed":
        st.session_state["upload_state"] = "completed"
        st.session_state["upload_result"] = status_data
        progress_bar.progress(100, text="Done!")
        placeholder.empty()
        st.rerun()
        return

    if job_status == "failed":
        st.session_state["upload_state"] = "failed"
        st.session_state["upload_error"] = status_data.get("error", "Unknown error")
        placeholder.empty()
        st.rerun()
        return

    # Still processing — update progress bar and wait
    pct = min(5 + poll_count * 2, 90)  # pseudo-progress 5 → 90%
    elapsed = poll_count * POLL_INTERVAL_SECONDS
    progress_bar.progress(pct, text=f"Importing leads, please wait... ({elapsed}s)")
    st.session_state["upload_poll_count"] = poll_count + 1

    time.sleep(POLL_INTERVAL_SECONDS)
    st.rerun()


def _render_completed() -> None:
    """State 4 — results summary grid (annotation A10)."""
    result: dict[str, Any] = st.session_state["upload_result"]

    show_success("Upload complete!")
    st.caption(f"Job ID: `{result.get('job_id', '—')}`")

    # Results metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Created", result.get("created", 0))
    with col2:
        st.metric("Skipped (duplicates)", result.get("skipped_duplicates", 0))
    with col3:
        st.metric("Skipped (invalid)", result.get("skipped_invalid", 0))
    with col4:
        errors = result.get("errors", 0)
        delta = None if errors == 0 else f"-{errors}"
        st.metric("Errors", errors, delta=delta, delta_color="inverse")

    st.divider()

    col_new, col_view = st.columns([1, 4])
    with col_new:
        if st.button("Upload another file", type="primary", use_container_width=True):
            _reset()
            st.rerun()
    with col_view:
        if st.button("View leads list", use_container_width=True):
            # Navigate to lead detail page (user can select from leads list)
            st.switch_page("src/ui/pages/lead_detail.py")


def _render_failed() -> None:
    """State 5 — error banner + retry (annotation A12)."""
    error_msg: str = st.session_state.get("upload_error", "An unknown error occurred.")

    show_error("Upload failed", detail=error_msg)

    st.divider()

    if st.button("Try again", type="primary"):
        _reset()
        st.rerun()


# ------------------------------------------------------------------
# Page entry point
# ------------------------------------------------------------------

def main() -> None:
    _init_state()

    st.title("💎 Upload Leads")
    st.caption("Import a CSV file of buyer prospects from your trade directory.")
    st.divider()

    state: str = st.session_state["upload_state"]

    if state == "select":
        _render_select()
    elif state in ("uploading", "processing"):
        _render_processing()
    elif state == "completed":
        _render_completed()
    elif state == "failed":
        _render_failed()
    else:
        _reset()
        st.rerun()


main()
