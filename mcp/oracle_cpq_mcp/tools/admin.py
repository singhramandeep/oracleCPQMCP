"""MCP tools for Oracle CPQ site admin APIs (certificates, SSO, Fusion OAuth)."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.errors import CPQAPIError
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.security.fusion_oauth import (
    FusionOAuthError,
    get_fusion_access_token as fetch_fusion_token,
    mask_access_token,
)
from oracle_cpq_mcp.tools._register import register_tool


def register_admin_tools(mcp: Any, client: CPQClient) -> None:
    """Register certificates, SSO, and Fusion OAuth tools."""

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

    def get_fusion_access_token(include_token: bool = False) -> dict[str, Any]:
        profile = client.profile
        if profile.mode != "fusion":
            raise CPQAPIError(
                f"Active profile mode is {profile.mode!r}; "
                "get_fusion_access_token requires mode=fusion.",
                code="VALIDATION_ERROR",
                hint="Use a profile YAML with mode: fusion and oauth_* env fields.",
                password=profile.sanitize_secret,
            )
        if not (
            profile.oauth_token_url
            and profile.oauth_client_id
            and profile.oauth_client_secret
            and profile.oauth_scope
        ):
            raise CPQAPIError(
                "Fusion profile is missing oauth_token_url / oauth_client_id / "
                "oauth_client_secret / oauth_scope for the active environment.",
                code="VALIDATION_ERROR",
                hint="Set OAuth fields under environments.<env> in the profile YAML.",
                password=profile.sanitize_secret,
            )
        try:
            token = fetch_fusion_token(
                profile.oauth_token_url,
                profile.oauth_client_id,
                profile.oauth_client_secret,
                profile.oauth_scope,
                timeout_seconds=min(profile.http_timeout, 60.0),
            )
        except FusionOAuthError as exc:
            raise CPQAPIError(
                f"Failed to obtain Fusion access token: {exc}",
                code="UNAUTHORIZED",
                hint="Verify oauth_token_url, client id/secret, and scope.",
                password=profile.sanitize_secret,
            ) from exc
        # Full token uses oauth_access_token (not access_token) so sanitize_tool_output
        # does not strip an explicitly requested reveal; access_token remains redacted.
        payload: dict[str, Any] = {
            "token_type": token.token_type,
            "expires_in": token.expires_in,
            "scope": token.scope,
            "access_token_masked": mask_access_token(token.access_token),
            "mode": profile.mode,
            "environment": profile.environment,
        }
        if include_token:
            payload["oauth_access_token"] = token.access_token
        return payload

    get_fusion_access_token.__doc__ = TOOL_CATALOG["get_fusion_access_token"].description
    register_tool(mcp, get_fusion_access_token, "get_fusion_access_token")
