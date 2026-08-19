"""MCP tools for Oracle CPQ BML APIs."""

from __future__ import annotations

from typing import Any, Literal

from fastmcp.utilities.types import File

from oracle_cpq_mcp.core.bml_fetchers import (
    bml_export_filename,
    fetch_all_util_library_code,
)
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool

BmlDelivery = Literal["zip", "json"]


def register_bml_tools(mcp: Any, client: CPQClient) -> None:
    """Register BML read tools on the FastMCP instance."""

    def get_all_bml_code(delivery: BmlDelivery = "zip") -> list[str | File] | dict[str, Any]:
        if delivery == "zip":
            zip_bytes = client.get_bytes("/adminMeta")
            filename = bml_export_filename(client.profile)
            summary = (
                f"Downloaded all Commerce BML and BMLT files from "
                f"{client.profile.customer_name} ({client.profile.environment}) "
                f"to {filename}. Equivalent to cpq-toolkit pull."
            )
            return [
                summary,
                File(
                    data=zip_bytes,
                    format="zip",
                    name=filename,
                ),
            ]

        functions = fetch_all_util_library_code(client)
        truncated = len(functions) >= 1000
        return {
            "delivery": "json",
            "customer": client.profile.customer_name,
            "environment": client.profile.environment,
            "utilLibraryFunctionCount": len(functions),
            "utilLibraryFunctions": functions,
            "truncated": truncated,
            "note": (
                "JSON delivery returns util library scriptText only. "
                "Use delivery='zip' for the full Commerce BML/BMLT site export."
            ),
        }

    get_all_bml_code.__doc__ = TOOL_CATALOG["get_all_bml_code"].description
    register_tool(mcp, get_all_bml_code, "get_all_bml_code")
