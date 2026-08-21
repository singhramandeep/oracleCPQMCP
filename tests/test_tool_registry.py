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
    assert len(CPQ_API_TOOLS) == 72
    assert "discover_tools" in TOOL_CATALOG
    assert "list_saved_prompts" in TOOL_CATALOG
    assert "start_prompt_picker" in TOOL_CATALOG
    assert "list_local_data" in TOOL_CATALOG
    assert "sync_users_local" in TOOL_CATALOG
    assert "get_all_bml_code" in TOOL_CATALOG
    assert "get_commerce_attributes" in TOOL_CATALOG
    assert "list_performance_logs" in TOOL_CATALOG
    assert "get_performance_log" in TOOL_CATALOG
    assert "list_transactions" in TOOL_CATALOG
    assert "generate_proposal" in TOOL_CATALOG
    assert "export_attachment" in TOOL_CATALOG
    assert "list_parts" in TOOL_CATALOG
    assert "get_task" in TOOL_CATALOG
    assert "list_product_families" in TOOL_CATALOG
    assert len(TOOL_CATALOG) == 87


def test_filter_users_read_tools() -> None:
    names = {spec.name for spec in filter_tools(domain="users", operation="read")}
    assert names == {
        "export_users_excel",
        "get_user",
        "get_user_groups",
        "list_users",
        "sync_users_local",
    }


def test_filter_write_tools() -> None:
    names = {spec.name for spec in filter_tools(operation="write")}
    assert names == {
        "copy_transaction",
        "copy_transaction_lines",
        "create_datatable",
        "create_group",
        "deploy_datatables",
        "export_attachment",
        "export_bml_library_functions",
        "export_datatables",
        "export_performance_logs",
        "generate_proposal",
        "update_user",
    }


def test_search_excel_returns_export_tool() -> None:
    results = search_tools("excel")
    assert results
    assert results[0].name == "export_users_excel"


def test_search_deploy_returns_deploy_tool() -> None:
    results = search_tools("deploy")
    assert results
    assert results[0].name == "deploy_datatables"


def test_search_bml_returns_bml_tool() -> None:
    results = search_tools("bml")
    names = {spec.name for spec in results}
    assert "get_all_bml_code" in names
    assert "get_bml_function" in names


def test_filter_commerce_read_tools() -> None:
    names = {spec.name for spec in filter_tools(domain="commerce", operation="read")}
    assert names == {
        "download_attachment",
        "get_commerce_action",
        "get_commerce_actions",
        "get_commerce_attribute",
        "get_commerce_attributes",
        "get_document_layout",
        "get_line_actions",
        "get_line_attributes",
        "get_transaction",
        "get_transaction_line",
        "list_commerce_processes",
        "list_transaction_lines",
        "list_transactions",
        "sync_commerce_metadata_local",
    }


def test_search_group_members() -> None:
    names = {spec.name for spec in search_tools("group members")}
    assert "list_group_users" in names
    assert "get_user_groups" in names


def test_mcp_tool_kwargs_read_only_hint() -> None:
    spec = TOOL_CATALOG["list_users"]
    kwargs = mcp_tool_kwargs(spec)
    assert kwargs["annotations"].readOnlyHint is True
    assert kwargs["annotations"].destructiveHint is False
    assert kwargs["annotations"].idempotentHint is True
    assert kwargs["annotations"].openWorldHint is True
    assert kwargs["title"] == "List Users"
    assert kwargs["annotations"].title == "List Users"
    assert kwargs["version"] == "1.0.0"
    assert kwargs["description"] == spec.description
    assert kwargs["icons"]
    assert kwargs["meta"]["domain"] == "users"
    assert kwargs["meta"]["version"] == "1.0.0"
    assert "users" in kwargs["tags"]
    assert "read" in kwargs["tags"]


def test_catalog_tools_have_title_version_icons() -> None:
    for name, spec in TOOL_CATALOG.items():
        assert spec.title.strip(), name
        assert spec.version == "1.0.0" or spec.version.count(".") == 2, name
        assert len(spec.icons) >= 1, name
        assert spec.icons[0].src.startswith("data:image/svg+xml"), name


def test_mcp_tool_kwargs_meta_tool_open_world_false() -> None:
    spec = TOOL_CATALOG["discover_tools"]
    kwargs = mcp_tool_kwargs(spec)
    assert kwargs["annotations"].openWorldHint is False
    assert kwargs["annotations"].idempotentHint is True


def test_mcp_tool_kwargs_destructive_write_tool() -> None:
    spec = TOOL_CATALOG["deploy_datatables"]
    kwargs = mcp_tool_kwargs(spec)
    assert kwargs["annotations"].readOnlyHint is False
    assert kwargs["annotations"].destructiveHint is True


def test_write_tool_descriptions_mention_dry_run() -> None:
    for name in (
        "update_user",
        "create_group",
        "deploy_datatables",
        "create_datatable",
        "export_datatables",
        "export_bml_library_functions",
        "generate_proposal",
        "export_attachment",
        "export_performance_logs",
        "copy_transaction",
        "copy_transaction_lines",
    ):
        assert "dry_run" in TOOL_CATALOG[name].description.lower()
        assert "confirmation_token" in TOOL_CATALOG[name].description.lower()


def test_write_tool_tags_include_dry_run_and_confirmation() -> None:
    for name in (
        "update_user",
        "create_group",
        "deploy_datatables",
        "create_datatable",
        "export_datatables",
        "export_bml_library_functions",
        "generate_proposal",
        "export_attachment",
        "export_performance_logs",
        "copy_transaction",
        "copy_transaction_lines",
    ):
        assert "dry_run" in TOOL_CATALOG[name].tags
        assert "confirmation" in TOOL_CATALOG[name].tags


def test_discover_tools_result_shape() -> None:
    payload = discover_tools_result(domain="groups", operation="read", limit=10)
    assert payload["count"] == 4
    assert len(payload["tools"]) == 4
    first = payload["tools"][0]
    assert "name" in first
    assert "readOnlyHint" in first
    assert "destructiveHint" in first
    assert first["readOnlyHint"] is True
