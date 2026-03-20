"""Unit tests for ProxycurlClient.

Covers:
- Successful enrichment with full profile data
- 404 → returns None
- 429 → raises ProxycurlAPIException (rate limit)
- 500 → raises ProxycurlAPIException
- Timeout → raises ProxycurlAPIException
- Empty payload → returns None
"""
import pytest
import respx
import httpx

from src.integrations.proxycurl_client import ProxycurlClient, PROXYCURL_PERSON_PROFILE_URL
from src.core.exceptions import ProxycurlAPIException


LINKEDIN_URL = "https://www.linkedin.com/in/john-doe"


@pytest.fixture
def client() -> ProxycurlClient:
    return ProxycurlClient(api_key="test-proxycurl-key")


@respx.mock
@pytest.mark.asyncio
async def test_enrich_returns_contact_data_on_success(client: ProxycurlClient) -> None:
    respx.get(PROXYCURL_PERSON_PROFILE_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "first_name": "John",
                "last_name": "Doe",
                "occupation": "VP Sales",
                "personal_emails": ["john.doe@acme.com"],
                "personal_numbers": ["+1-555-0100"],
            },
        )
    )

    result = await client.enrich_by_linkedin_url(LINKEDIN_URL)

    assert result is not None
    assert result.full_name == "John Doe"
    assert result.title == "VP Sales"
    assert result.email == "john.doe@acme.com"
    assert result.phone == "+1-555-0100"
    assert result.linkedin_url == LINKEDIN_URL
    assert result.enrichment_source.value == "proxycurl"


@respx.mock
@pytest.mark.asyncio
async def test_enrich_returns_none_on_404(client: ProxycurlClient) -> None:
    respx.get(PROXYCURL_PERSON_PROFILE_URL).mock(
        return_value=httpx.Response(404, json={})
    )

    result = await client.enrich_by_linkedin_url(LINKEDIN_URL)

    assert result is None


@respx.mock
@pytest.mark.asyncio
async def test_enrich_raises_on_429_rate_limit(client: ProxycurlClient) -> None:
    respx.get(PROXYCURL_PERSON_PROFILE_URL).mock(
        return_value=httpx.Response(429, json={"message": "rate limited"})
    )

    with pytest.raises(ProxycurlAPIException, match="credits exhausted"):
        await client.enrich_by_linkedin_url(LINKEDIN_URL)


@respx.mock
@pytest.mark.asyncio
async def test_enrich_raises_on_500_server_error(client: ProxycurlClient) -> None:
    respx.get(PROXYCURL_PERSON_PROFILE_URL).mock(
        return_value=httpx.Response(500, json={"error": "internal server error"})
    )

    with pytest.raises(ProxycurlAPIException, match="server error"):
        await client.enrich_by_linkedin_url(LINKEDIN_URL)


@pytest.mark.asyncio
async def test_enrich_raises_on_timeout(client: ProxycurlClient) -> None:
    with respx.mock:
        respx.get(PROXYCURL_PERSON_PROFILE_URL).mock(
            side_effect=httpx.TimeoutException("timed out")
        )

        with pytest.raises(ProxycurlAPIException, match="timed out"):
            await client.enrich_by_linkedin_url(LINKEDIN_URL)


@respx.mock
@pytest.mark.asyncio
async def test_enrich_returns_none_on_empty_payload(client: ProxycurlClient) -> None:
    respx.get(PROXYCURL_PERSON_PROFILE_URL).mock(
        return_value=httpx.Response(200, json={})
    )

    result = await client.enrich_by_linkedin_url(LINKEDIN_URL)

    assert result is None


@respx.mock
@pytest.mark.asyncio
async def test_enrich_handles_missing_optional_fields(client: ProxycurlClient) -> None:
    """Profile with only first_name — email and phone absent."""
    respx.get(PROXYCURL_PERSON_PROFILE_URL).mock(
        return_value=httpx.Response(
            200,
            json={"first_name": "Jane", "last_name": None, "occupation": "Buyer"},
        )
    )

    result = await client.enrich_by_linkedin_url(LINKEDIN_URL)

    assert result is not None
    assert result.full_name == "Jane"
    assert result.email is None
    assert result.phone is None
