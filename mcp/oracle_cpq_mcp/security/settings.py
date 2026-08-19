"""Security configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from oracle_cpq_mcp.core.config import parse_bool_env


@dataclass(frozen=True)
class SecuritySettings:
    """Centralized security settings for the MCP server."""

    confirmation_secret: str | None
    confirmation_ttl_seconds: int
    schema_integrity_enabled: bool
    max_tool_calls_per_session: int
    rate_limit_enabled: bool
    audit_enabled: bool
    allow_prod: bool
    max_response_bytes: int
    replay_window_seconds: int
    read_calls_per_minute: int
    write_calls_per_minute: int
    privileged_calls_per_minute: int


def load_security_settings() -> SecuritySettings:
    """Load security settings from environment with fail-safe defaults."""
    return SecuritySettings(
        confirmation_secret=os.environ.get("CPQ_CONFIRMATION_SECRET") or None,
        confirmation_ttl_seconds=int(os.environ.get("CPQ_CONFIRMATION_TTL", "300")),
        schema_integrity_enabled=parse_bool_env(
            os.environ.get("CPQ_SCHEMA_INTEGRITY"), default=True
        ),
        max_tool_calls_per_session=int(os.environ.get("CPQ_MAX_TOOL_CALLS", "20")),
        rate_limit_enabled=parse_bool_env(
            os.environ.get("CPQ_RATE_LIMIT_ENABLED"), default=True
        ),
        audit_enabled=parse_bool_env(os.environ.get("CPQ_AUDIT_ENABLED"), default=True),
        allow_prod=parse_bool_env(os.environ.get("CPQ_ALLOW_PROD"), default=False),
        max_response_bytes=int(os.environ.get("CPQ_MAX_RESPONSE_BYTES", "2000000")),
        replay_window_seconds=int(os.environ.get("CPQ_REPLAY_WINDOW_SECONDS", "60")),
        read_calls_per_minute=int(os.environ.get("CPQ_READ_CALLS_PER_MINUTE", "120")),
        write_calls_per_minute=int(os.environ.get("CPQ_WRITE_CALLS_PER_MINUTE", "10")),
        privileged_calls_per_minute=int(
            os.environ.get("CPQ_PRIVILEGED_CALLS_PER_MINUTE", "5")
        ),
    )
