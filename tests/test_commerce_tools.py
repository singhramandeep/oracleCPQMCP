"""Tests for Commerce metadata MCP tools."""

from __future__ import annotations

import httpx
import pytest
import respx

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.commerce import register_commerce_tools


@pytest.fixture()
def profile() -> CPQProfile:
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


@pytest.fixture(autouse=True)
def _security(profile: CPQProfile) -> None:
    settings = SecuritySettings(
        confirmation_secret="test-secret",
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
    )
    configure_security(profile, settings)


@pytest.fixture()
def client(profile: CPQProfile) -> CPQClient:
    return CPQClient(profile)


class _McpStub:
    def __init__(self) -> None:
        self.tools: dict[str, object] = {}

    def tool(self, **kwargs: object):
        def decorator(fn: object) -> object:
            self.tools[getattr(fn, "__name__")] = fn
            return fn

        return decorator


@respx.mock
def test_get_commerce_attributes_uses_profile_process(client: CPQClient) -> None:
    mcp = _McpStub()
    register_commerce_tools(mcp, client)
    route = respx.get(
        "https://dev.example.com/rest/v19/commerceProcesses/oraclecpqo/documents/transaction/attributes"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"variableName": "status"}],
                "hasMore": False,
                "offset": 0,
                "limit": 100,
            },
        )
    )

    fn = mcp.tools["get_commerce_attributes"]
    result = fn()
    assert route.called
    assert result["status"] == "ok"
    assert result["tool"] == "get_commerce_attributes"
    assert result["data"]["items"][0]["variableName"] == "status"
    assert result["environment"] == "dev"
    assert result["customer_id"] == "test"
    assert "retrieved_at" in result


@respx.mock
def test_get_commerce_attributes_pagination_hint(client: CPQClient) -> None:
    mcp = _McpStub()
    register_commerce_tools(mcp, client)
    respx.get(
        "https://dev.example.com/rest/v19/commerceProcesses/oraclecpqo/documents/transaction/attributes"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"variableName": "a"}],
                "hasMore": True,
                "offset": 0,
                "limit": 50,
                "count": 50,
            },
        )
    )

    fn = mcp.tools["get_commerce_attributes"]
    result = fn(limit=50, offset=0)
    assert result["pagination"]["nextOffset"] == 50


@respx.mock
def test_get_line_actions_supports_expand_all(client: CPQClient) -> None:
    mcp = _McpStub()
    register_commerce_tools(mcp, client)
    route = respx.get(
        "https://dev.example.com/rest/v19/commerceProcesses/oraclecpqo/documents/transactionLine/actionDefs"
    ).mock(return_value=httpx.Response(200, json={"items": []}))

    fn = mcp.tools["get_line_actions"]
    fn(expand_all=True)
    assert route.called
    assert route.calls.last.request.url.params.get("expand") == "all*"
    assert route.calls.last.request.url.params.get("limit") == "100"


@respx.mock
def test_get_commerce_attribute_single(client: CPQClient) -> None:
    mcp = _McpStub()
    register_commerce_tools(mcp, client)
    route = respx.get(
        "https://dev.example.com/rest/v19/commerceProcesses/oraclecpqo/"
        "documents/transaction/attributes/status_t"
    ).mock(return_value=httpx.Response(200, json={"variableName": "status_t"}))

    fn = mcp.tools["get_commerce_attribute"]
    result = fn(attribute_var_name="status_t")
    assert route.called
    assert result["status"] == "ok"
    assert result["data"]["variableName"] == "status_t"


@respx.mock
def test_list_commerce_processes(client: CPQClient) -> None:
    mcp = _McpStub()
    register_commerce_tools(mcp, client)
    route = respx.get("https://dev.example.com/rest/v19/commerceProcessSetups").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"variableName": "oraclecpqo"}],
                "hasMore": False,
                "offset": 0,
                "limit": 100,
            },
        )
    )

    fn = mcp.tools["list_commerce_processes"]
    result = fn(limit=100, offset=0)
    assert route.called
    assert result["status"] == "ok"
    assert result["tool"] == "list_commerce_processes"
