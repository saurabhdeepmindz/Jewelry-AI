"""LangChain outreach email generation agent.

Generates personalized jewelry wholesale outreach emails given:
  - Lead company name and country
  - Contact name and title
  - Matched inventory items (SKU, carat, color, clarity)
  - Sequence step (1=initial, 2=day4 follow-up, 3=day7 final)

Model: gpt-4o-mini (cost-efficient for template generation).
Output: subject line + HTML email body.
"""
import json
import re
from typing import TypedDict

from src.core.exceptions import OutreachValidationException
from src.core.logging import get_logger

logger = get_logger(__name__)

_STEP_CONTEXT = {
    1: "This is the first outreach — introduce Shivam Jewels and the matched inventory.",
    2: (
        "This is a Day 4 follow-up. Acknowledge that we reached out previously. "
        "Gently add urgency: stock availability is limited and moves quickly."
    ),
    3: (
        "This is the Day 7 final follow-up. Acknowledge two prior contacts. "
        "Add strong urgency: this specific inventory may not be available much longer."
    ),
}

_SYSTEM_PROMPT = """You are the outreach specialist for Shivam Jewels, a premier diamond and
gemstone wholesaler based in India. Shivam Jewels supplies certified, GIA-graded diamonds to
jewelry retailers and wholesale buyers worldwide.

Your task is to write a short, personalized outreach email to a prospective buyer.

Tone: professional, warm, and consultative — NOT salesy or pushy.
Goal: establish a relationship and introduce the matched inventory naturally.
Length: 150–250 words for the body.

Rules:
1. Always reference the specific matched diamond inventory items provided.
2. Do NOT use generic phrases like "I hope this finds you well" as the opener.
3. Address the contact by first name if available, otherwise use their company name.
4. Mention Shivam Jewels by name at least once.
5. For follow-up steps (step 2 or 3), acknowledge prior contact and add appropriate urgency.
6. The body should be valid HTML (use <p> tags for paragraphs, <strong> for emphasis).
7. Keep the subject line under 60 characters.

You MUST respond with ONLY valid JSON in this exact format:
{"subject": "<subject line>", "body": "<html email body>"}

Do not include markdown fences, explanations, or any other text outside the JSON."""


class OutreachContext(TypedDict):
    """Input context for the outreach agent."""

    company_name: str
    country: str | None
    contact_name: str | None
    contact_title: str | None
    inventory_matches: list[dict]  # list of {sku, carat, color, clarity}
    sequence_step: int


class OutreachDraft(TypedDict):
    """Output from the outreach agent."""

    subject: str
    body: str


def _build_human_prompt(ctx: OutreachContext) -> str:
    """Construct the human-turn prompt with all context fields."""
    lines = [
        f"Company: {ctx['company_name']}",
        f"Country: {ctx.get('country') or 'Unknown'}",
        f"Contact name: {ctx.get('contact_name') or 'Not available'}",
        f"Contact title: {ctx.get('contact_title') or 'Not available'}",
        f"Sequence step: {ctx['sequence_step']}",
        f"Step context: {_STEP_CONTEXT.get(ctx['sequence_step'], _STEP_CONTEXT[1])}",
        "",
        "Matched inventory items:",
    ]

    matches = ctx.get("inventory_matches") or []
    if matches:
        for item in matches:
            sku = item.get("sku", "N/A")
            carat = item.get("carat", "N/A")
            color = item.get("color", "N/A")
            clarity = item.get("clarity", "N/A")
            lines.append(f"  - SKU {sku}: {carat:.2f}ct, Color {color}, Clarity {clarity}" if isinstance(carat, (int, float)) else f"  - SKU {sku}: {carat}ct, Color {color}, Clarity {clarity}")
    else:
        lines.append("  - (No specific inventory items — write a general introduction)")

    lines.append("")
    lines.append("Please generate the outreach email now.")
    return "\n".join(lines)


def _strip_json_fences(text: str) -> str:
    """Remove markdown code fences if the LLM wrapped the JSON response."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    fenced = re.sub(r"^```(?:json)?\s*", "", text)
    fenced = re.sub(r"\s*```$", "", fenced)
    return fenced.strip()


def _parse_draft(raw: str, context_info: str) -> OutreachDraft:
    """Parse JSON response from LLM into OutreachDraft. Raises OutreachValidationException on failure."""
    cleaned = _strip_json_fences(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error(
            "OutreachAgent JSON parse error context=%s raw=%r exc=%s",
            context_info,
            raw[:200],
            exc,
        )
        raise OutreachValidationException(
            f"Outreach agent returned invalid JSON: {exc}",
            detail=f"Raw response (first 200 chars): {raw[:200]}",
        ) from exc

    subject = data.get("subject")
    body = data.get("body")

    if not subject or not body:
        raise OutreachValidationException(
            "Outreach agent response missing 'subject' or 'body' fields",
            detail=f"Parsed keys: {list(data.keys())}",
        )

    draft: OutreachDraft = {"subject": str(subject), "body": str(body)}
    return draft


async def run_outreach_agent(ctx: OutreachContext) -> OutreachDraft:
    """Generate a personalized outreach email draft using gpt-4o-mini.

    Parameters
    ----------
    ctx:
        OutreachContext TypedDict with all lead + contact + inventory fields.

    Returns
    -------
    OutreachDraft
        TypedDict with 'subject' and 'body' keys.

    Raises
    ------
    OutreachValidationException
        If the LLM response cannot be parsed as valid JSON with subject + body.
    """
    # Lazy import — avoid loading LangChain/OpenAI at startup
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage

    from src.core.config import get_settings
    settings = get_settings()

    model = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY,
        temperature=0.7,
        max_tokens=1024,
    )

    human_prompt = _build_human_prompt(ctx)
    context_info = f"{ctx['company_name']} step={ctx['sequence_step']}"

    logger.info(
        "OutreachAgent generating draft company=%s step=%d",
        ctx["company_name"],
        ctx["sequence_step"],
    )

    messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=human_prompt),
    ]

    response = await model.ainvoke(messages)
    raw_content = str(response.content)

    draft = _parse_draft(raw_content, context_info)

    logger.info(
        "OutreachAgent draft generated company=%s step=%d subject=%r",
        ctx["company_name"],
        ctx["sequence_step"],
        draft["subject"],
    )

    return draft
