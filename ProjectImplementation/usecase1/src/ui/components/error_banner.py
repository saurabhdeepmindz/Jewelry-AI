"""Shared UI components for displaying error, warning, and success banners.

Usage:
    from src.ui.components.error_banner import show_error, show_warning, show_success

    show_error("Failed to upload file: connection timeout")
    show_warning("No inventory matches found for this lead")
    show_success("CSV uploaded — 42 leads created")
"""
from __future__ import annotations

import streamlit as st

from src.ui.api_client import APIError


def show_error(message: str, *, detail: str | None = None) -> None:
    """Render a red error banner.

    Parameters
    ----------
    message:
        Primary error text shown to the user.
    detail:
        Optional technical detail (e.g. HTTP status) shown in an expander.
    """
    if detail:
        with st.expander(f"❌ {message}", expanded=True):
            st.code(detail, language="text")
    else:
        st.error(f"❌ {message}")


def show_api_error(exc: APIError) -> None:
    """Render a structured error banner from an APIError exception."""
    if exc.status_code == 404:
        show_warning("Resource not found.")
    elif exc.status_code == 422:
        show_error("Validation error — check your input.", detail=exc.detail)
    elif exc.status_code >= 500:
        show_error(
            "Server error — please try again later.",
            detail=f"HTTP {exc.status_code}: {exc.detail}",
        )
    else:
        show_error(f"Request failed (HTTP {exc.status_code})", detail=exc.detail)


def show_warning(message: str) -> None:
    """Render an amber warning banner."""
    st.warning(f"⚠️ {message}")


def show_success(message: str) -> None:
    """Render a green success banner."""
    st.success(f"✅ {message}")


def show_info(message: str) -> None:
    """Render a blue info banner."""
    st.info(f"[i] {message}")
