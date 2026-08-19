"""Structured security audit logging."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from oracle_cpq_mcp.security.confirmation import hash_arguments
from oracle_cpq_mcp.security.context import SecurityContext
from oracle_cpq_mcp.security.policy import ToolPolicy
from oracle_cpq_mcp.security.settings import SecuritySettings

logger = logging.getLogger("oracle_cpq_mcp.audit")


def emit_audit_event(
    *,
    context: SecurityContext,
    tool_name: str,
    policy: ToolPolicy,
    settings: SecuritySettings,
    kwargs: dict[str, Any],
    authorization_result: str,
    policy_result: str,
    confirmation_required: bool,
    confirmation_result: str | None,
    execution_result: str,
    error_code: str | None,
    duration_ms: float,
) -> None:
    """Emit a structured JSON audit event (no secrets)."""
    if not settings.audit_enabled:
        return

    event = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "request_id": context.request_id,
        "trace_id": context.trace_id,
        "tool_name": tool_name,
        "risk_level": policy.risk,
        "customer_id": context.customer_id,
        "environment": context.environment,
        "args_hash": hash_arguments(tool_name, kwargs),
        "authorization_result": authorization_result,
        "policy_result": policy_result,
        "confirmation_required": confirmation_required,
        "confirmation_result": confirmation_result,
        "execution_result": execution_result,
        "duration_ms": round(duration_ms, 2),
        "error_code": error_code,
        "actor": context.actor,
    }
    logger.info("AUDIT %s", json.dumps(event, sort_keys=True))
