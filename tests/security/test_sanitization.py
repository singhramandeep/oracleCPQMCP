"""Tests for output sanitization."""

from __future__ import annotations

from oracle_cpq_mcp.security.sanitization import (
    redact_sensitive_data,
    sanitize_error_details,
    sanitize_tool_output,
)


def test_redact_password_in_nested_dict() -> None:
    payload = {"login": "alice", "credentials": {"password": "secret123"}}
    redacted = redact_sensitive_data(payload)
    assert redacted["login"] == "alice"
    assert redacted["credentials"]["password"] == "[REDACTED]"


def test_sanitize_tool_output_preserves_success_fields() -> None:
    payload = {"partyNumber": "123", "password": "hidden"}
    result = sanitize_tool_output(payload, max_bytes=10000)
    assert result["password"] == "[REDACTED]"


def test_sanitize_tool_output_redacts_error_payloads() -> None:
    payload = {
        "status": "error",
        "code": "CPQ_API_ERROR",
        "message": "failed",
        "details": {
            "status_code": 500,
            "response": {"password": "leaked", "token": "abc"},
            "curl": "curl -u 'user:***'",
        },
    }
    result = sanitize_tool_output(payload, max_bytes=10000)
    assert result["status"] == "error"
    assert "response" not in (result.get("details") or {})
    assert "curl" not in (result.get("details") or {})
    assert result["details"]["status_code"] == 500


def test_sanitize_error_details_strips_unsafe_keys() -> None:
    details = sanitize_error_details(
        {"status_code": 404, "response": {"secret": "x"}, "curl": "curl ...", "path": "/users"}
    )
    assert details == {"status_code": 404, "path": "/users"}
