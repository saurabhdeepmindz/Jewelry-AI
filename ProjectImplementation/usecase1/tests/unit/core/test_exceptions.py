"""Unit tests for src/core/exceptions.py.

TDD: Each exception must have the correct HTTP status code and inherit correctly.
Run: pytest tests/unit/core/test_exceptions.py -v
"""
import pytest
from src.core.exceptions import (
    ApolloAPIException,
    AuthException,
    BaseAppException,
    BusinessRuleException,
    CacheException,
    ConflictException,
    ContactNotFoundException,
    DatabaseException,
    DuplicateLeadException,
    EmailDeliveryError,
    EnrichmentCreditException,
    EnrichmentRateLimitError,
    ImmutableRecordError,
    InfrastructureException,
    IntegrationException,
    InvalidCredentialsException,
    InsufficientPermissionsException,
    InventoryNotFoundException,
    LeadNotEligibleException,
    LeadNotFoundException,
    LeadValidationException,
    NotFoundException,
    OpenAIAPIException,
    OutreachAlreadySentException,
    OutreachPendingReviewException,
    OutreachValidationException,
    PermissionException,
    SendGridAPIException,
    TokenExpiredException,
    UserNotFoundException,
    ValidationException,
)


class TestBaseAppException:
    def test_base_exception_has_500_status_code(self) -> None:
        exc = BaseAppException()
        assert exc.status_code == 500

    def test_base_exception_stores_custom_message(self) -> None:
        exc = BaseAppException(message="Something went wrong")
        assert exc.message == "Something went wrong"
        assert str(exc) == "Something went wrong"

    def test_base_exception_stores_code_and_detail(self) -> None:
        exc = BaseAppException(code="MY_CODE", detail="extra info")
        assert exc.code == "MY_CODE"
        assert exc.detail == "extra info"

    def test_base_exception_uses_defaults_when_no_args(self) -> None:
        exc = BaseAppException()
        assert exc.code == "INTERNAL_ERROR"
        assert exc.detail is None


class TestValidationExceptions:
    def test_validation_exception_is_422(self) -> None:
        assert ValidationException().status_code == 422

    def test_lead_validation_exception_is_422(self) -> None:
        assert LeadValidationException().status_code == 422

    def test_outreach_validation_exception_is_422(self) -> None:
        assert OutreachValidationException().status_code == 422

    def test_validation_exception_inherits_base(self) -> None:
        assert issubclass(ValidationException, BaseAppException)


class TestNotFoundExceptions:
    def test_not_found_exception_is_404(self) -> None:
        assert NotFoundException().status_code == 404

    def test_lead_not_found_is_404(self) -> None:
        assert LeadNotFoundException().status_code == 404

    def test_contact_not_found_is_404(self) -> None:
        assert ContactNotFoundException().status_code == 404

    def test_inventory_not_found_is_404(self) -> None:
        assert InventoryNotFoundException().status_code == 404

    def test_user_not_found_is_404(self) -> None:
        assert UserNotFoundException().status_code == 404


class TestConflictExceptions:
    def test_conflict_exception_is_409(self) -> None:
        assert ConflictException().status_code == 409

    def test_duplicate_lead_is_conflict(self) -> None:
        exc = DuplicateLeadException()
        assert exc.status_code == 409
        assert isinstance(exc, ConflictException)
        assert exc.code == "DUPLICATE_LEAD"

    def test_outreach_already_sent_is_409(self) -> None:
        assert OutreachAlreadySentException().status_code == 409

    def test_immutable_record_error_is_409(self) -> None:
        exc = ImmutableRecordError()
        assert exc.status_code == 409
        assert exc.code == "IMMUTABLE_RECORD"


class TestAuthAndPermissionExceptions:
    def test_auth_exception_is_401(self) -> None:
        assert AuthException().status_code == 401

    def test_invalid_credentials_is_401(self) -> None:
        assert InvalidCredentialsException().status_code == 401

    def test_token_expired_is_401(self) -> None:
        assert TokenExpiredException().status_code == 401

    def test_permission_exception_is_403(self) -> None:
        assert PermissionException().status_code == 403

    def test_insufficient_permissions_is_403(self) -> None:
        assert InsufficientPermissionsException().status_code == 403


class TestIntegrationExceptions:
    def test_integration_exception_is_502(self) -> None:
        assert IntegrationException().status_code == 502

    def test_apollo_api_exception_is_502(self) -> None:
        assert ApolloAPIException().status_code == 502

    def test_sendgrid_api_exception_is_502(self) -> None:
        assert SendGridAPIException().status_code == 502

    def test_openai_api_exception_is_502(self) -> None:
        assert OpenAIAPIException().status_code == 502

    def test_enrichment_rate_limit_error_is_429(self) -> None:
        exc = EnrichmentRateLimitError()
        assert exc.status_code == 429

    def test_email_delivery_error_is_502(self) -> None:
        assert EmailDeliveryError().status_code == 502


class TestBusinessRuleExceptions:
    def test_business_rule_exception_is_400(self) -> None:
        assert BusinessRuleException().status_code == 400

    def test_lead_not_eligible_is_400(self) -> None:
        exc = LeadNotEligibleException()
        assert exc.status_code == 400
        assert exc.code == "LEAD_NOT_ELIGIBLE"

    def test_outreach_pending_review_is_400(self) -> None:
        assert OutreachPendingReviewException().status_code == 400

    def test_enrichment_credit_exception_is_400(self) -> None:
        assert EnrichmentCreditException().status_code == 400


class TestInfrastructureExceptions:
    def test_infrastructure_exception_is_500(self) -> None:
        assert InfrastructureException().status_code == 500

    def test_database_exception_is_500(self) -> None:
        assert DatabaseException().status_code == 500

    def test_cache_exception_is_500(self) -> None:
        assert CacheException().status_code == 500
