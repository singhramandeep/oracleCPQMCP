"""Fusion CX MCP tools, registered per YAML ``cx.modules`` product."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from oracle_cpq_mcp.core.cx_client import CXClient
from oracle_cpq_mcp.tools.cx.adaptive_search import register_adaptive_search_tools
from oracle_cpq_mcp.tools.cx.prm import register_prm_tools
from oracle_cpq_mcp.tools.cx.sales import register_sales_tools

_CX_MODULE_REGISTRARS: dict[str, Callable[[Any, CXClient], None]] = {
    "Sales": register_sales_tools,
    "PRM": register_prm_tools,
}


def register_cx_tools(mcp: Any, client: CXClient) -> None:
    """Register CX module packages enabled on the active profile."""
    profile = client.profile
    if not profile.cx_enabled:
        return
    enabled = set(profile.cx_modules or [])
    if enabled:
        register_adaptive_search_tools(mcp, client)
    for yaml_name, register in _CX_MODULE_REGISTRARS.items():
        if yaml_name in enabled:
            register(mcp, client)
