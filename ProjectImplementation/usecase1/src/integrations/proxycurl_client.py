"""Proxycurl LinkedIn profile enrichment client.

Uses async httpx to call the Proxycurl Person Profile API.
Given a LinkedIn profile URL, returns enriched ContactData or None.

Business rules:
- 404 → return None (profile not found or URL invalid)
- 429 → raise ProxycurlAPIException with rate-limit message (credits exhausted)
- 5xx → raise ProxycurlAPIException (upstream failure)
- Timeout → raise ProxycurlAPIException
- Empty payload → return None (no usable data)

Proxycurl charges per successful API call (~$0.01/profile).
Only call this client when Apollo and Hunter have both returned no usable data.
"""
from typing import Any

import httpx

from src.core.exceptions import ProxycurlAPIException
from src.core.logging import get_logger
from src.domain.contact import ContactData, EnrichmentSource

logger = get_logger(__name__)

PROXYCURL_PERSON_PROFILE_URL = "https://nubela.co/proxycurl/api/v2/linkedin"
TIMEOUT_SECONDS = 15.0


class ProxycurlClient:
    """Async HTTP client wrapping the Proxycurl Person Profile endpoint.

    Proxycurl requires a LinkedIn profile URL to look up a person.
    The LinkedIn URL is typically provided by Apollo or discovered via lead domain.
    """

    def __init__(self, api_key: str | None = None) -> None:
        if api_key is None:
            from src.core.config import get_settings
            api_key = get_settings().PROXYCURL_API_KEY
        self._api_key = api_key

    async def enrich_by_linkedin_url(
        self,
        linkedin_url: str,
    ) -> ContactData | None:
        """Fetch enriched profile data from a LinkedIn profile URL.

        Parameters
        ----------
        linkedin_url:
            Full LinkedIn profile URL, e.g. https://linkedin.com/in/john-doe

        Returns
        -------
        ContactData | None
            Populated ContactData if Proxycurl returned a usable profile.
            None if the profile was not found.

        Raises
        ------
        ProxycurlAPIException
            On rate limit (429), server errors (5xx), or timeouts.
        """
        params = {
            "linkedin_profile_url": linkedin_url,
            "extra": "include",
            "github_profile_id": "exclude",
            "facebook_profile_id": "exclude",
            "twitter_profile_id": "exclude",
            "personal_contact_number": "include",
            "personal_email": "include",
            "inferred_salary": "exclude",
            "skills": "exclude",
            "use_cache": "if-present",
            "fallback_to_cache": "on-error",
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                response = await client.get(
                    PROXYCURL_PERSON_PROFILE_URL,
                    params=params,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise ProxycurlAPIException(
                f"Proxycurl timed out after {TIMEOUT_SECONDS}s for URL {linkedin_url!r}"
            ) from exc

        if response.status_code == 404:
            logger.info(
                "Proxycurl: profile not found linkedin_url=%s", linkedin_url
            )
            return None

        if response.status_code == 429:
            raise ProxycurlAPIException(
                "Proxycurl API rate limit / credits exhausted — check your dashboard"
            )

        if response.status_code >= 500:
            raise ProxycurlAPIException(
                f"Proxycurl server error: HTTP {response.status_code}"
            )

        if response.status_code != 200:
            logger.warning(
                "Proxycurl unexpected status=%d linkedin_url=%s",
                response.status_code,
                linkedin_url,
            )
            return None

        data: dict[str, Any] = response.json()
        if not data:
            return None

        # Extract best available phone
        phone: str | None = None
        personal_numbers: list[str] = data.get("personal_numbers") or []
        if personal_numbers:
            phone = personal_numbers[0]

        # Extract best available email
        email: str | None = data.get("personal_emails", [None])[0] if data.get("personal_emails") else None

        full_name_parts = [data.get("first_name"), data.get("last_name")]
        full_name = " ".join(p for p in full_name_parts if p) or None

        # Primary occupation title
        title: str | None = data.get("occupation")
        if not title:
            experiences: list[dict[str, Any]] = data.get("experiences") or []
            if experiences:
                title = experiences[0].get("title")

        logger.info(
            "Proxycurl: enriched profile linkedin_url=%s name=%s",
            linkedin_url,
            full_name,
        )

        return ContactData(
            full_name=full_name,
            title=title,
            email=email,
            phone=phone,
            linkedin_url=linkedin_url,
            enrichment_source=EnrichmentSource.proxycurl,
        )
