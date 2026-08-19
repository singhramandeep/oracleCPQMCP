"""Tests for MCP tool registry and discovery filtering."""

from __future__ import annotations

from oracle_cpq_mcp.registry.tool_registry import (
    TOOL_CATALOG,
    CPQ_API_TOOLS,
    discover_tools_result,
    filter_tools,
    mcp_tool_kwargs,
    search_tools,
)


def test_catalog_contains_all_cpq_and_discovery_tools() -> None:
    assert len(CPQ_API_TOOLS) == 13
    assert "discover_tools" in TOOL_CATALOG
    assert len(TOOL_CATALOG) == 14


def test_filter_users_read_tools() -> None:
    names = {spec.name for spec in filter_tools(domain="users", operation="read")}
    assert names == {
        "export_users_excel",
        "get_user",
        "get_user_groups",
        "list_users",
    }


def test_filter_write_tools() -> None:
    names = {spec.name for spec in filter_tools(operation="write")}
    assert names == {"create_group", "deploy_datatables", "update_user"}


def test_search_excel_returns_export_tool() -> None:
    results = search_tools("excel")
    assert results
    assert results[0].name == "export_users_excel"


def test_search_deploy_returns_deploy_tool() -> None:
    results = search_tools("deploy")
    assert results
    assert results[0].name == "deploy_datatables"


def test_search_group_members() -> None:
    names = {spec.name for spec in search_tools("group members")}
    assert "list_group_users" in names
    assert "get_user_groups" in names


def test_mcp_tool_kwargs_read_only_hint() -> None:
    spec = TOOL_CATALOG["list_users"]
    kwargs = mcp_tool_kwargs(spec)
    assert kwargs["annotations"].readOnlyHint is True
    assert kwargs["annotations"].destructiveHint is False
    assert kwargs["meta"]["domain"] == "users"
    assert "users" in kwargs["tags"]
    assert "read" in kwargs["tags"]


def test_mcp_tool_kwargs_destructive_write_tool() -> None:
    spec = TOOL_CATALOG["deploy_datatables"]
    kwargs = mcp_tool_kwargs(spec)
    assert kwargs["annotations"].readOnlyHint is False
    assert kwargs["annotations"].destructiveHint is True


def test_write_tool_descriptions_mention_dry_run() -> None:
    for name in ("update_user", "create_group", "deploy_datatables"):
        assert "dry_run" in TOOL_CATALOG[name].description.lower()
        assert "confirmation_token" in TOOL_CATALOG[name].description.lower()


def test_write_tool_tags_include_dry_run_and_confirmation() -> None:
    for name in ("update_user", "create_group", "deploy_datatables"):
        assert "dry_run" in TOOL_CATALOG[name].tags
        assert "confirmation" in TOOL_CATALOG[name].tags


def test_discover_tools_result_shape() -> None:
    payload = discover_tools_result(domain="groups", operation="read", limit=10)
    assert payload["count"] == 3
    assert len(payload["tools"]) == 3
    first = payload["tools"][0]
    assert "name" in first
    assert "readOnlyHint" in first
    assert "destructiveHint" in first
    assert first["readOnlyHint"] is True
