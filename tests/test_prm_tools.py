"""Tests for Fusion CX PRM MCP tools."""

from __future__ import annotations

from typing import Any
from urllib.parse import unquote

import httpx
import pytest
import respx

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.core.cx_client import CXClient
from oracle_cpq_mcp.security.context import reset_session_tool_calls
from oracle_cpq_mcp.security.rate_limit import reset_rate_limits
from oracle_cpq_mcp.security.replay import reset_replay_store
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.cx import register_cx_tools
from oracle_cpq_mcp.tools.cx.prm import register_prm_tools


class _FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def _cx_prm_profile(**kwargs: object) -> CPQProfile:
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
        "cx_modules": ["PRM"],
        "cx_credentials": [
            CredentialSet(username="user@example.com", password="secret")
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
def test_list_partners_success() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/resources/11.13.18.05/partners"
    )
    respx.get(url).mock(
        return_value=httpx.Response(
            200,
            json={"items": [{"CompanyNumber": "P1"}], "count": 1, "hasMore": False},
        )
    )
    profile = _cx_prm_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_prm_tools(mcp, CXClient(profile))
    result = mcp.tools["list_partners"](limit=5)
    assert result["status"] == "ok"
    assert result["data"]["items"][0]["CompanyNumber"] == "P1"


def test_list_partners_requires_prm_module() -> None:
    profile = _cx_prm_profile(cx_modules=["Sales"])
    _configure(profile)
    mcp = _FakeMcp()
    register_prm_tools(mcp, CXClient(profile))
    result = mcp.tools["list_partners"]()
    assert result["status"] == "error"
    assert "PRM" in result["message"]
    lov = mcp.tools["list_partner_lov"](
        company_number="2001",
        lov_name="PartnerProfilePEO_LOVVA_For_gnx_sls_Status_c",
    )
    assert lov["status"] == "error"
    assert "PRM" in lov["message"]


def test_register_cx_tools_registers_prm_when_enabled() -> None:
    profile = _cx_prm_profile(cx_modules=["PRM"])
    _configure(profile)
    mcp = _FakeMcp()
    register_cx_tools(mcp, CXClient(profile))
    assert "list_partners" in mcp.tools
    assert "list_territories" not in mcp.tools
    assert "list_partner_contact_user_details" in mcp.tools
    assert "list_partner_programs" in mcp.tools
    assert "list_partner_lov" in mcp.tools


@respx.mock
def test_list_partner_contact_user_details_success() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/resources/11.13.18.05/partnerContacts/CDRM_7102/child/userdetails"
    )
    respx.get(url).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"Username": "company@inflight.com", "UserAccountStatus": "REQUEST"}],
                "count": 1,
                "hasMore": False,
            },
        )
    )
    profile = _cx_prm_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_prm_tools(mcp, CXClient(profile))
    result = mcp.tools["list_partner_contact_user_details"](party_number="CDRM_7102")
    assert result["status"] == "ok"
    assert result["data"]["items"][0]["Username"] == "company@inflight.com"


@respx.mock
def test_get_partner_contact_user_detail_encodes_username() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/resources/11.13.18.05/partnerContacts/CDRM_7102"
        "/child/userdetails/company%40inflight.com"
    )
    respx.get(url).mock(
        return_value=httpx.Response(
            200,
            json={"Username": "company@inflight.com", "UserAccountStatus": "REQUEST"},
        )
    )
    profile = _cx_prm_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_prm_tools(mcp, CXClient(profile))
    result = mcp.tools["get_partner_contact_user_detail"](
        party_number="CDRM_7102",
        username="company@inflight.com",
    )
    assert result["status"] == "ok"
    assert result["data"]["Username"] == "company@inflight.com"


@respx.mock
def test_list_partner_programs_success() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/resources/11.13.18.05/partnerPrograms"
    )
    respx.get(url).mock(
        return_value=httpx.Response(
            200,
            json={"items": [{"ProgramNumber": "PROG1"}], "count": 1, "hasMore": False},
        )
    )
    profile = _cx_prm_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_prm_tools(mcp, CXClient(profile))
    result = mcp.tools["list_partner_programs"](limit=10)
    assert result["status"] == "ok"
    assert result["data"]["items"][0]["ProgramNumber"] == "PROG1"


@respx.mock
def test_list_partner_lov_success() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/resources/11.13.18.05/partners/2001"
        "/lov/PartnerProfilePEO_LOVVA_For_gnx_sls_Status_c"
    )
    respx.get(url).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "LookupType": "APPROVAL_STATUS",
                        "LookupCode": "SUBMITTED_CREDIT",
                        "Meaning": "Submittted To Credit Manager",
                    }
                ],
                "count": 1,
                "hasMore": False,
            },
        )
    )
    profile = _cx_prm_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_prm_tools(mcp, CXClient(profile))
    result = mcp.tools["list_partner_lov"](
        company_number="2001",
        lov_name="PartnerProfilePEO_LOVVA_For_gnx_sls_Status_c",
    )
    assert result["status"] == "ok"
    assert result["data"]["items"][0]["LookupCode"] == "SUBMITTED_CREDIT"


@respx.mock
def test_list_partner_lov_lookup_code_sets_q() -> None:
    url = (
        "https://icchjb-dev2.fa.ocs.oraclecloud.com"
        "/crmRestApi/resources/11.13.18.05/partners/2001"
        "/lov/PartnerProfilePEO_LOVVA_For_gnx_sls_Status_c"
    )
    route = respx.get(url).mock(
        return_value=httpx.Response(
            200,
            json={"items": [], "count": 0, "hasMore": False},
        )
    )
    profile = _cx_prm_profile()
    _configure(profile)
    mcp = _FakeMcp()
    register_prm_tools(mcp, CXClient(profile))
    result = mcp.tools["list_partner_lov"](
        company_number="2001",
        lov_name="PartnerProfilePEO_LOVVA_For_gnx_sls_Status_c",
        lookup_code="SUBMITTED_CREDIT",
    )
    assert result["status"] == "ok"
    assert 'LookupCode="SUBMITTED_CREDIT"' in unquote(str(route.calls.last.request.url))


def test_list_partner_lov_rejects_invalid_lov_name() -> None:
    from pydantic import ValidationError

    from oracle_cpq_mcp.security.validation import ListPartnerLovInput

    with pytest.raises(ValidationError):
        ListPartnerLovInput(company_number="2001", lov_name="../secret")
    with pytest.raises(ValidationError):
        ListPartnerLovInput(company_number="2001", lov_name="bad/name")
