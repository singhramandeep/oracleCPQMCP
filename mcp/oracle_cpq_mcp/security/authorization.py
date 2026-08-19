"""Deny-by-default authorization checks for MCP tools."""

from __future__ import annotations

from oracle_cpq_mcp.security.context import SecurityContext
from oracle_cpq_mcp.security.exceptions import AuthorizationDeniedError, PolicyViolationError
from oracle_cpq_mcp.security.policy import ToolPolicy, get_tool_policy
from oracle_cpq_mcp.security.settings import SecuritySettings

BLOCKED_ARGUMENT_NAMES = frozenset(
    {
        "tenant",
        "tenant_id",
        "environment",
        "env",
        "user_id",
        "credentials",
        "password",
        "api_key",
        "access_token",
        "refresh_token",
        "credential_index",
        "cpq_environment",
        "cpq_customer_profile",
    }
)


def check_blocked_arguments(kwargs: dict) -> None:
    """Reject LLM-supplied security-sensitive argument names."""
    for key in kwargs:
        if key.lower() in BLOCKED_ARGUMENT_NAMES:
            raise PolicyViolationError(
                f"Argument '{key}' is not allowed — "
                "tenant, environment, and credentials are host-controlled."
            )


def authorize_tool(
    tool_name: str,
    *,
    context: SecurityContext,
    settings: SecuritySettings,
    kwargs: dict | None = None,
) -> ToolPolicy:
    """Authorize a tool invocation; deny-by-default."""
    policy = get_tool_policy(tool_name)
    if policy is None:
        raise AuthorizationDeniedError(f"Unknown tool '{tool_name}' is not permitted.")

    if kwargs:
        check_blocked_arguments(kwargs)

    if context.environment == "prod" and not settings.allow_prod:
        raise PolicyViolationError(
            "Production environment access denied. "
            "Set CPQ_ALLOW_PROD=1 in host environment to enable prod."
        )

    if context.read_only and policy.risk in (
        "LOW_RISK_WRITE",
        "HIGH_RISK_WRITE",
        "DESTRUCTIVE",
    ):
        dry_run = True
        if kwargs:
            dry_run = kwargs.get("dry_run", True)
        if not dry_run:
            raise AuthorizationDeniedError(
                f"Tool '{tool_name}' is blocked while profile READ_ONLY=true."
            )

    return policy
