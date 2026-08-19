"""Security-layer exceptions mapped to structured tool errors."""

from __future__ import annotations

from oracle_cpq_mcp.core.errors import ErrorCode, build_tool_error


class SecurityError(Exception):
    """Base class for security policy violations."""

    code: ErrorCode = "SECURITY_VIOLATION"
    hint: str | None = None

    def to_tool_error(self) -> dict:
        return build_tool_error(self.code, str(self), hint=self.hint)


class PolicyViolationError(SecurityError):
    code: ErrorCode = "POLICY_VIOLATION"


class AuthorizationDeniedError(SecurityError):
    code: ErrorCode = "AUTHORIZATION_DENIED"
    hint = "This operation is not permitted under the current security policy."


class ConfirmationRequiredError(SecurityError):
    code: ErrorCode = "CONFIRMATION_REQUIRED"
    hint = "Obtain a confirmation_token from preflight, then retry with dry_run=false."


class ConfirmationInvalidError(SecurityError):
    code: ErrorCode = "CONFIRMATION_INVALID"
    hint = "Confirmation token is missing, expired, or does not match the operation."


class RateLimitedError(SecurityError):
    code: ErrorCode = "RATE_LIMITED"
    hint = "Rate limit exceeded; wait and retry."


class ValidationSecurityError(SecurityError):
    code: ErrorCode = "VALIDATION_ERROR"


class SchemaIntegrityError(SecurityError):
    code: ErrorCode = "SECURITY_VIOLATION"
    hint = "Tool definition hash does not match the approved manifest."
