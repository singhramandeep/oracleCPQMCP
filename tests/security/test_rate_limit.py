"""Tests for rate limiting."""

from __future__ import annotations

import pytest

from oracle_cpq_mcp.security.exceptions import RateLimitedError
from oracle_cpq_mcp.security.policy import get_tool_policy
from oracle_cpq_mcp.security.rate_limit import check_rate_limit, reset_rate_limits
from oracle_cpq_mcp.security.settings import SecuritySettings


def test_rate_limit_blocks_excess_calls() -> None:
    reset_rate_limits()
    settings = SecuritySettings(
        confirmation_secret="x",
        confirmation_ttl_seconds=300,
        schema_integrity_enabled=False,
        max_tool_calls_per_session=100,
        rate_limit_enabled=True,
        audit_enabled=False,
        allow_prod=False,
        max_response_bytes=1000,
        replay_window_seconds=60,
        read_calls_per_minute=120,
        write_calls_per_minute=2,
        privileged_calls_per_minute=5,
    )
    policy = get_tool_policy("update_user")
    assert policy is not None
    limit = policy.max_calls_per_minute
    for _ in range(limit):
        check_rate_limit("update_user", customer_id="test", policy=policy, settings=settings)
    with pytest.raises(RateLimitedError):
        check_rate_limit("update_user", customer_id="test", policy=policy, settings=settings)
