"""Tests for output sanitization."""

from __future__ import annotations

from oracle_cpq_mcp.security.sanitization import redact_sensitive_data, sanitize_tool_output


def test_redact_password_in_nested_dict() -> None:
    payload = {"login": "alice", "credentials": {"password": "secret123"}}
    redacted = redact_sensitive_data(payload)
    assert redacted["login"] == "alice"
    assert redacted["credentials"]["password"] == "[REDACTED]"


def test_sanitize_tool_output_preserves_success_fields() -> None:
    payload = {"partyNumber": "123", "password": "hidden"}
    result = sanitize_tool_output(payload, max_bytes=10000)
    assert result["password"] == "[REDACTED]"
