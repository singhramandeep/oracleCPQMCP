"""MCP tool for discovering and filtering the CPQ tool catalog."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG, DomainFilter, OperationFilter, discover_tools_result
from oracle_cpq_mcp.tools._register import register_tool

_DISCOVER_DOC = TOOL_CATALOG["discover_tools"].description


def register_discovery_tools(mcp: Any) -> None:
    """Register the discover_tools meta tool."""

    def discover_tools(
        query: str | None = None,
        domain: DomainFilter = "all",
        operation: OperationFilter = "all",
        limit: int = 20,
    ) -> dict[str, Any]:
        return discover_tools_result(
            query=query,
            domain=domain,
            operation=operation,
            limit=max(1, min(limit, 50)),
        )

    discover_tools.__doc__ = _DISCOVER_DOC
    register_tool(mcp, discover_tools, "discover_tools")
