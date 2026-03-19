"""Unit tests for src/integrations/hunter_client.py.

HTTP calls mocked via respx — no real network traffic.
Follows testing-rules.md: use respx, not unittest.mock.patch on httpx.
"""
import httpx
import pytest
import respx

from src.core.exceptions import HunterAPIException
from src.integrations.hunter_client import HUNTER_API_BASE, HunterClient

VERIFY_URL = f"{HUNTER_API_BASE}/email-verifier"
FINDER_URL = f"{HUNTER_API_BASE}/email-finder"


class TestHunterClientVerifyEmail:
    """Test HunterClient.verify_email(email)."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_true_when_deliverable(self) -> None:
        respx.get(VERIFY_URL).mock(
            return_value=httpx.Response(
                200, json={"data": {"result": "deliverable"}}
            )
        )

        client = HunterClient(api_key="test-key")
        result = await client.verify_email("buyer@example.com")

        assert result is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_false_when_risky(self) -> None:
        respx.get(VERIFY_URL).mock(
            return_value=httpx.Response(
                200, json={"data": {"result": "risky"}}
            )
        )

        client = HunterClient(api_key="test-key")
        result = await client.verify_email("risky@example.com")

        assert result is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_false_when_undeliverable(self) -> None:
        respx.get(VERIFY_URL).mock(
            return_value=httpx.Response(
                200, json={"data": {"result": "undeliverable"}}
            )
        )

        client = HunterClient(api_key="test-key")
        result = await client.verify_email("bounce@example.com")

        assert result is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_false_on_404(self) -> None:
        respx.get(VERIFY_URL).mock(return_value=httpx.Response(404))

        client = HunterClient(api_key="test-key")
        result = await client.verify_email("unknown@example.com")

        assert result is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_hunter_exception_on_500(self) -> None:
        respx.get(VERIFY_URL).mock(return_value=httpx.Response(500))

        client = HunterClient(api_key="test-key")
        with pytest.raises(HunterAPIException):
            await client.verify_email("buyer@example.com")

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_hunter_exception_on_timeout(self) -> None:
        respx.get(VERIFY_URL).mock(
            side_effect=httpx.TimeoutException("timeout")
        )

        client = HunterClient(api_key="test-key")
        with pytest.raises(HunterAPIException):
            await client.verify_email("buyer@example.com")


class TestHunterClientFindEmail:
    """Test HunterClient.find_email(domain, full_name)."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_email_on_success(self) -> None:
        respx.get(FINDER_URL).mock(
            return_value=httpx.Response(
                200, json={"data": {"email": "sarah@pristine.example.com"}}
            )
        )

        client = HunterClient(api_key="test-key")
        result = await client.find_email("pristine.example.com", "Sarah Mitchell")

        assert result == "sarah@pristine.example.com"

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_none_when_not_found(self) -> None:
        respx.get(FINDER_URL).mock(return_value=httpx.Response(404))

        client = HunterClient(api_key="test-key")
        result = await client.find_email("unknown.example.com")

        assert result is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_hunter_exception_on_500(self) -> None:
        respx.get(FINDER_URL).mock(return_value=httpx.Response(500))

        client = HunterClient(api_key="test-key")
        with pytest.raises(HunterAPIException):
            await client.find_email("example.com")

    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_email_without_name(self) -> None:
        respx.get(FINDER_URL).mock(
            return_value=httpx.Response(
                200, json={"data": {"email": "generic@example.com"}}
            )
        )

        client = HunterClient(api_key="test-key")
        result = await client.find_email("example.com")

        assert result == "generic@example.com"
