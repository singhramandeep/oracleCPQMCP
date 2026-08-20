"""Tests for Parts MCP tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.parts import register_parts_tools


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


@pytest.fixture()
def configured(profile: CPQProfile) -> CPQProfile:
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
    return profile


class FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):
        def decorator(fn: Any) -> Any:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def test_list_parts_calls_get(configured: CPQProfile) -> None:
    client = MagicMock()
    client.profile = configured
    client.get.return_value = {
        "items": [{"id": "FSM1C"}],
        "hasMore": False,
        "offset": 0,
        "limit": 5,
        "count": 1,
    }
    mcp = FakeMcp()
    register_parts_tools(mcp, client)
    result = mcp.tools["list_parts"](limit=5, offset=0)
    client.get.assert_called_once()
    assert client.get.call_args.args[0] == "/parts"
    assert result["status"] == "ok"
    assert result["tool"] == "list_parts"


def test_get_part_calls_path(configured: CPQProfile) -> None:
    client = MagicMock()
    client.profile = configured
    client.get.return_value = {"id": "FSM1C", "partNumber": "FSM1C"}
    mcp = FakeMcp()
    register_parts_tools(mcp, client)
    result = mcp.tools["get_part"](part_id="FSM1C")
    client.get.assert_called_once_with("/parts/FSM1C")
    assert result["status"] == "ok"
    assert result["data"]["partNumber"] == "FSM1C"


def test_search_parts_posts_body(configured: CPQProfile) -> None:
    client = MagicMock()
    client.profile = configured
    client.post.return_value = {"items": [], "hasMore": False, "offset": 0, "limit": 100}
    mcp = FakeMcp()
    register_parts_tools(mcp, client)
    body = {"criteria": {"partNumber": "FSM1C"}}
    result = mcp.tools["search_parts"](body=body)
    client.post.assert_called_once_with("/parts/actions/search", json_body=body)
    assert result["status"] == "ok"
    assert result["tool"] == "search_parts"
