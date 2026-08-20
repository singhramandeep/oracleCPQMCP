"""Recursive redaction of sensitive fields in tool outputs."""

from __future__ import annotations

import json
from typing import Any

SENSITIVE_FIELD_NAMES = frozenset(
    {
        "password",
        "passwd",
        "access_token",
        "refresh_token",
        "client_secret",
        "api_key",
        "authorization",
        "cookie",
        "set-cookie",
        "secret",
        "token",
    }
)

# Keys that must never reach the LLM in error details (raw CPQ blobs / curl with username).
_LLM_UNSAFE_DETAIL_KEYS = frozenset({"response", "curl", "body"})

REDACTED = "[REDACTED]"


def redact_sensitive_data(value: Any) -> Any:
    """Recursively redact sensitive keys from dict/list structures."""
    if isinstance(value, dict):
        return {
            key: REDACTED
            if key.lower() in SENSITIVE_FIELD_NAMES
            else redact_sensitive_data(val)
            for key, val in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]
    return value


def sanitize_error_details(details: dict[str, Any] | None) -> dict[str, Any] | None:
    """Strip LLM-unsafe detail keys and redact remaining sensitive fields."""
    if not details:
        return None
    cleaned = {
        key: value
        for key, value in details.items()
        if key.lower() not in _LLM_UNSAFE_DETAIL_KEYS
    }
    redacted = redact_sensitive_data(cleaned)
    return redacted if isinstance(redacted, dict) and redacted else None


def enforce_response_size(value: Any, max_bytes: int) -> Any:
    """Reject or truncate responses exceeding max byte size."""
    try:
        encoded = json.dumps(value, default=str).encode("utf-8")
    except (TypeError, ValueError):
        return value
    if len(encoded) <= max_bytes:
        return value
    return {
        "status": "error",
        "code": "POLICY_VIOLATION",
        "message": "Response exceeds maximum allowed size.",
        "hint": "Reduce limit/offset or request a narrower data set.",
        "details": {"max_response_bytes": max_bytes, "actual_bytes": len(encoded)},
    }


def sanitize_tool_output(value: Any, *, max_bytes: int) -> Any:
    """Redact sensitive fields and enforce response size limits (including errors)."""
    if isinstance(value, list):
        return [
            sanitize_tool_output(item, max_bytes=max_bytes)
            if isinstance(item, dict)
            else item
            for item in value
        ]
    if isinstance(value, dict):
        if value.get("status") == "error":
            sanitized = dict(value)
            if "details" in sanitized:
                sanitized["details"] = sanitize_error_details(
                    sanitized["details"] if isinstance(sanitized["details"], dict) else None
                )
            return redact_sensitive_data(sanitized)
        redacted = redact_sensitive_data(value)
        return enforce_response_size(redacted, max_bytes)
    return value
