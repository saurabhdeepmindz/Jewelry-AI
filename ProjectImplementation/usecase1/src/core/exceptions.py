"""Exception hierarchy for Jewelry AI platform.

All application exceptions inherit from BaseAppException.
FastAPI exception handlers translate these to structured JSON responses.

HTTP status codes:
  422 — ValidationException     (invalid input)
  404 — NotFoundException       (resource not found)
  409 — ConflictException       (duplicate or state conflict)
  401 — AuthException           (unauthenticated / token invalid)
  403 — PermissionException     (authenticated but unauthorised)
  502 — IntegrationException    (external API failure)
  400 — BusinessRuleException   (domain rule violation)
  500 — InfrastructureException (internal platform error)
"""


class BaseAppException(RuntimeError):
    """Base class for all application exceptions."""

    status_code: int = 500
    default_message: str = "An unexpected error occurred."
    default_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        detail: str | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.detail = detail
        super().__init__(self.message)


# ── 422 Validation ────────────────────────────────────────────────────────────

class ValidationException(BaseAppException):
    status_code = 422
    default_message = "Validation failed."
    default_code = "VALIDATION_ERROR"


class LeadValidationException(ValidationException):
    default_message = "Lead data failed validation."
    default_code = "LEAD_VALIDATION_ERROR"


class InventoryValidationException(ValidationException):
    default_message = "Inventory data failed validation."
    default_code = "INVENTORY_VALIDATION_ERROR"


class OutreachValidationException(ValidationException):
    default_message = "Outreach data failed validation."
    default_code = "OUTREACH_VALIDATION_ERROR"


# ── 404 Not Found ─────────────────────────────────────────────────────────────

class NotFoundException(BaseAppException):
    status_code = 404
    default_message = "Resource not found."
    default_code = "NOT_FOUND"


class LeadNotFoundException(NotFoundException):
    default_message = "Lead not found."
    default_code = "LEAD_NOT_FOUND"


class InventoryNotFoundException(NotFoundException):
    default_message = "Inventory item not found."
    default_code = "INVENTORY_NOT_FOUND"


class ContactNotFoundException(NotFoundException):
    default_message = "Contact not found."
    default_code = "CONTACT_NOT_FOUND"


class UserNotFoundException(NotFoundException):
    default_message = "User not found."
    default_code = "USER_NOT_FOUND"


# ── 409 Conflict ─────────────────────────────────────────────────────────────

class ConflictException(BaseAppException):
    status_code = 409
    default_message = "Conflict — resource already exists or is in an incompatible state."
    default_code = "CONFLICT"


class DuplicateLeadException(ConflictException):
    default_message = "A lead with this company name already exists."
    default_code = "DUPLICATE_LEAD"


class OutreachAlreadySentException(ConflictException):
    default_message = "This outreach message has already been sent."
    default_code = "OUTREACH_ALREADY_SENT"


class ImmutableRecordError(ConflictException):
    default_message = "This record is immutable and cannot be modified or deleted."
    default_code = "IMMUTABLE_RECORD"


# ── 401 Auth ──────────────────────────────────────────────────────────────────

class AuthException(BaseAppException):
    status_code = 401
    default_message = "Authentication required."
    default_code = "AUTHENTICATION_REQUIRED"


class InvalidCredentialsException(AuthException):
    default_message = "Invalid email or password."
    default_code = "INVALID_CREDENTIALS"


class TokenExpiredException(AuthException):
    default_message = "Access token has expired."
    default_code = "TOKEN_EXPIRED"


# ── 403 Permission ────────────────────────────────────────────────────────────

class PermissionException(BaseAppException):
    status_code = 403
    default_message = "You do not have permission to perform this action."
    default_code = "FORBIDDEN"


class InsufficientPermissionsException(PermissionException):
    default_message = "Your role does not allow this operation."
    default_code = "INSUFFICIENT_PERMISSIONS"


# ── 502 Integration ───────────────────────────────────────────────────────────

class IntegrationException(BaseAppException):
    status_code = 502
    default_message = "External service returned an error."
    default_code = "INTEGRATION_ERROR"


class ApolloAPIException(IntegrationException):
    default_message = "Apollo.io API returned an error."
    default_code = "APOLLO_API_ERROR"


class HunterAPIException(IntegrationException):
    default_message = "Hunter.io API returned an error."
    default_code = "HUNTER_API_ERROR"


class ProxycurlAPIException(IntegrationException):
    default_message = "Proxycurl API returned an error."
    default_code = "PROXYCURL_API_ERROR"


class SendGridAPIException(IntegrationException):
    default_message = "SendGrid API returned an error."
    default_code = "SENDGRID_API_ERROR"


class OpenAIAPIException(IntegrationException):
    default_message = "OpenAI API returned an error."
    default_code = "OPENAI_API_ERROR"


class EnrichmentRateLimitError(IntegrationException):
    status_code = 429
    default_message = "Enrichment API rate limit exceeded."
    default_code = "ENRICHMENT_RATE_LIMIT"


class EmailDeliveryError(IntegrationException):
    default_message = "Failed to deliver email via SendGrid."
    default_code = "EMAIL_DELIVERY_ERROR"


# ── 400 Business Rule ─────────────────────────────────────────────────────────

class BusinessRuleException(BaseAppException):
    status_code = 400
    default_message = "Business rule violation."
    default_code = "BUSINESS_RULE_VIOLATION"


class LeadNotEligibleException(BusinessRuleException):
    default_message = "Lead is not eligible — no matching inventory items found."
    default_code = "LEAD_NOT_ELIGIBLE"


class OutreachPendingReviewException(BusinessRuleException):
    default_message = "Outreach message is pending review and cannot be sent yet."
    default_code = "OUTREACH_PENDING_REVIEW"


class EnrichmentCreditException(BusinessRuleException):
    default_message = "Lead has already been enriched. Re-enrichment is not allowed."
    default_code = "ENRICHMENT_ALREADY_DONE"


# ── 500 Infrastructure ────────────────────────────────────────────────────────

class InfrastructureException(BaseAppException):
    status_code = 500
    default_message = "Internal platform error."
    default_code = "INFRASTRUCTURE_ERROR"


class DatabaseException(InfrastructureException):
    default_message = "Database operation failed."
    default_code = "DATABASE_ERROR"


class CacheException(InfrastructureException):
    default_message = "Cache operation failed."
    default_code = "CACHE_ERROR"
