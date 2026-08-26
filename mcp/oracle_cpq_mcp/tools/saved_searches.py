"""MCP tools for Oracle CPQ saved searches (searchResources)."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.commerce_paths import resolve_search_resource_var_name
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.pagination import build_page_params, enrich_pagination_hint
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool

_SHOW_ALL_VALUES = frozenset({"ALL", "HIDDEN", "VISIBLE", "INACTIVE"})


def register_saved_search_tools(mcp: Any, client: CPQClient) -> None:
    """Register saved search tools on the FastMCP instance."""

    def list_saved_searches(
        resource_var_name: str | None = None,
        process_var_name: str | None = None,
        show_all: str = "VISIBLE",
        limit: int = 100,
        offset: int = 0,
        total_results: bool = True,
    ) -> dict[str, Any]:
        resource = resolve_search_resource_var_name(
            client.profile,
            resource_var_name,
            process_var_name,
        )
        if isinstance(resource, dict):
            return resource
        show = (show_all or "VISIBLE").strip().upper()
        if show not in _SHOW_ALL_VALUES:
            show = "VISIBLE"
        params = build_page_params(
            limit,
            offset,
            total_results=total_results,
            extra={"showAll": show},
        )
        response = client.get(f"/searchResources/{resource}", params=params)
        if isinstance(response, dict) and (
            "hasMore" in response or "items" in response
        ):
            return enrich_pagination_hint(response, "list_saved_searches")
        return response

    list_saved_searches.__doc__ = TOOL_CATALOG["list_saved_searches"].description
    register_tool(mcp, list_saved_searches, "list_saved_searches")

    def get_saved_search(
        search_id: int,
        resource_var_name: str | None = None,
        process_var_name: str | None = None,
    ) -> dict[str, Any]:
        resource = resolve_search_resource_var_name(
            client.profile,
            resource_var_name,
            process_var_name,
        )
        if isinstance(resource, dict):
            return resource
        return client.get(f"/searchResources/{resource}/{search_id}")

    get_saved_search.__doc__ = TOOL_CATALOG["get_saved_search"].description
    register_tool(mcp, get_saved_search, "get_saved_search")
