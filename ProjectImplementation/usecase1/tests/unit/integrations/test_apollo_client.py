"""Unit tests for src/integrations/apollo_client.py.

HTTP calls mocked via respx — no real network traffic.
Follows testing-rules.md: use respx, not unittest.mock.patch on httpx.
"""
import httpx
import pytest
import respx

from src.core.exceptions import ApolloAPIException
from src.domain.contact import EnrichmentSource
from src.integrations.apollo_client import APOLLO_PEOPLE_MATCH_URL, ApolloClient

DOMAIN = "pristinediamonds.example.com"
PERSON_PAYLOAD = {
    "person": {
        "name": "Sarah Mitchell",
        "title": "Head Buyer",
        "email": "s.mitchell@pristinediamonds.example.com",
        "phone_numbers": [{"raw_number": "+1-212-555-0101"}],
        "linkedin_url": "https://linkedin.com/in/sarahmitchell",
    }
}


class TestApolloClientEnrich:
    """Test ApolloClient.enrich(domain)."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_contact_data_on_200(self) -> None:
        respx.post(APOLLO_PEOPLE_MATCH_URL).mock(
            return_value=httpx.Response(200, json=PERSON_PAYLOAD)
        )

        client = ApolloClient(api_key="test-key")
        result = await client.enrich(DOMAIN)

        assert result is not None
        assert result.full_name == "Sarah Mitchell"
        assert result.title == "Head Buyer"
        assert result.email == "s.mitchell@pristinediamonds.example.com"
        assert result.phone == "+1-212-555-0101"
        assert result.linkedin_url == "https://linkedin.com/in/sarahmitchell"
        assert result.enrichment_source == EnrichmentSource.apollo

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_none_on_404(self) -> None:
        respx.post(APOLLO_PEOPLE_MATCH_URL).mock(
            return_value=httpx.Response(404)
        )

        client = ApolloClient(api_key="test-key")
        result = await client.enrich("unknown.example.com")

        assert result is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_none_on_401(self) -> None:
        respx.post(APOLLO_PEOPLE_MATCH_URL).mock(
            return_value=httpx.Response(401)
        )

        client = ApolloClient(api_key="bad-key")
        result = await client.enrich("example.com")

        assert result is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_none_on_403(self) -> None:
        respx.post(APOLLO_PEOPLE_MATCH_URL).mock(
            return_value=httpx.Response(403)
        )

        client = ApolloClient(api_key="blocked-key")
        result = await client.enrich("example.com")

        assert result is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_apollo_exception_on_500(self) -> None:
        respx.post(APOLLO_PEOPLE_MATCH_URL).mock(
            return_value=httpx.Response(500)
        )

        client = ApolloClient(api_key="test-key")
        with pytest.raises(ApolloAPIException):
            await client.enrich("example.com")

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_apollo_exception_on_timeout(self) -> None:
        respx.post(APOLLO_PEOPLE_MATCH_URL).mock(
            side_effect=httpx.TimeoutException("timeout")
        )

        client = ApolloClient(api_key="test-key")
        with pytest.raises(ApolloAPIException):
            await client.enrich("example.com")

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_none_when_person_is_null(self) -> None:
        respx.post(APOLLO_PEOPLE_MATCH_URL).mock(
            return_value=httpx.Response(200, json={"person": None})
        )

        client = ApolloClient(api_key="test-key")
        result = await client.enrich("noperson.example.com")

        assert result is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_none_when_person_is_empty_dict(self) -> None:
        respx.post(APOLLO_PEOPLE_MATCH_URL).mock(
            return_value=httpx.Response(200, json={"person": {}})
        )

        client = ApolloClient(api_key="test-key")
        result = await client.enrich("empty.example.com")

        assert result is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_phone_is_none_when_phone_numbers_empty(self) -> None:
        payload = {
            "person": {
                "name": "John Doe",
                "title": "Buyer",
                "email": "john@example.com",
                "phone_numbers": [],
                "linkedin_url": None,
            }
        }
        respx.post(APOLLO_PEOPLE_MATCH_URL).mock(
            return_value=httpx.Response(200, json=payload)
        )

        client = ApolloClient(api_key="test-key")
        result = await client.enrich("example.com")

        assert result is not None
        assert result.phone is None
