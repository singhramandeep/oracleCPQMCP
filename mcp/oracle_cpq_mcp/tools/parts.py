"""MCP tools for Oracle CPQ Parts APIs."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.pagination import build_page_params, enrich_pagination_hint
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool


def register_parts_tools(mcp: Any, client: CPQClient) -> None:
    """Register parts catalog tools on the FastMCP instance."""

    def list_parts(
        limit: int = 100,
        offset: int = 0,
        q_expr: str | None = None,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        extra: dict[str, Any] = {}
        if q_expr:
            extra["q"] = q_expr
        if fields:
            extra["fields"] = ",".join(fields)
        params = build_page_params(limit, offset, extra=extra or None)
        response = client.get("/parts", params=params)
        return enrich_pagination_hint(response, "list_parts")

    list_parts.__doc__ = TOOL_CATALOG["list_parts"].description
    register_tool(mcp, list_parts, "list_parts")

    def get_part(part_id: str) -> dict[str, Any]:
        return client.get(f"/parts/{part_id}")

    get_part.__doc__ = TOOL_CATALOG["get_part"].description
    register_tool(mcp, get_part, "get_part")

    def search_parts(body: dict[str, Any]) -> dict[str, Any]:
        response = client.post("/parts/actions/search", json_body=body)
        if isinstance(response, dict) and ("hasMore" in response or "items" in response):
            return enrich_pagination_hint(response, "search_parts")
        return response

    search_parts.__doc__ = TOOL_CATALOG["search_parts"].description
    register_tool(mcp, search_parts, "search_parts")
