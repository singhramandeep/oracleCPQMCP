"""Replay protection for state-changing tool invocations."""

from __future__ import annotations

import time
from threading import Lock

from oracle_cpq_mcp.security.confirmation import hash_arguments
from oracle_cpq_mcp.security.context import SecurityContext
from oracle_cpq_mcp.security.exceptions import PolicyViolationError
from oracle_cpq_mcp.security.settings import SecuritySettings

_lock = Lock()
_recent_writes: dict[str, float] = {}


def _replay_key(tool: str, arguments: dict, context: SecurityContext) -> str:
    args_hash = hash_arguments(tool, arguments)
    return f"{context.customer_id}:{context.environment}:{tool}:{args_hash}"


def check_replay(
    tool: str,
    arguments: dict,
    *,
    context: SecurityContext,
    settings: SecuritySettings,
) -> None:
    """Reject duplicate state-changing calls within the replay window."""
    key = _replay_key(tool, arguments, context)
    now = time.monotonic()
    window = settings.replay_window_seconds

    with _lock:
        expired = [k for k, ts in _recent_writes.items() if now - ts > window]
        for k in expired:
            del _recent_writes[k]

        if key in _recent_writes:
            raise PolicyViolationError(
                "Duplicate state-changing request detected within replay window."
            )
        _recent_writes[key] = now


def record_successful_write(
    tool: str,
    arguments: dict,
    *,
    context: SecurityContext,
) -> None:
    """Record a successful write (already stored by check_replay before execute)."""
    _ = (tool, arguments, context)


def reset_replay_store() -> None:
    """Clear replay state (for tests)."""
    with _lock:
        _recent_writes.clear()
