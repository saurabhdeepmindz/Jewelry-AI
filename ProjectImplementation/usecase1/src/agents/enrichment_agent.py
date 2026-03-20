"""LangChain tool-use enrichment agent.

Orchestrates Apollo, Hunter, and Proxycurl as LangChain tools.
The agent decides the best enrichment strategy for a given lead domain/URL,
falls back gracefully, and returns a unified ContactData result.

Tool call order (cost-aware):
  1. apollo_enrich       — full contact (name, title, email, phone, linkedin)
  2. hunter_find_email   — email-only fallback if Apollo returns nothing
  3. proxycurl_enrich    — LinkedIn deep-dive if linkedin_url available but email missing

The agent is intentionally simple: a single LLM reasoning step selects and
sequences tools. It does NOT loop more than 3 steps to contain LLM costs.

LLM: Uses claude-haiku-4-5 by default (cost-efficient for tool routing).
     Override via ENRICHMENT_AGENT_MODEL env var.
"""
from __future__ import annotations

import json
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from src.core.logging import get_logger
from src.domain.contact import ContactData, EnrichmentSource
from src.integrations.apollo_client import ApolloClient
from src.integrations.hunter_client import HunterClient
from src.integrations.proxycurl_client import ProxycurlClient

logger = get_logger(__name__)

_SYSTEM_PROMPT = """You are a contact enrichment agent for a jewelry wholesale CRM.
Your job is to find the best available contact data for a company lead.

You have three tools:
- apollo_enrich(domain): Full contact enrichment via Apollo.io — name, title, email, phone, LinkedIn
- hunter_find_email(domain): Email-only lookup via Hunter.io — use when Apollo returns no data
- proxycurl_enrich(linkedin_url): Deep LinkedIn profile lookup — use only when a linkedin_url is already known but email is missing

Strategy:
1. Always try apollo_enrich first.
2. If Apollo returns no data, try hunter_find_email.
3. If a linkedin_url is available but email is still missing, try proxycurl_enrich.
4. Stop after 3 tool calls maximum.
5. Return the best available ContactData as a JSON object with keys:
   full_name, title, email, phone, linkedin_url, enrichment_source

enrichment_source must be one of: apollo, hunter, proxycurl, manual.
If no data found, return {"enrichment_source": null}.
"""


def _build_tools(
    domain: str,
    linkedin_url: str | None,
) -> list[Any]:
    """Build LangChain tool functions bound to the given lead context."""

    apollo_client = ApolloClient()
    hunter_client = HunterClient()
    proxycurl_client = ProxycurlClient()

    @tool
    async def apollo_enrich(domain: str) -> str:  # noqa: F841
        """Enrich a company domain via Apollo.io. Returns full contact or 'no_data'."""
        try:
            result = await apollo_client.enrich(domain)
            if result is None:
                return "no_data"
            return result.model_dump_json()
        except Exception as exc:
            logger.warning("apollo_enrich tool error: %s", exc)
            return f"error: {exc}"

    @tool
    async def hunter_find_email(domain: str) -> str:  # noqa: F841
        """Find a work email for a company domain via Hunter.io. Returns email or 'no_data'."""
        try:
            email = await hunter_client.find_email(domain)
            if email is None:
                return "no_data"
            return json.dumps({"email": email, "enrichment_source": "hunter"})
        except Exception as exc:
            logger.warning("hunter_find_email tool error: %s", exc)
            return f"error: {exc}"

    @tool
    async def proxycurl_enrich(linkedin_url: str) -> str:  # noqa: F841
        """Enrich a LinkedIn profile URL via Proxycurl. Returns contact data or 'no_data'."""
        try:
            result = await proxycurl_client.enrich_by_linkedin_url(linkedin_url)
            if result is None:
                return "no_data"
            return result.model_dump_json()
        except Exception as exc:
            logger.warning("proxycurl_enrich tool error: %s", exc)
            return f"error: {exc}"

    return [apollo_enrich, hunter_find_email, proxycurl_enrich]


def _parse_agent_output(content: str) -> ContactData | None:
    """Parse the agent's final JSON response into a ContactData object."""
    try:
        # Strip markdown fences if present
        cleaned = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
        source_raw = data.get("enrichment_source")
        if not source_raw:
            return None
        return ContactData(
            full_name=data.get("full_name"),
            title=data.get("title"),
            email=data.get("email"),
            phone=data.get("phone"),
            linkedin_url=data.get("linkedin_url"),
            enrichment_source=EnrichmentSource(source_raw),
        )
    except Exception as exc:
        logger.warning("Failed to parse enrichment agent output: %s — raw: %s", exc, content[:200])
        return None


async def run_enrichment_agent(
    domain: str,
    linkedin_url: str | None = None,
    model: str = "claude-haiku-4-5-20251001",
) -> ContactData | None:
    """Run the LangChain enrichment agent for a single lead.

    Parameters
    ----------
    domain:
        Company website domain, e.g. "acme.com". Used by Apollo and Hunter.
    linkedin_url:
        Optional LinkedIn profile URL already known (e.g. from a previous Apollo call).
        Passed to Proxycurl if needed.
    model:
        LangChain model ID. Defaults to claude-haiku-4-5 for cost efficiency.

    Returns
    -------
    ContactData | None
        Best available contact data, or None if all providers returned nothing.
    """
    tools = _build_tools(domain, linkedin_url)
    llm = ChatAnthropic(model=model, max_tokens=1024).bind_tools(tools)

    context_parts = [f"Lead domain: {domain}"]
    if linkedin_url:
        context_parts.append(f"Known LinkedIn URL: {linkedin_url}")

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content="\n".join(context_parts)),
    ]

    tool_map = {t.name: t for t in tools}
    max_steps = 3

    for step in range(max_steps):
        response = await llm.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            # Agent is done — parse the final answer
            final_text = response.content if isinstance(response.content, str) else ""
            result = _parse_agent_output(final_text)
            logger.info(
                "Enrichment agent completed domain=%s steps=%d found=%s",
                domain,
                step + 1,
                result is not None,
            )
            return result

        # Execute each tool call and feed results back
        from langchain_core.messages import ToolMessage
        for tool_call in response.tool_calls:
            tool_fn = tool_map.get(tool_call["name"])
            if tool_fn is None:
                tool_output = f"error: unknown tool {tool_call['name']!r}"
            else:
                try:
                    tool_output = await tool_fn.ainvoke(tool_call["args"])
                except Exception as exc:
                    tool_output = f"error: {exc}"
            messages.append(
                ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
            )

    # Exceeded max steps — try to parse whatever the last message contained
    last_content = messages[-1].content if messages else ""
    if isinstance(last_content, str):
        return _parse_agent_output(last_content)
    return None
