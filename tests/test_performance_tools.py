"""Tests for performance log tools and query param building."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.security.exceptions import ValidationSecurityError
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.security.validation import validate_tool_input
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.performance import _list_query_extra, register_performance_tools


@pytest.fixture()
def profile() -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v18",
        company_login_name="_host",
        read_only=True,
    )


def test_list_query_extra_joins_fields_and_orderby() -> None:
    extra = _list_query_extra(
        q_expr="{serverTime:{$gte:100}}",
        fields=["id", "event", "serverTime"],
        orderby=["serverTime:desc", "eventDate:asc"],
    )
    assert extra == {
        "q": "{serverTime:{$gte:100}}",
        "fields": "id,event,serverTime",
        "orderby": "serverTime:desc,eventDate:asc",
    }


def test_list_performance_logs_input_rejects_bad_orderby() -> None:
    with pytest.raises(ValidationSecurityError):
        validate_tool_input(
            "list_performance_logs",
            {"orderby": ["serverTime;drop"]},
        )


def test_get_performance_log_requires_numeric_id() -> None:
    with pytest.raises(ValidationSecurityError):
        validate_tool_input("get_performance_log", {"log_id": "abc"})


def test_list_performance_logs_calls_client_with_filters(profile: CPQProfile) -> None:
    configure_security(
        profile,
        SecuritySettings(
            confirmation_secret="test-secret-key-for-hmac",
            confirmation_ttl_seconds=300,
            schema_integrity_enabled=False,
            max_tool_calls_per_session=50,
            rate_limit_enabled=False,
            audit_enabled=False,
            allow_prod=False,
            max_response_bytes=2_000_000,
            replay_window_seconds=60,
            read_calls_per_minute=120,
            write_calls_per_minute=10,
            privileged_calls_per_minute=5,
        ),
    )

    class FakeMcp:
        def __init__(self) -> None:
            self.tools: dict[str, Any] = {}

        def tool(self, **_kwargs: Any):
            def decorator(fn: Any) -> Any:
                self.tools[fn.__name__] = fn
                return fn

            return decorator

    client = MagicMock()
    client.profile = profile
    client.get.return_value = {
        "items": [{"id": 1, "event": "Logout"}],
        "hasMore": False,
        "offset": 0,
        "limit": 10,
        "count": 1,
    }

    mcp = FakeMcp()
    register_performance_tools(mcp, client)
    result = mcp.tools["list_performance_logs"](
        limit=10,
        offset=0,
        total_results=True,
        q_expr="{event:{$eq:'Logout'}}",
        fields=["id", "event"],
        orderby=["eventDate:desc"],
    )
    assert result["status"] == "ok"
    assert result["data"]["items"][0]["id"] == 1
    client.get.assert_called_once()
    path, kwargs = client.get.call_args
    assert path[0] == "/performanceLogs"
    params = kwargs["params"]
    assert params["limit"] == 10
    assert params["totalResults"] == "true"
    assert params["q"] == "{event:{$eq:'Logout'}}"
    assert params["fields"] == "id,event"
    assert params["orderby"] == "eventDate:desc"


def test_get_performance_log_path(profile: CPQProfile) -> None:
    configure_security(
        profile,
        SecuritySettings(
            confirmation_secret="test-secret-key-for-hmac",
            confirmation_ttl_seconds=300,
            schema_integrity_enabled=False,
            max_tool_calls_per_session=50,
            rate_limit_enabled=False,
            audit_enabled=False,
            allow_prod=False,
            max_response_bytes=2_000_000,
            replay_window_seconds=60,
            read_calls_per_minute=120,
            write_calls_per_minute=10,
            privileged_calls_per_minute=5,
        ),
    )

    class FakeMcp:
        def __init__(self) -> None:
            self.tools: dict[str, Any] = {}

        def tool(self, **_kwargs: Any):
            def decorator(fn: Any) -> Any:
                self.tools[fn.__name__] = fn
                return fn

            return decorator

    client = MagicMock()
    client.profile = profile
    client.get.return_value = {"id": 99, "event": "Login"}
    mcp = FakeMcp()
    register_performance_tools(mcp, client)
    result = mcp.tools["get_performance_log"](log_id="99")
    assert result["status"] == "ok"
    assert result["data"]["id"] == 99
    client.get.assert_called_once_with("/performanceLogs/99")
