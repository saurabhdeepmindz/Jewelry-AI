"""Contact enrichment service.

Enrichment strategy:
  1. Load lead — raise NotFoundException if not found.
  2. Check for existing active contact — raise EnrichmentCreditException
     (business rule: never re-enrich an already-enriched lead; credits are finite).
  3. If lead has a domain → try Apollo.io (full contact: name, title, email, phone, linkedin).
  4. If Apollo returns data and has an email → verify deliverability with Hunter.io.
  5. If Apollo returned None → fall back to Hunter.io email-finder (email only).
  6. If both direct providers return nothing → delegate to EnrichmentAgent (LangChain
     tool-use agent that orchestrates Apollo + Hunter + Proxycurl with LLM reasoning).
  7. If all strategies exhausted → raise IntegrationException.
  8. Create Contact record, update lead.status = "enriched", flush.
"""
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    EnrichmentCreditException,
    IntegrationException,
    NotFoundException,
)
from src.core.logging import get_logger
from src.domain.contact import ContactCreate, ContactData, ContactRead, EnrichmentSource
from src.integrations.apollo_client import ApolloClient
from src.integrations.hunter_client import HunterClient
from src.repositories.contact_repository import ContactRepository
from src.repositories.lead_repository import LeadRepository

# Lazy import to avoid loading LangChain at startup when not needed
def _get_enrichment_agent():  # type: ignore[return]
    from src.agents.enrichment_agent import run_enrichment_agent
    return run_enrichment_agent

logger = get_logger(__name__)


async def enrich_lead(session: AsyncSession, lead_id: UUID) -> ContactRead:
    """Enrich a single lead with contact data from Apollo.io / Hunter.io.

    Parameters
    ----------
    session:
        Active async database session (caller is responsible for commit).
    lead_id:
        UUID of the lead to enrich.

    Returns
    -------
    ContactRead
        The newly created contact record.

    Raises
    ------
    NotFoundException
        Lead does not exist or has been soft-deleted.
    EnrichmentCreditException
        Lead already has an active contact — re-enrichment is blocked.
    IntegrationException
        All enrichment providers returned no usable data.
    """
    lead_repo = LeadRepository(session)
    contact_repo = ContactRepository(session)

    lead = await lead_repo.get_by_id(lead_id)
    if lead is None:
        raise NotFoundException(f"Lead {lead_id!r} not found")

    existing = await contact_repo.get_active_by_lead_id(lead_id)
    if existing is not None:
        raise EnrichmentCreditException(
            "Lead is already enriched — use cached contact data"
        )

    contact_data: ContactData | None = None
    apollo = ApolloClient()
    hunter = HunterClient()

    # --- Apollo first (full enrichment) ---
    if lead.domain:
        try:
            contact_data = await apollo.enrich(lead.domain)
        except IntegrationException as exc:
            logger.warning(
                "Apollo.io failed for lead_id=%s domain=%s: %s",
                lead_id,
                lead.domain,
                exc,
            )

    # --- Hunter fallback (email-only enrichment) ---
    if contact_data is None and lead.domain:
        try:
            email = await hunter.find_email(lead.domain)
            if email:
                contact_data = ContactData(
                    email=email,
                    enrichment_source=EnrichmentSource.hunter,
                )
        except IntegrationException as exc:
            logger.warning(
                "Hunter.io failed for lead_id=%s domain=%s: %s",
                lead_id,
                lead.domain,
                exc,
            )

    # --- EnrichmentAgent fallback (LangChain: Apollo + Hunter + Proxycurl with LLM routing) ---
    if contact_data is None and lead.domain:
        try:
            run_enrichment_agent = _get_enrichment_agent()
            contact_data = await run_enrichment_agent(
                domain=lead.domain,
                linkedin_url=None,
            )
        except Exception as exc:
            logger.warning(
                "EnrichmentAgent failed for lead_id=%s domain=%s: %s",
                lead_id,
                lead.domain,
                exc,
            )

    if contact_data is None:
        raise IntegrationException(
            "Could not enrich lead: all providers (Apollo, Hunter, EnrichmentAgent) returned no data"
        )

    # --- Email verification (best-effort; failure does not block enrichment) ---
    email_verified = False
    if contact_data.email:
        try:
            email_verified = await hunter.verify_email(contact_data.email)
        except IntegrationException as exc:
            logger.warning(
                "Hunter email verify failed for lead_id=%s: %s", lead_id, exc
            )

    create_data = ContactCreate(
        lead_id=lead_id,
        full_name=contact_data.full_name,
        title=contact_data.title,
        email=contact_data.email,
        email_verified=email_verified,
        phone=contact_data.phone,
        linkedin_url=contact_data.linkedin_url,
        enrichment_source=contact_data.enrichment_source,
    )
    contact = await contact_repo.create(create_data)

    # Update lead pipeline status
    lead.status = "enriched"
    lead.updated_at = datetime.now(UTC)
    await session.flush()

    logger.info(
        "Lead enriched lead_id=%s contact_id=%s source=%s",
        lead_id,
        contact.id,
        contact_data.enrichment_source.value,
    )
    return ContactRead.model_validate(contact)
