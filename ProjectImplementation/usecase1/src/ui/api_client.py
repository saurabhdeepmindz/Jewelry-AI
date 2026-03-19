"""Thin HTTP client wrapping the Jewelry AI FastAPI backend.

All Streamlit pages call the backend exclusively through this module.
No direct database, service, or repository imports are permitted in UI code.

Usage:
    from src.ui.api_client import get_api_client, APIError

    client = get_api_client()
    lead = client.get_lead(lead_id)
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx
import streamlit as st


class APIError(Exception):
    """Raised when the backend returns a non-2xx response or is unreachable."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class APIClient:
    """Synchronous HTTP client for the Jewelry AI FastAPI backend.

    All methods raise APIError on non-2xx responses.
    Timeout is 30 s for uploads (large CSV), 10 s for all other calls.
    """

    _DEFAULT_TIMEOUT = 10.0
    _UPLOAD_TIMEOUT = 30.0

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, path: str) -> str:
        return urljoin(self._base_url + "/", path.lstrip("/"))

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            detail: str = response.json().get("detail", response.text)
        except Exception:
            detail = response.text or str(response.status_code)
        raise APIError(status_code=response.status_code, detail=detail)

    def _get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        with httpx.Client(timeout=self._DEFAULT_TIMEOUT) as client:
            response = client.get(self._url(path), **kwargs)
        self._raise_for_status(response)
        result: dict[str, Any] = response.json()
        return result

    def _post(self, path: str, timeout: float | None = None, **kwargs: Any) -> dict[str, Any]:
        t = timeout or self._DEFAULT_TIMEOUT
        with httpx.Client(timeout=t) as client:
            response = client.post(self._url(path), **kwargs)
        self._raise_for_status(response)
        result: dict[str, Any] = response.json()
        return result

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health(self) -> dict[str, Any]:
        """GET /health — liveness check."""
        return self._get("/health")

    # ------------------------------------------------------------------
    # Lead Ingestion (Increment 1 / WF-007)
    # ------------------------------------------------------------------

    def upload_leads_csv(self, csv_bytes: bytes, filename: str) -> dict[str, Any]:
        """POST /api/v1/leads/upload — submit CSV file for async ingestion.

        Returns:
            {"job_id": str, "status": "queued"}
        """
        files = {"file": (filename, csv_bytes, "text/csv")}
        return self._post(
            "/api/v1/leads/upload",
            timeout=self._UPLOAD_TIMEOUT,
            files=files,
        )

    def get_ingestion_job_status(self, job_id: str) -> dict[str, Any]:
        """GET /api/v1/leads/jobs/{job_id} — poll ingestion job status.

        Returns:
            {
                "job_id": str,
                "status": "processing" | "completed" | "failed",
                "created": int,
                "skipped_duplicates": int,
                "skipped_invalid": int,
                "errors": int,
                "error"?: str,
            }
        """
        return self._get(f"/api/v1/leads/jobs/{job_id}")

    # ------------------------------------------------------------------
    # Lead Detail (Increment 2 / WF-003)
    # ------------------------------------------------------------------

    def list_leads(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> dict[str, Any]:
        """GET /api/v1/leads — paginated lead list."""
        params: dict[str, Any] = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        return self._get("/api/v1/leads", params=params)

    def get_lead(self, lead_id: str) -> dict[str, Any]:
        """GET /api/v1/leads/{lead_id} — full lead detail.

        Returns the Lead object with all fields.
        """
        return self._get(f"/api/v1/leads/{lead_id}")

    def get_lead_contacts(self, lead_id: str) -> list[dict[str, Any]]:
        """GET /api/v1/leads/{lead_id}/contacts — list of enriched contacts.

        Returns a list of Contact objects (may be empty).
        """
        response = self._get(f"/api/v1/leads/{lead_id}/contacts")
        contacts: list[dict[str, Any]] = (
            response if isinstance(response, list) else response.get("contacts", [])
        )
        return contacts

    def get_lead_matches(self, lead_id: str) -> list[dict[str, Any]]:
        """GET /api/v1/leads/{lead_id}/matches — inventory matches for a lead.

        Returns a list of InventoryMatch objects (may be empty).
        """
        response = self._get(f"/api/v1/leads/{lead_id}/matches")
        matches: list[dict[str, Any]] = (
            response if isinstance(response, list) else response.get("matches", [])
        )
        return matches

    def get_lead_activities(self, lead_id: str) -> list[dict[str, Any]]:
        """GET /api/v1/leads/{lead_id}/activities — CRM activity timeline.

        Returns a list of CRMActivity objects ordered newest-first.
        """
        response = self._get(f"/api/v1/leads/{lead_id}/activities")
        activities: list[dict[str, Any]] = (
            response if isinstance(response, list) else response.get("activities", [])
        )
        return activities

    # ------------------------------------------------------------------
    # Enrichment (Increment 2 / WF-003 — Enrich button)
    # ------------------------------------------------------------------

    def trigger_enrichment(self, lead_id: str) -> dict[str, Any]:
        """POST /api/v1/enrichment/{lead_id} — kick off async enrichment job.

        Returns:
            {"job_id": str, "status": "queued"}
        """
        return self._post(f"/api/v1/enrichment/{lead_id}")

    def get_enrichment_job_status(self, job_id: str) -> dict[str, Any]:
        """GET /api/v1/enrichment/jobs/{job_id} — poll enrichment job status.

        Returns:
            {
                "job_id": str,
                "lead_id": str,
                "status": "processing" | "completed" | "failed",
                "contact_id"?: str,
                "enrichment_source"?: str,
                "error"?: str,
            }
        """
        return self._get(f"/api/v1/enrichment/jobs/{job_id}")


# ------------------------------------------------------------------
# Singleton factory — one client per Streamlit session
# ------------------------------------------------------------------

@st.cache_resource
def get_api_client() -> APIClient:
    """Return a cached APIClient singleton for the current Streamlit session.

    Reads API_BASE_URL from st.secrets (set in .streamlit/secrets.toml).
    Falls back to localhost:8000 for local development.
    """
    try:
        base_url: str = st.secrets["API_BASE_URL"]
    except (KeyError, FileNotFoundError):
        base_url = "http://localhost:8000"
    return APIClient(base_url=base_url)
