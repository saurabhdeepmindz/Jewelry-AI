"""Test factories — factory_boy builders for all domain entities.

Usage:
    from tests.factories.lead_factory import LeadCreateFactory, LeadORMFactory
    from tests.factories.contact_factory import ContactCreateFactory, ContactORMFactory
    from tests.factories.outreach_factory import OutreachCreateFactory, OutreachMessageORMFactory

For ORM factories (SQLAlchemy), inject the session before use:
    LeadORMFactory._meta.sqlalchemy_session = session
    OutreachMessageORMFactory._meta.sqlalchemy_session = session
"""
