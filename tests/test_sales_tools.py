"""Tests for Fusion CX Sales MCP tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

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
from oracle_cpq_mcp.tools.cx._common import adf_collection_params, crm_rest_path
from oracle_cpq_mcp.tools.cx.sales import register_sales_tools


class _FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):  # noqa: ANN201
        def decorator(fn):  # noqa: ANN001, ANN202
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def _cx_sales_profile(**kwargs: object) -> CPQProfile:
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


@respx.mock
def test_list_territories_success() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/searchResources/11.13.18.05/custom-actions/queries"
    )
    route = respx.post(url).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "TerritoryId": 1,
                        "Name": "VEC Mountain West",
                        "UniqueTerritoryNumber": "VEC_US_1054",
                    }
                ],
                "count": 1,
                "hasMore": False,
            },
        )
    )
    profile = _cx_sales_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_sales_tools(mcp, CXClient(profile))
    result = mcp.tools["list_territories"](limit=10)
    assert result["status"] == "ok"
    assert result["data"]["count"] == 1
    assert result["data"]["items"][0]["UniqueTerritoryNumber"] == "VEC_US_1054"
    assert "Authorization" in respx.calls.last.request.headers
    assert route.calls.last.request.headers["Preference"] == "transient"


def test_list_territories_requires_sales_module() -> None:
    profile = _cx_sales_profile(cx_modules=["PRM"])
    _configure(profile)
    mcp = _FakeMcp()
    register_sales_tools(mcp, CXClient(profile))
    result = mcp.tools["list_territories"]()
    assert result["status"] == "error"
    assert "Sales" in result["message"]


def test_list_territories_requires_cx_enabled() -> None:
    profile = _cx_sales_profile(cx_enabled=False)
    _configure(profile)
    mcp = _FakeMcp()
    register_sales_tools(mcp, CXClient(profile))
    result = mcp.tools["list_territories"]()
    assert result["status"] == "error"
    assert "not enabled" in result["message"].lower()


def test_register_cx_tools_gates_on_enabled_modules() -> None:
    sales_profile = _cx_sales_profile()
    _configure(sales_profile)
    mcp_sales = _FakeMcp()
    register_cx_tools(mcp_sales, CXClient(sales_profile))
    assert "list_territories" in mcp_sales.tools

    prm_only = _cx_sales_profile(cx_modules=["PRM"])
    _configure(prm_only)
    mcp_prm = _FakeMcp()
    register_cx_tools(mcp_prm, CXClient(prm_only))
    assert "list_territories" not in mcp_prm.tools

    disabled = _cx_sales_profile(cx_enabled=False)
    _configure(disabled)
    mcp_off = _FakeMcp()
    register_cx_tools(mcp_off, CXClient(disabled))
    assert "list_territories" not in mcp_off.tools


def test_crm_rest_path_and_adf_collection_params() -> None:
    assert crm_rest_path("territories") == (
        "/crmRestApi/resources/11.13.18.05/territories"
    )
    params = adf_collection_params(
        limit=10,
        offset=20,
        q="Name LIKE 'VEC%'",
        order_by="Name:asc",
        only_data=False,
        total_results=True,
    )
    assert params["limit"] == 10
    assert params["offset"] == 20
    assert params["q"] == "Name LIKE 'VEC%'"
    assert params["orderBy"] == "Name:asc"
    assert params["onlyData"] == "false"
    assert params["totalResults"] == "true"
    assert "finder" not in params

@respx.mock
def test_list_accounts_success() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/searchResources/11.13.18.05/custom-actions/queries"
    )
    respx.post(url).mock(
        return_value=httpx.Response(
            200,
            json={"items": [{"PartyNumber": "123"}], "count": 1, "hasMore": False},
        )
    )
    profile = _cx_sales_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_sales_tools(mcp, CXClient(profile))
    result = mcp.tools["list_accounts"](limit=10)
    assert result["status"] == "ok"
    assert result["data"]["items"][0]["PartyNumber"] == "123"


@respx.mock
def test_get_territory_success() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/resources/11.13.18.05/territories/TV1"
    )
    respx.get(url).mock(
        return_value=httpx.Response(200, json={"TerritoryId": 1, "Name": "West"}),
    )
    profile = _cx_sales_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_sales_tools(mcp, CXClient(profile))
    result = mcp.tools["get_territory"](territory_version_id="TV1")
    assert result["status"] == "ok"
    assert result["data"]["Name"] == "West"


def test_register_cx_tools_registers_both_modules() -> None:
    profile = _cx_sales_profile(cx_modules=["Sales", "PRM"])
    _configure(profile)
    mcp = _FakeMcp()
    register_cx_tools(mcp, CXClient(profile))
    assert "list_territories" in mcp.tools
    assert "list_partners" in mcp.tools


@respx.mock
def test_list_account_addresses_success() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/resources/11.13.18.05/accounts/CDRM_1/child/Address"
    )
    respx.get(url).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"AddressNumber": "ADDR1", "City": "Holland"}],
                "count": 1,
                "hasMore": False,
            },
        )
    )
    profile = _cx_sales_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_sales_tools(mcp, CXClient(profile))
    result = mcp.tools["list_account_addresses"](party_number="CDRM_1")
    assert result["status"] == "ok"
    assert result["data"]["items"][0]["AddressNumber"] == "ADDR1"


@respx.mock
def test_get_account_address_success() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/resources/11.13.18.05/accounts/CDRM_1/child/Address/ADDR1"
    )
    respx.get(url).mock(
        return_value=httpx.Response(
            200,
            json={"AddressNumber": "ADDR1", "City": "Holland"},
        )
    )
    profile = _cx_sales_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_sales_tools(mcp, CXClient(profile))
    result = mcp.tools["get_account_address"](
        party_number="CDRM_1", address_number="ADDR1"
    )
    assert result["status"] == "ok"
    assert result["data"]["City"] == "Holland"


@respx.mock
def test_list_opportunities_success() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/searchResources/11.13.18.05/custom-actions/queries"
    )
    respx.post(url).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"OptyNumber": "OPTY1", "Name": "Deal A"}],
                "count": 1,
                "hasMore": False,
            },
        )
    )
    profile = _cx_sales_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_sales_tools(mcp, CXClient(profile))
    result = mcp.tools["list_opportunities"](limit=10)
    assert result["status"] == "ok"
    assert result["data"]["items"][0]["OptyNumber"] == "OPTY1"


@respx.mock
def test_get_opportunity_and_team_success() -> None:
    base = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/resources/11.13.18.05/opportunities/OPTY1"
    )
    respx.get(base).mock(
        return_value=httpx.Response(
            200,
            json={"OptyNumber": "OPTY1", "Name": "Deal A"},
        )
    )
    respx.get(f"{base}/child/OpportunityTeam").mock(
        return_value=httpx.Response(
            200,
            json={"items": [{"PartyName": "Rep"}], "count": 1, "hasMore": False},
        )
    )
    profile = _cx_sales_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_sales_tools(mcp, CXClient(profile))
    opty = mcp.tools["get_opportunity"](opty_number="OPTY1")
    assert opty["status"] == "ok"
    assert opty["data"]["Name"] == "Deal A"
    team = mcp.tools["list_opportunity_team"](opty_number="OPTY1")
    assert team["status"] == "ok"
    assert team["data"]["items"][0]["PartyName"] == "Rep"


def test_register_sales_tools_includes_new_account_and_opportunity_tools() -> None:
    profile = _cx_sales_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_sales_tools(mcp, CXClient(profile))
    for name in (
        "list_account_attachments",
        "get_account_attachment",
        "list_account_primary_addresses",
        "get_account_primary_address",
        "list_opportunity_attachments",
        "get_opportunity_attachment",
        "list_opportunity_contacts",
        "get_opportunity_contact",
        "list_opportunity_revenue_partners",
        "get_opportunity_revenue_partner",
    ):
        assert name in mcp.tools

