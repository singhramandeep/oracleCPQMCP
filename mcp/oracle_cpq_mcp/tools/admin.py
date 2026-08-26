"""MCP tools for Oracle CPQ site admin APIs (certificates, SSO)."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool


def register_admin_tools(mcp: Any, client: CPQClient) -> None:
    """Register certificates and SSO configuration tools."""

    def list_certificates() -> dict[str, Any]:
        return client.get("/certificates")

    list_certificates.__doc__ = TOOL_CATALOG["list_certificates"].description
    register_tool(mcp, list_certificates, "list_certificates")

    def get_certificate(name: str) -> dict[str, Any]:
        return client.get(f"/certificates/{name}")

    get_certificate.__doc__ = TOOL_CATALOG["get_certificate"].description
    register_tool(mcp, get_certificate, "get_certificate")

    def get_sso_configuration() -> dict[str, Any]:
        return client.get("/ssoConfiguration")

    get_sso_configuration.__doc__ = TOOL_CATALOG["get_sso_configuration"].description
    register_tool(mcp, get_sso_configuration, "get_sso_configuration")
