"""Tests for the safe tool registration wrapper."""

from __future__ import annotations

from typing import Any

import pytest

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.core.errors import CPQAPIError
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import (
    _returns_list,
    _wrap_if_list_return,
    configure_security,
    register_tool,
)


@pytest.fixture(autouse=True)
def _setup_security() -> None:
    profile = CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v18",
        company_login_name="_host",
        read_only=False,
    )
    settings = SecuritySettings(
        confirmation_secret="test-secret",
        confirmation_ttl_seconds=300,
        schema_integrity_enabled=False,
        max_tool_calls_per_session=20,
        rate_limit_enabled=False,
        audit_enabled=False,
        allow_prod=False,
        max_response_bytes=2_000_000,
        replay_window_seconds=60,
        read_calls_per_minute=120,
        write_calls_per_minute=10,
        privileged_calls_per_minute=5,
    )
    configure_security(profile, settings)


def test_returns_list_detects_list_annotation() -> None:
    def list_tool() -> list[dict[str, Any]]:
        return []

    def dict_tool() -> dict[str, Any]:
        return {}

    assert _returns_list(list_tool) is True
    assert _returns_list(dict_tool) is False


def test_wrap_if_list_return_for_list_tools() -> None:
    def list_tool() -> list[dict[str, Any]]:
        return []

    error = {"status": "error", "code": "INTERNAL_ERROR", "message": "boom"}
    wrapped = _wrap_if_list_return(list_tool, error)
    assert wrapped == [error]


def test_wrap_if_list_return_for_dict_tools() -> None:
    def dict_tool() -> dict[str, Any]:
        return {}

    error = {"status": "error", "code": "NOT_FOUND", "message": "missing"}
    assert _wrap_if_list_return(dict_tool, error) == error


def test_register_tool_passes_output_schema() -> None:
    captured: dict[str, Any] = {}

    class FakeMcp:
        def tool(self, **kwargs: Any):
            captured.update(kwargs)

            def decorator(fn: Any) -> Any:
                return fn

            return decorator

    def ok_tool(party_number: str) -> dict[str, Any]:
        return {"partyNumber": party_number}

    ok_tool.__doc__ = "test"
    register_tool(FakeMcp(), ok_tool, "get_user")
    assert "output_schema" in captured
    assert "oneOf" in captured["output_schema"]


def test_register_tool_catches_cpq_api_error() -> None:
    class FakeMcp:
        def tool(self, **kwargs: Any):
            def decorator(fn: Any) -> Any:
                return fn

            return decorator

    def failing_tool(party_number: str) -> dict[str, Any]:
        raise CPQAPIError(
            "CPQ API error 404 for GET /users/x",
            status_code=404,
            method="GET",
            path="/users/x",
        )

    failing_tool.__doc__ = "test"
    wrapped = register_tool(FakeMcp(), failing_tool, "get_user")
    result = wrapped(party_number="user123")
    assert result["status"] == "error"
    assert result["code"] == "NOT_FOUND"


def test_register_tool_catches_value_error() -> None:
    class FakeMcp:
        def tool(self, **kwargs: Any):
            def decorator(fn: Any) -> Any:
                return fn

            return decorator

    def bad_input(party_number: str) -> dict[str, Any]:
        raise ValueError("party_number is required")

    bad_input.__doc__ = "test"
    wrapped = register_tool(FakeMcp(), bad_input, "get_user")
    result = wrapped(party_number="user123")
    assert result["status"] == "error"
    assert result["code"] == "VALIDATION_ERROR"


def test_register_tool_catches_unexpected_exception() -> None:
    class FakeMcp:
        def tool(self, **kwargs: Any):
            def decorator(fn: Any) -> Any:
                return fn

            return decorator

    def boom(party_number: str) -> dict[str, Any]:
        raise RuntimeError("unexpected")

    boom.__doc__ = "test"
    wrapped = register_tool(FakeMcp(), boom, "get_user")
    result = wrapped(party_number="user123")
    assert result["status"] == "error"
    assert result["code"] == "INTERNAL_ERROR"
