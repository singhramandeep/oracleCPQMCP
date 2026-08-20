"""CPQ API error types with credential-safe, structured tool responses."""

from __future__ import annotations

import re
from typing import Any, Literal

ErrorCode = Literal[
    "NOT_FOUND",
    "UNAUTHORIZED",
    "FORBIDDEN",
    "BAD_REQUEST",
    "CONFLICT",
    "RATE_LIMITED",
    "NETWORK_ERROR",
    "READ_ONLY_BLOCKED",
    "VALIDATION_ERROR",
    "INVALID_RESPONSE",
    "CPQ_API_ERROR",
    "INTERNAL_ERROR",
    "POLICY_VIOLATION",
    "AUTHORIZATION_DENIED",
    "CONFIRMATION_REQUIRED",
    "CONFIRMATION_INVALID",
    "SECURITY_VIOLATION",
    "SCHEMA_INTEGRITY_FAILED",
]

_SENSITIVE_PATTERNS = (
    re.compile(r"Basic\s+[A-Za-z0-9+/=]+", re.IGNORECASE),
    re.compile(r"Authorization:\s*[^\s]+", re.IGNORECASE),
    re.compile(r"password[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"passwd[=:]\s*\S+", re.IGNORECASE),
)


def sanitize_message(message: str, password: str | None = None) -> str:
    """Remove credentials and auth headers from error text."""
    result = message
    for pattern in _SENSITIVE_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    if password:
        result = result.replace(password, "[REDACTED]")
    return result


def build_tool_error(
    code: ErrorCode,
    message: str,
    *,
    hint: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the canonical structured error envelope returned by MCP tools."""
    payload: dict[str, Any] = {
        "status": "error",
        "code": code,
        "message": message,
    }
    if hint:
        payload["hint"] = hint
    if details:
        payload["details"] = details
    return payload


def _hint_for_not_found(path: str | None) -> str:
    normalized = path or ""
    if normalized.startswith("/users"):
        return (
            "Verify party_number exists in CPQ (Users API uses partyNumber, not login)."
        )
    if normalized.startswith("/datatables"):
        return "Verify the data table name spelling and casing in CPQ."
    if "/groups/" in normalized:
        return (
            "Verify the group variableName and COMPANY_LOGIN_NAME in the profile .env."
        )
    if normalized.startswith("/adminCustom"):
        return "Verify the data table name; row endpoints use adminCustom{TableName}."
    return "Verify the resource identifier and API path exist in CPQ."


def classify_http_error(
    status_code: int,
    *,
    method: str | None = None,
    path: str | None = None,
    body: Any = None,
) -> tuple[ErrorCode, str]:
    """Map an HTTP status (and CPQ path context) to an error code and actionable hint."""
    _ = body  # reserved for future CPQ-specific body parsing
    if status_code == 401:
        return (
            "UNAUTHORIZED",
            "Check DEV_USERNAME/DEV_PASSWORD (or TEST_/PROD_ equivalents) in profile .env.",
        )
    if status_code == 403:
        return (
            "FORBIDDEN",
            "The integration user may lack permission for this CPQ resource or operation.",
        )
    if status_code == 404:
        return "NOT_FOUND", _hint_for_not_found(path)
    if status_code == 400:
        return (
            "BAD_REQUEST",
            "Review request parameters and JSON body against the CPQ REST API schema.",
        )
    if status_code == 409:
        return (
            "CONFLICT",
            "The resource may already exist or be locked; verify current CPQ state.",
        )
    if status_code == 429:
        return (
            "RATE_LIMITED",
            "CPQ rate limit reached; wait briefly and retry the request.",
        )
    if status_code >= 500:
        return (
            "CPQ_API_ERROR",
            "CPQ server error; retry later or check Oracle CPQ site status.",
        )
    if method and path:
        return (
            "CPQ_API_ERROR",
            f"CPQ returned HTTP {status_code} for {method.upper()} {path}.",
        )
    return "CPQ_API_ERROR", "Review the CPQ API response in details.response."


def exception_to_tool_error(exc: Exception) -> dict[str, Any]:
    """Convert a non-CPQ exception into a structured tool error envelope."""
    if isinstance(exc, ValueError):
        return build_tool_error(
            "VALIDATION_ERROR",
            sanitize_message(str(exc)),
            hint="Check tool input parameters and profile configuration.",
        )
    if isinstance(exc, TypeError):
        return build_tool_error(
            "VALIDATION_ERROR",
            sanitize_message(str(exc)),
            hint="Check tool argument types match the tool schema.",
        )
    return build_tool_error(
        "INTERNAL_ERROR",
        sanitize_message(str(exc)) or "An unexpected error occurred.",
        hint="Retry the request; if it persists, check server logs for details.",
    )


class CPQAPIError(Exception):
    """Raised when Oracle CPQ returns a non-success HTTP response."""

    def __init__(
        self,
        message: str,
        *,
        code: ErrorCode | None = None,
        hint: str | None = None,
        status_code: int | None = None,
        method: str | None = None,
        path: str | None = None,
        url: str | None = None,
        curl_command: str | None = None,
        body: Any = None,
        password: str | None = None,
    ) -> None:
        safe_message = sanitize_message(message, password)
        self.code = code
        self.hint = sanitize_message(hint, password) if hint else None
        self.status_code = status_code
        self.method = method
        self.path = path
        self.url = sanitize_message(url, password) if url else None
        self.curl_command = sanitize_message(curl_command, password) if curl_command else None
        self.body = body
        self._password = password
        super().__init__(safe_message)

    def _resolve_code_and_hint(self) -> tuple[ErrorCode, str]:
        if self.code and self.hint:
            return self.code, self.hint
        if self.code:
            _, default_hint = classify_http_error(
                self.status_code or 0,
                method=self.method,
                path=self.path,
                body=self.body,
            )
            return self.code, self.hint or default_hint
        if self.status_code is not None:
            code, hint = classify_http_error(
                self.status_code,
                method=self.method,
                path=self.path,
                body=self.body,
            )
            return code, self.hint or hint
        if "READ_ONLY mode" in str(self):
            return (
                "READ_ONLY_BLOCKED",
                self.hint
                or "Set READ_ONLY=false in the profile .env to allow create/update/deploy operations.",
            )
        if "Request to CPQ failed" in str(self):
            return (
                "NETWORK_ERROR",
                self.hint
                or "Verify the CPQ base URL, network/VPN connectivity, and site availability.",
            )
        if "Unexpected CPQ response" in str(self):
            return (
                "INVALID_RESPONSE",
                self.hint
                or "CPQ returned an unexpected payload shape; verify REST API version and endpoint.",
            )
        return (
            "CPQ_API_ERROR",
            self.hint or "Review server logs for the CPQ API response; details are not returned to the client.",
        )

    def _build_details(self) -> dict[str, Any]:
        """Build LLM-safe details (no raw CPQ body or curl — those stay in server logs)."""
        details: dict[str, Any] = {}
        if self.status_code is not None:
            details["status_code"] = self.status_code
        if self.method:
            details["method"] = self.method
        if self.path:
            details["path"] = self.path
        if self.url:
            details["url"] = self.url
        return details

    def to_tool_error(self) -> dict[str, Any]:
        """Return the structured error envelope for MCP tool responses."""
        code, hint = self._resolve_code_and_hint()
        return build_tool_error(
            code,
            str(self),
            hint=hint,
            details=self._build_details() or None,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return structured tool error (alias for to_tool_error)."""
        return self.to_tool_error()
