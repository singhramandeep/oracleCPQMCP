"""Tests for Commerce metadata MCP tools."""

from __future__ import annotations

import httpx
import pytest
import respx

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.core.cpq_client import CPQClient
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
    ).mock(return_value=httpx.Response(200, json={"items": [{"variableName": "status"}]}))

    fn = mcp.tools["get_commerce_attributes"]
    result = fn()
    assert route.called
    assert result["status"] == "ok"
    assert result["tool"] == "get_commerce_attributes"
    assert result["data"]["items"][0]["variableName"] == "status"


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
