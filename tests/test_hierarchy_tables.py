"""Tests for product hierarchy and commerce process table builders."""

from __future__ import annotations

import httpx
import pytest
import respx

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.hierarchy_tables import (
    PRODUCT_HIERARCHY_COLUMNS,
    build_commerce_processes_table,
    build_product_hierarchy_table,
)
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.commerce import register_commerce_tools
from oracle_cpq_mcp.tools.configuration import register_configuration_tools


@pytest.fixture()
def profile() -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v18",
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
def test_build_product_hierarchy_table_flattens_bm_fields(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v18/productFamilies").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "variableName": "deposits",
                        "label": "Deposits",
                        "description": "",
                    }
                ],
                "hasMore": False,
            },
        )
    )
    respx.get(
        "https://dev.example.com/rest/v18/productFamilies/deposits/productLines"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "_bm_pline_variable_name": "deposits",
                        "_bm_pline_name": "Deposits",
                        "_bm_pline_description": "line desc",
                    }
                ],
                "hasMore": False,
            },
        )
    )
    respx.get(
        "https://dev.example.com/rest/v18/productFamilies/deposits/"
        "productLines/deposits/models"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "_bm_model_variable_name": "deposits",
                        "_bm_model_name": "Deposits",
                        "_bm_model_description": "model desc",
                    }
                ],
                "hasMore": False,
            },
        )
    )

    table = build_product_hierarchy_table(client, page_size=50)
    assert table["columns"] == PRODUCT_HIERARCHY_COLUMNS
    assert table["truncated"] is False
    assert table["counts"] == {
        "families": 1,
        "lines": 1,
        "models": 1,
        "rows": 1,
    }
    assert table["rows"] == [
        {
            "family_variable_name": "deposits",
            "family_name": "Deposits",
            "line_variable_name": "deposits",
            "line_name": "Deposits",
            "model_variable_name": "deposits",
            "model_name": "Deposits",
            "family_description": "",
            "line_description": "line desc",
            "model_description": "model desc",
        }
    ]


@respx.mock
def test_build_product_hierarchy_table_empty_models_still_emits_row(
    client: CPQClient,
) -> None:
    respx.get("https://dev.example.com/rest/v18/productFamilies").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"variableName": "fam", "label": "Fam"}],
                "hasMore": False,
            },
        )
    )
    respx.get("https://dev.example.com/rest/v18/productFamilies/fam/productLines").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "_bm_pline_variable_name": "line1",
                        "_bm_pline_name": "Line 1",
                    }
                ],
                "hasMore": False,
            },
        )
    )
    respx.get(
        "https://dev.example.com/rest/v18/productFamilies/fam/productLines/line1/models"
    ).mock(
        return_value=httpx.Response(200, json={"items": [], "hasMore": False})
    )

    table = build_product_hierarchy_table(client)
    assert table["counts"]["rows"] == 1
    assert table["rows"][0]["model_variable_name"] == ""
    assert table["rows"][0]["line_variable_name"] == "line1"


@respx.mock
def test_build_product_hierarchy_table_respects_max_families(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v18/productFamilies").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {"variableName": "a", "label": "A"},
                    {"variableName": "b", "label": "B"},
                ],
                "hasMore": True,
            },
        )
    )
    respx.get("https://dev.example.com/rest/v18/productFamilies/a/productLines").mock(
        return_value=httpx.Response(200, json={"items": [], "hasMore": False})
    )
    respx.get("https://dev.example.com/rest/v18/productFamilies/b/productLines").mock(
        return_value=httpx.Response(200, json={"items": [], "hasMore": False})
    )

    table = build_product_hierarchy_table(client, page_size=2, max_families=2)
    assert table["truncated"] is True
    assert table["counts"]["families"] == 2
    assert "max_families" in table["message"]


@respx.mock
def test_build_commerce_processes_table(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v18/commerceProcessSetups").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "variableName": "oraclecpqo",
                        "name": "Oracle Quote to Order",
                        "label": "Q2O",
                        "description": "main",
                        "id": 1,
                    }
                ],
                "hasMore": False,
            },
        )
    )
    table = build_commerce_processes_table(client)
    assert table["counts"]["processes"] == 1
    assert table["rows"][0]["variable_name"] == "oraclecpqo"
    assert table["rows"][0]["name"] == "Oracle Quote to Order"
    assert table["rows"][0]["label"] == "Q2O"


@respx.mock
def test_list_product_hierarchy_table_tool_registered(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v18/productFamilies").mock(
        return_value=httpx.Response(200, json={"items": [], "hasMore": False})
    )
    mcp = _McpStub()
    register_configuration_tools(mcp, client)
    fn = mcp.tools["list_product_hierarchy_table"]
    result = fn()  # type: ignore[operator]
    assert result["status"] == "ok"
    assert result["data"]["columns"] == PRODUCT_HIERARCHY_COLUMNS


@respx.mock
def test_list_commerce_processes_table_tool_registered(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v18/commerceProcessSetups").mock(
        return_value=httpx.Response(200, json={"items": [], "hasMore": False})
    )
    mcp = _McpStub()
    register_commerce_tools(mcp, client)
    fn = mcp.tools["list_commerce_processes_table"]
    result = fn()  # type: ignore[operator]
    assert result["status"] == "ok"
    assert result["data"]["counts"]["processes"] == 0
