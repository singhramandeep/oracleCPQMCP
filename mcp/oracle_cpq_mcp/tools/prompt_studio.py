"""MCP tools for local Prompt Studio lifecycle."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.prompt_studio_process import ensure_prompt_studio as _ensure
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool


def register_prompt_studio_tools(mcp: Any) -> None:
    """Register Prompt Studio ensure/start tools on the FastMCP instance."""

    def ensure_prompt_studio() -> dict[str, Any]:
        return _ensure()

    ensure_prompt_studio.__doc__ = TOOL_CATALOG["ensure_prompt_studio"].description
    register_tool(mcp, ensure_prompt_studio, "ensure_prompt_studio")
