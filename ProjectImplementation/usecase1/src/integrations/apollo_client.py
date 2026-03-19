"""Apollo.io contact enrichment client.

Uses async httpx to call the Apollo.io People Match API.
Returns ContactData or None if no contact was found for the domain.

Business rules:
- 401/403 → treat as "not found" (key may be invalid or domain blocked)
- 404 → return None (no person found)
- 5xx → raise ApolloAPIException (upstream failure)
- Timeout → raise ApolloAPIException
- Empty person payload → return None (no data to use)
"""
from typing import Any

import httpx

from src.core.exceptions import ApolloAPIException
from src.core.logging import get_logger
from src.domain.contact import ContactData, EnrichmentSource

logger = get_logger(__name__)

APOLLO_PEOPLE_MATCH_URL = "https://api.apollo.io/v1/people/match"
TIMEOUT_SECONDS = 10.0


class ApolloClient:
    """Async HTTP client wrapping Apollo.io People Match endpoint."""

    def __init__(self, api_key: str | None = None) -> None:
        if api_key is None:
            from src.core.config import get_settings
            api_key = get_settings().APOLLO_API_KEY
        self._api_key = api_key

    async def enrich(self, domain: str) -> ContactData | None:
        """Fetch the primary contact for a company domain.

        Returns ContactData if Apollo found a person, None otherwise.
        Raises ApolloAPIException on server errors or timeouts.
        """
        payload = {
            "api_key": self._api_key,
            "domain": domain,
            "reveal_personal_emails": False,
        }
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.post(
                    APOLLO_PEOPLE_MATCH_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
        except httpx.TimeoutException as exc:
            raise ApolloAPIException(
                f"Apollo.io timed out after {TIMEOUT_SECONDS}s for domain {domain!r}"
            ) from exc

        if response.status_code in (401, 403):
            logger.warning(
                "Apollo.io auth error domain=%s status=%d",
                domain,
                response.status_code,
            )
            return None

        if response.status_code == 404:
            return None

        if response.status_code >= 500:
            raise ApolloAPIException(
                f"Apollo.io server error: HTTP {response.status_code}"
            )

        if response.status_code != 200:
            logger.warning(
                "Apollo.io unexpected status domain=%s status=%d",
                domain,
                response.status_code,
            )
            return None

        person: dict[str, Any] = response.json().get("person") or {}
        if not person:
            return None

        phone_numbers: list[dict[str, str]] = person.get("phone_numbers") or []
        phone = phone_numbers[0].get("raw_number") if phone_numbers else None

        return ContactData(
            full_name=person.get("name"),
            title=person.get("title"),
            email=person.get("email"),
            phone=phone,
            linkedin_url=person.get("linkedin_url"),
            enrichment_source=EnrichmentSource.apollo,
        )
