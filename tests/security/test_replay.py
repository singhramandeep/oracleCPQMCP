"""Tests for replay protection."""

from __future__ import annotations

import pytest

from oracle_cpq_mcp.security.context import SecurityContext
from oracle_cpq_mcp.security.exceptions import PolicyViolationError
from oracle_cpq_mcp.security.replay import check_replay, reset_replay_store
from oracle_cpq_mcp.security.settings import SecuritySettings


def test_duplicate_write_blocked() -> None:
    reset_replay_store()
    ctx = SecurityContext(
        request_id="r1",
        trace_id="t1",
        customer_id="test",
        environment="dev",
        read_only=False,
    )
    settings = SecuritySettings(
        confirmation_secret="x",
        confirmation_ttl_seconds=300,
        schema_integrity_enabled=False,
        max_tool_calls_per_session=20,
        rate_limit_enabled=True,
        audit_enabled=False,
        allow_prod=False,
        max_response_bytes=1000,
        replay_window_seconds=60,
        read_calls_per_minute=120,
        write_calls_per_minute=10,
        privileged_calls_per_minute=5,
    )
    args = {"party_number": "abc", "patch_body": {"email": "a@b.com"}, "dry_run": False}
    check_replay("update_user", args, context=ctx, settings=settings)
    with pytest.raises(PolicyViolationError, match="Duplicate"):
        check_replay("update_user", args, context=ctx, settings=settings)
