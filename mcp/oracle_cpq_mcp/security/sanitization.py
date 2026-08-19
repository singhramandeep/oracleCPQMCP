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
    """Redact sensitive fields and enforce response size limits."""
    if isinstance(value, list):
        return [
            sanitize_tool_output(item, max_bytes=max_bytes)
            if isinstance(item, dict)
            else item
            for item in value
        ]
    if isinstance(value, dict):
        if value.get("status") == "error":
            return value
        redacted = redact_sensitive_data(value)
        return enforce_response_size(redacted, max_bytes)
    return value
