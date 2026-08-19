"""Tests for CPQ error types, classification, and structured tool envelopes."""

from __future__ import annotations

from oracle_cpq_mcp.core.errors import (
    CPQAPIError,
    build_tool_error,
    classify_http_error,
    exception_to_tool_error,
    sanitize_message,
)


def test_build_tool_error_shape() -> None:
    payload = build_tool_error(
        "NOT_FOUND",
        "User not found",
        hint="Verify party_number.",
        details={"status_code": 404},
    )
    assert payload == {
        "status": "error",
        "code": "NOT_FOUND",
        "message": "User not found",
        "hint": "Verify party_number.",
        "details": {"status_code": 404},
    }


def test_classify_http_error_not_found_users() -> None:
    code, hint = classify_http_error(404, method="GET", path="/users/12345")
    assert code == "NOT_FOUND"
    assert "party_number" in hint


def test_classify_http_error_unauthorized() -> None:
    code, hint = classify_http_error(401)
    assert code == "UNAUTHORIZED"
    assert "USERNAME" in hint


def test_classify_http_error_datatables() -> None:
    code, hint = classify_http_error(404, path="/datatables/MyTable")
    assert code == "NOT_FOUND"
    assert "data table" in hint.lower()


def test_cpq_api_error_to_tool_error_includes_details() -> None:
    exc = CPQAPIError(
        "CPQ API error 401 for GET /users",
        code="UNAUTHORIZED",
        hint="Check credentials.",
        status_code=401,
        method="GET",
        path="/users",
        url="https://dev.example.com/rest/v18/users?limit=5",
        curl_command="curl -X GET -u 'user:***' 'https://dev.example.com/rest/v18/users?limit=5'",
        body={"error": "Unauthorized"},
    )
    payload = exc.to_tool_error()
    assert payload["status"] == "error"
    assert payload["code"] == "UNAUTHORIZED"
    assert payload["message"] == "CPQ API error 401 for GET /users"
    assert payload["hint"] == "Check credentials."
    assert payload["details"]["status_code"] == 401
    assert payload["details"]["method"] == "GET"
    assert payload["details"]["path"] == "/users"
    assert payload["details"]["url"] == "https://dev.example.com/rest/v18/users?limit=5"
    assert payload["details"]["curl"] == (
        "curl -X GET -u 'user:***' 'https://dev.example.com/rest/v18/users?limit=5'"
    )
    assert payload["details"]["response"] == {"error": "Unauthorized"}


def test_cpq_api_error_to_dict_is_alias_for_to_tool_error() -> None:
    exc = CPQAPIError("Request to CPQ failed: timeout", code="NETWORK_ERROR")
    assert exc.to_dict() == exc.to_tool_error()


def test_cpq_api_error_derives_code_from_status_when_not_set() -> None:
    exc = CPQAPIError(
        "CPQ API error 404 for GET /users/x",
        status_code=404,
        method="GET",
        path="/users/x",
    )
    payload = exc.to_tool_error()
    assert payload["code"] == "NOT_FOUND"
    assert "hint" in payload


def test_cpq_api_error_sanitizes_password_in_url() -> None:
    exc = CPQAPIError(
        "failed",
        url="https://example.com?password=secret123",
        curl_command="curl -u 'user:***'",
        password="secret123",
    )
    payload = exc.to_tool_error()
    assert "secret123" not in str(payload)
    assert "[REDACTED]" in payload["details"]["url"]


def test_exception_to_tool_error_value_error() -> None:
    payload = exception_to_tool_error(ValueError("party_number is required"))
    assert payload["status"] == "error"
    assert payload["code"] == "VALIDATION_ERROR"
    assert "party_number" in payload["message"]


def test_exception_to_tool_error_generic() -> None:
    payload = exception_to_tool_error(RuntimeError("boom"))
    assert payload["code"] == "INTERNAL_ERROR"


def test_sanitize_message_redacts_basic_auth() -> None:
    raw = "Authorization: Basic dXNlcjpwYXNz"
    assert "[REDACTED]" in sanitize_message(raw)
