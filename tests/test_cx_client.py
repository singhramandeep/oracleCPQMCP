"""Tests for Fusion CX HTTP helper."""

from __future__ import annotations

import httpx
import respx

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.core.cx_client import CXAPIError, CXClient


def _cx_profile(**kwargs: object) -> CPQProfile:
    defaults: dict[str, object] = {
        "customer_name": "CX",
        "customer_id": "cx",
        "environment": "dev",
        "base_url": "",
        "rest_version": "v19",
        "cpq_enabled": False,
        "cx_enabled": True,
        "cx_url": "https://cx.example.com",
        "cx_auth": "basic",
        "cx_modules": ["Sales"],
        "cx_credentials": [CredentialSet(username="u1", password="p1")],
        "read_only": True,
        "debug_mode": False,
    }
    defaults.update(kwargs)
    return CPQProfile(**defaults)  # type: ignore[arg-type]


@respx.mock
def test_cx_client_basic_get() -> None:
    respx.get("https://cx.example.com/crmRestApi/resources/11.13.18.05/territories").mock(
        return_value=httpx.Response(200, json={"items": [], "count": 0})
    )
    client = CXClient(_cx_profile())
    payload = client.get(
        "/crmRestApi/resources/11.13.18.05/territories",
        params={"limit": 10, "onlyData": "true"},
    )
    assert payload["count"] == 0
    assert respx.calls.last.request.headers["Authorization"].startswith("Basic ")


def test_cx_client_requires_enabled() -> None:
    profile = _cx_profile(cx_enabled=False, cx_url=None)
    client = CXClient(profile)
    try:
        client.get("/crmRestApi/resources/11.13.18.05/territories")
    except CXAPIError as exc:
        assert exc.code == "VALIDATION_ERROR"
        return
    raise AssertionError("expected CXAPIError")


@respx.mock
def test_cx_client_post_with_extra_headers() -> None:
    route = respx.post(
        "https://cx.example.com/crmRestApi/searchResources/11.13.18.05/custom-actions/queries"
    ).mock(return_value=httpx.Response(200, json={"items": [], "count": 0}))
    client = CXClient(_cx_profile())
    payload = client.post(
        "/crmRestApi/searchResources/11.13.18.05/custom-actions/queries",
        json_body={"entity": "Account", "limit": 1},
        headers={"Preference": "transient"},
    )
    assert payload["count"] == 0
    assert route.calls.last.request.headers["Preference"] == "transient"


@respx.mock
def test_cx_client_bearer_get() -> None:
    token_url = "https://idcs.example.com/oauth2/v1/token"
    respx.post(token_url).mock(
        return_value=httpx.Response(
            200,
            json={"access_token": "cxtok", "token_type": "Bearer", "expires_in": 3600},
        )
    )
    respx.get("https://cx.example.com/crmRestApi/ping").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    profile = _cx_profile(
        cx_auth="bearer",
        cx_credentials=[],
        cx_oauth_token_url=token_url,
        cx_oauth_client_id="cid",
        cx_oauth_client_secret="csecret",
        cx_oauth_scope="urn:opc:resource:fusion:x:cpq/",
    )
    payload = CXClient(profile).get("/crmRestApi/ping")
    assert payload == {"ok": True}
    assert respx.calls.last.request.headers["Authorization"] == "Bearer cxtok"
