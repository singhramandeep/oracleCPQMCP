"""MCP tools for Oracle CPQ Parts APIs."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.cpq_collection import cpq_expand_params, cpq_list_params
from oracle_cpq_mcp.core.pagination import enrich_pagination_hint
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool


def register_parts_tools(mcp: Any, client: CPQClient) -> None:
    """Register parts catalog tools on the FastMCP instance."""

    def list_parts(
        limit: int = 100,
        offset: int = 0,
        total_results: bool = True,
        only_data: bool = True,
        q_expr: str | None = None,
        fields: list[str] | None = None,
        orderby: list[str] | None = None,
        finder: str | None = None,
    ) -> dict[str, Any]:
        params = cpq_list_params(
            limit,
            offset,
            total_results=total_results,
            q_expr=q_expr,
            fields=fields,
            orderby=orderby,
            finder=finder,
            only_data=only_data,
        )
        response = client.get("/parts", params=params)
        return enrich_pagination_hint(response, "list_parts")

    list_parts.__doc__ = TOOL_CATALOG["list_parts"].description
    register_tool(mcp, list_parts, "list_parts")

    def get_part(
        part_id: str,
        expand: str | None = None,
        exclude_field_types: str | None = None,
        only_data: bool = True,
    ) -> dict[str, Any]:
        params = cpq_expand_params(
            expand=expand,
            exclude_field_types=exclude_field_types,
            only_data=only_data,
        )
        return client.get(f"/parts/{part_id}", params=params)

    get_part.__doc__ = TOOL_CATALOG["get_part"].description
    register_tool(mcp, get_part, "get_part")

    def search_parts(body: dict[str, Any]) -> dict[str, Any]:
        response = client.post("/parts/actions/search", json_body=body)
        if isinstance(response, dict) and ("hasMore" in response or "items" in response):
            return enrich_pagination_hint(response, "search_parts")
        return response

    search_parts.__doc__ = TOOL_CATALOG["search_parts"].description
    register_tool(mcp, search_parts, "search_parts")
