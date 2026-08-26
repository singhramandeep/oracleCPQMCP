"""Unit tests for saved search MCP tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from oracle_cpq_mcp.core.commerce_paths import commerce_transaction_search_resource
from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.security.context import reset_session_tool_calls
from oracle_cpq_mcp.security.rate_limit import reset_rate_limits
from oracle_cpq_mcp.security.replay import reset_replay_store
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.saved_searches import register_saved_search_tools


class _FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):  # noqa: ANN201
        def decorator(fn):  # noqa: ANN001, ANN202
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def _profile() -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v19",
        commerce_process_var_names=["oraclecpqo"],
        read_only=True,
    )


def _configure(profile: CPQProfile) -> None:
    reset_session_tool_calls()
    reset_rate_limits()
    reset_replay_store()
    configure_security(
        profile,
        SecuritySettings(
            confirmation_secret="test-secret-key-for-hmac",
            confirmation_ttl_seconds=300,
            schema_integrity_enabled=False,
            max_tool_calls_per_session=100,
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


def test_commerce_transaction_search_resource() -> None:
    assert (
        commerce_transaction_search_resource("oraclecpqo")
        == "commerceDocumentsOraclecpqoTransaction"
    )


def test_list_saved_searches_uses_profile_process() -> None:
    profile = _profile()
    _configure(profile)
    client = MagicMock()
    client.profile = profile
    client.get.return_value = {"items": [], "hasMore": False, "count": 0}
    mcp = _FakeMcp()
    register_saved_search_tools(mcp, client)  # type: ignore[arg-type]
    result = mcp.tools["list_saved_searches"](limit=10, offset=0)
    assert result["status"] == "ok"
    client.get.assert_called_with(
        "/searchResources/commerceDocumentsOraclecpqoTransaction",
        params={
            "limit": 10,
            "offset": 0,
            "totalResults": "true",
            "showAll": "VISIBLE",
        },
    )


def test_list_saved_searches_explicit_resource() -> None:
    profile = _profile()
    _configure(profile)
    client = MagicMock()
    client.profile = profile
    client.get.return_value = {"items": [{"name": "My Quotes"}], "hasMore": False}
    mcp = _FakeMcp()
    register_saved_search_tools(mcp, client)  # type: ignore[arg-type]
    mcp.tools["list_saved_searches"](
        resource_var_name="commerceDocumentsOraclecpqoTransaction",
        show_all="ALL",
        limit=5,
        offset=0,
    )
    client.get.assert_called_with(
        "/searchResources/commerceDocumentsOraclecpqoTransaction",
        params={
            "limit": 5,
            "offset": 0,
            "totalResults": "true",
            "showAll": "ALL",
        },
    )


def test_get_saved_search() -> None:
    profile = _profile()
    _configure(profile)
    client = MagicMock()
    client.profile = profile
    client.get.return_value = {"name": "Vision Quotes", "savedSearchNumber": 38678835}
    mcp = _FakeMcp()
    register_saved_search_tools(mcp, client)  # type: ignore[arg-type]
    result = mcp.tools["get_saved_search"](search_id=38678835)
    assert result["status"] == "ok"
    client.get.assert_called_with(
        "/searchResources/commerceDocumentsOraclecpqoTransaction/38678835"
    )
