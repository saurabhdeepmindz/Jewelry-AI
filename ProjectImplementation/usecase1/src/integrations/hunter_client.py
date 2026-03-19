"""Hunter.io email finder and email verifier client.

Two operations:
  find_email(domain, full_name?) → str | None
    Searches for a person's work email at a company domain.

  verify_email(email) → bool
    Verifies whether an email address is deliverable.

Business rules:
- 404 → return None / False (not found)
- 5xx → raise HunterAPIException
- Timeout → raise HunterAPIException
- result == "deliverable" → True; anything else → False
"""
from typing import Any

import httpx

from src.core.exceptions import HunterAPIException
from src.core.logging import get_logger

logger = get_logger(__name__)

HUNTER_API_BASE = "https://api.hunter.io/v2"
TIMEOUT_SECONDS = 10.0


class HunterClient:
    """Async HTTP client wrapping Hunter.io email-finder and email-verifier APIs."""

    def __init__(self, api_key: str | None = None) -> None:
        if api_key is None:
            from src.core.config import get_settings
            api_key = get_settings().HUNTER_API_KEY
        self._api_key = api_key

    async def find_email(
        self,
        domain: str,
        full_name: str | None = None,
    ) -> str | None:
        """Find a person's work email at the given domain.

        Splits full_name into first/last when space is present.
        Returns email string on success, None if not found.
        Raises HunterAPIException on server errors or timeouts.
        """
        params: dict[str, Any] = {"domain": domain, "api_key": self._api_key}
        if full_name and " " in full_name:
            first, last = full_name.split(" ", 1)
            params["first_name"] = first
            params["last_name"] = last

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.get(
                    f"{HUNTER_API_BASE}/email-finder", params=params
                )
        except httpx.TimeoutException as exc:
            raise HunterAPIException(
                f"Hunter.io email-finder timed out for domain {domain!r}"
            ) from exc

        if response.status_code == 404:
            return None

        if response.status_code >= 500:
            raise HunterAPIException(
                f"Hunter.io server error: HTTP {response.status_code}"
            )

        if response.status_code != 200:
            return None

        email: str | None = response.json().get("data", {}).get("email")
        return email

    async def verify_email(self, email: str) -> bool:
        """Verify whether an email address is deliverable.

        Returns True only when Hunter reports result == "deliverable".
        Returns False for risky, undeliverable, or unknown results.
        Raises HunterAPIException on server errors or timeouts.
        """
        params = {"email": email, "api_key": self._api_key}

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.get(
                    f"{HUNTER_API_BASE}/email-verifier", params=params
                )
        except httpx.TimeoutException as exc:
            raise HunterAPIException(
                f"Hunter.io email-verifier timed out for {email!r}"
            ) from exc

        if response.status_code == 404:
            return False

        if response.status_code >= 500:
            raise HunterAPIException(
                f"Hunter.io server error: HTTP {response.status_code}"
            )

        if response.status_code != 200:
            return False

        deliverability: str | None = response.json().get("data", {}).get("result")
        return deliverability == "deliverable"
