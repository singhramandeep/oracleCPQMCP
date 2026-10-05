"""Tests for Fusion CX Adaptive Search helpers and discovery tools."""

from __future__ import annotations

import json
from typing import Any

import httpx
import respx

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.core.cx_client import CXClient
from oracle_cpq_mcp.security.context import reset_session_tool_calls
from oracle_cpq_mcp.security.rate_limit import reset_rate_limits
from oracle_cpq_mcp.security.replay import reset_replay_store
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.cx import register_cx_tools
from oracle_cpq_mcp.tools.cx._common import (
    CX_AS_ENTITY_BY_TOOL,
    _order_by_to_as_sort,
    crm_search_path,
)


class _FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):  # noqa: ANN201
        def decorator(fn):  # noqa: ANN001, ANN202
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def _cx_profile(**kwargs: object) -> CPQProfile:
    defaults: dict[str, object] = {
        "customer_name": "Gentex",
        "customer_id": "GentexFusion",
        "environment": "dev",
        "base_url": "",
        "rest_version": "v19",
        "cpq_enabled": False,
        "cx_enabled": True,
        "cx_url": "https://icchjb-dev2.fa.ocs.oraclecloud.com",
        "cx_auth": "basic",
        "cx_modules": ["Sales", "PRM"],
        "cx_credentials": [
            CredentialSet(username="a.ramachandrappa@gentex.com", password="Welcome11")
        ],
        "read_only": True,
        "debug_mode": False,
    }
    defaults.update(kwargs)
    return CPQProfile(**defaults)  # type: ignore[arg-type]


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


def test_crm_search_path_and_entity_map() -> None:
    assert crm_search_path("metaModels") == (
        "/crmRestApi/searchResources/11.13.18.05/metaModels"
    )
    assert CX_AS_ENTITY_BY_TOOL["list_accounts"] == "Account"
    assert CX_AS_ENTITY_BY_TOOL["list_partners"] == "Partner"
    assert _order_by_to_as_sort("Name:desc") == [
        {"attribute": "Name", "direction": "descending"}
    ]


@respx.mock
def test_list_adaptive_search_metamodels_success() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/searchResources/11.13.18.05/metaModels"
    )
    respx.get(url).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"metaModeluuid": "mm-1", "workflowState": "Active"}],
                "count": 1,
                "hasMore": False,
            },
        )
    )
    profile = _cx_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_cx_tools(mcp, CXClient(profile))
    result = mcp.tools["list_adaptive_search_metamodels"](limit=10)
    assert result["status"] == "ok"
    assert result["data"]["items"][0]["workflowState"] == "Active"


@respx.mock
def test_suggest_adaptive_search_preference_recommend() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/searchResources/11.13.18.05/custom-actions/queries"
    )
    route = respx.post(url).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"localizedValue": "Today", "field": "CreationDate"}],
                "count": 1,
                "hasMore": False,
            },
        )
    )
    profile = _cx_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_cx_tools(mcp, CXClient(profile))
    result = mcp.tools["suggest_adaptive_search"](
        entity="Lead",
        suggestion_type="filter",
        fields="CreationDate",
    )
    assert result["status"] == "ok"
    assert result["data"]["items"][0]["localizedValue"] == "Today"
    assert route.called
    assert route.calls.last.request.headers["Preference"] == "recommend"
    body = json.loads(route.calls.last.request.content.decode())
    assert body["entity"] == "Lead"
    assert body["suggestions"]["type"] == "filter"


@respx.mock
def test_list_accounts_uses_adaptive_search_post() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/searchResources/11.13.18.05/custom-actions/queries"
    )
    route = respx.post(url).mock(
        return_value=httpx.Response(
            200,
            json={"items": [{"PartyNumber": "123"}], "count": 1, "hasMore": False},
        )
    )
    profile = _cx_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_cx_tools(mcp, CXClient(profile))
    result = mcp.tools["list_accounts"](
        limit=10,
        q={"op": "$eq", "attribute": "PartyNumber", "value": "123"},
        order_by="PartyUniqueName:asc",
    )
    assert result["status"] == "ok"
    assert result["data"]["items"][0]["PartyNumber"] == "123"
    assert route.calls.last.request.headers["Preference"] == "transient"
    body = json.loads(route.calls.last.request.content.decode())
    assert body["entity"] == "Account"
    assert body["q"]["op"] == "$eq"
    assert body["sort"][0]["direction"] == "ascending"


def test_prm_only_registers_adaptive_search_not_sales_lists() -> None:
    profile = _cx_profile(cx_modules=["PRM"])
    _configure(profile)
    mcp = _FakeMcp()
    register_cx_tools(mcp, CXClient(profile))
    assert "list_adaptive_search_entities" in mcp.tools
    assert "suggest_adaptive_search" in mcp.tools
    assert "list_partners" in mcp.tools
    assert "list_territories" not in mcp.tools
