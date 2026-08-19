"""In-memory sliding-window rate limiting for MCP tools."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from oracle_cpq_mcp.security.exceptions import RateLimitedError
from oracle_cpq_mcp.security.policy import ToolPolicy
from oracle_cpq_mcp.security.settings import SecuritySettings

_lock = Lock()
_windows: dict[str, deque[float]] = defaultdict(deque)


def _window_key(tool_name: str, customer_id: str) -> str:
    return f"{customer_id}:{tool_name}"


def check_rate_limit(
    tool_name: str,
    *,
    customer_id: str,
    policy: ToolPolicy,
    settings: SecuritySettings,
) -> None:
    """Raise RateLimitedError when per-tool limit exceeded."""
    if not settings.rate_limit_enabled:
        return

    limit = policy.max_calls_per_minute
    key = _window_key(tool_name, customer_id)
    now = time.monotonic()
    window_start = now - 60.0

    with _lock:
        bucket = _windows[key]
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= limit:
            raise RateLimitedError(
                f"Rate limit exceeded for '{tool_name}' ({limit} calls/minute)."
            )
        bucket.append(now)


def reset_rate_limits() -> None:
    """Clear rate limit state (for tests)."""
    with _lock:
        _windows.clear()
