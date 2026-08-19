"""Security context for MCP tool invocations."""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass

from oracle_cpq_mcp.core.config import CPQProfile

_current_context: ContextVar["SecurityContext | None"] = ContextVar(
    "security_context", default=None
)
_session_tool_calls: ContextVar[int] = ContextVar("session_tool_calls", default=0)


@dataclass(frozen=True)
class SecurityContext:
    """Immutable security context derived from host env — never from LLM args."""

    request_id: str
    trace_id: str
    customer_id: str
    environment: str
    read_only: bool
    actor: str = "stdio_host"
    credential_index: int = 0


def build_security_context(profile: CPQProfile) -> SecurityContext:
    """Build a security context from the active CPQ profile."""
    return SecurityContext(
        request_id=str(uuid.uuid4()),
        trace_id=str(uuid.uuid4()),
        customer_id=profile.customer_id,
        environment=profile.environment,
        read_only=profile.read_only,
        actor="stdio_host",
        credential_index=profile.credential_index,
    )


def set_security_context(ctx: SecurityContext) -> None:
    _current_context.set(ctx)


def get_security_context() -> SecurityContext | None:
    return _current_context.get()


def increment_session_tool_calls() -> int:
    count = _session_tool_calls.get() + 1
    _session_tool_calls.set(count)
    return count


def reset_session_tool_calls() -> None:
    _session_tool_calls.set(0)
