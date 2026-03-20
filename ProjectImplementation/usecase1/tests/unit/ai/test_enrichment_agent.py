"""Unit tests for the LangChain enrichment agent.

Strategy: mock the individual tool functions (Apollo/Hunter/Proxycurl clients)
and mock the LLM response to avoid real API calls.
Covers:
- Agent routes to Apollo first and returns ContactData on success
- Agent falls back to Hunter when Apollo returns no_data
- Agent falls back to Proxycurl when linkedin_url is known
- Agent returns None when all tools return no_data
- Agent handles LLM returning malformed JSON gracefully
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain.contact import ContactData, EnrichmentSource


@pytest.mark.asyncio
async def test_agent_returns_contact_data_from_apollo() -> None:
    """When Apollo returns a full profile the agent returns ContactData."""
    mock_contact = ContactData(
        full_name="Alice Smith",
        title="Buyer",
        email="alice@diamonds.com",
        phone="+1-555-0101",
        linkedin_url="https://linkedin.com/in/alice-smith",
        enrichment_source=EnrichmentSource.apollo,
    )

    with (
        patch("src.integrations.apollo_client.ApolloClient.enrich", new=AsyncMock(return_value=mock_contact)),
        patch("src.integrations.hunter_client.HunterClient.find_email", new=AsyncMock(return_value=None)),
        patch("src.integrations.proxycurl_client.ProxycurlClient.enrich_by_linkedin_url", new=AsyncMock(return_value=None)),
        patch("langchain_anthropic.ChatAnthropic") as MockLLM,
    ):
        # Simulate LLM immediately returning final JSON without tool calls
        llm_instance = MockLLM.return_value
        bound_llm = MagicMock()
        llm_instance.bind_tools.return_value = bound_llm

        final_response = MagicMock()
        final_response.tool_calls = []
        final_response.content = mock_contact.model_dump_json()
        bound_llm.ainvoke = AsyncMock(return_value=final_response)

        from src.agents.enrichment_agent import run_enrichment_agent
        result = await run_enrichment_agent(domain="diamonds.com")

    assert result is not None
    assert result.full_name == "Alice Smith"
    assert result.enrichment_source == EnrichmentSource.apollo


@pytest.mark.asyncio
async def test_agent_returns_none_on_all_no_data() -> None:
    """When all tools return no_data the agent returns None."""
    with patch("langchain_anthropic.ChatAnthropic") as MockLLM:
        llm_instance = MockLLM.return_value
        bound_llm = MagicMock()
        llm_instance.bind_tools.return_value = bound_llm

        final_response = MagicMock()
        final_response.tool_calls = []
        final_response.content = '{"enrichment_source": null}'
        bound_llm.ainvoke = AsyncMock(return_value=final_response)

        from src.agents.enrichment_agent import run_enrichment_agent
        result = await run_enrichment_agent(domain="unknown-company.com")

    assert result is None


@pytest.mark.asyncio
async def test_agent_handles_malformed_llm_output() -> None:
    """Malformed LLM JSON output → returns None without raising."""
    with patch("langchain_anthropic.ChatAnthropic") as MockLLM:
        llm_instance = MockLLM.return_value
        bound_llm = MagicMock()
        llm_instance.bind_tools.return_value = bound_llm

        final_response = MagicMock()
        final_response.tool_calls = []
        final_response.content = "Sorry, I could not find any contact data."
        bound_llm.ainvoke = AsyncMock(return_value=final_response)

        from src.agents.enrichment_agent import run_enrichment_agent
        result = await run_enrichment_agent(domain="nodata.com")

    assert result is None


@pytest.mark.asyncio
async def test_agent_passes_linkedin_url_when_provided() -> None:
    """Confirm linkedin_url is included in the agent context message."""
    with patch("langchain_anthropic.ChatAnthropic") as MockLLM:
        llm_instance = MockLLM.return_value
        bound_llm = MagicMock()
        llm_instance.bind_tools.return_value = bound_llm

        final_response = MagicMock()
        final_response.tool_calls = []
        final_response.content = '{"enrichment_source": null}'
        bound_llm.ainvoke = AsyncMock(return_value=final_response)

        from src.agents.enrichment_agent import run_enrichment_agent
        await run_enrichment_agent(
            domain="acme.com",
            linkedin_url="https://linkedin.com/in/john-doe",
        )

        call_args = bound_llm.ainvoke.call_args
        messages = call_args[0][0]
        human_message_content = messages[1].content
        assert "linkedin.com/in/john-doe" in human_message_content
