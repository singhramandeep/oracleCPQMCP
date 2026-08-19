"""Tests for authorization and policy enforcement."""

from __future__ import annotations

import pytest

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.security.authorization import authorize_tool
from oracle_cpq_mcp.security.context import SecurityContext
from oracle_cpq_mcp.security.exceptions import AuthorizationDeniedError, PolicyViolationError
from oracle_cpq_mcp.security.settings import SecuritySettings


def _ctx(env: str = "dev", read_only: bool = False) -> SecurityContext:
    return SecurityContext(
        request_id="req-1",
        trace_id="trace-1",
        customer_id="test",
        environment=env,
        read_only=read_only,
    )


def test_authorize_read_tool_allowed() -> None:
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
    policy = authorize_tool("get_user", context=_ctx(), settings=settings, kwargs={"party_number": "abc"})
    assert policy.risk == "READ_ONLY"


def test_authorize_prod_denied_without_flag() -> None:
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
    with pytest.raises(PolicyViolationError, match="Production"):
        authorize_tool("get_user", context=_ctx(env="prod"), settings=settings, kwargs={"party_number": "abc"})


def test_authorize_read_only_blocks_write_execution() -> None:
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
    with pytest.raises(AuthorizationDeniedError):
        authorize_tool(
            "update_user",
            context=_ctx(read_only=True),
            settings=settings,
            kwargs={"party_number": "abc", "patch_body": {"email": "x@y.com"}, "dry_run": False},
        )


def test_authorize_read_only_allows_dry_run_preflight() -> None:
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
    policy = authorize_tool(
        "update_user",
        context=_ctx(read_only=True),
        settings=settings,
        kwargs={"party_number": "abc", "patch_body": {"email": "x@y.com"}, "dry_run": True},
    )
    assert policy.confirmation_required is True


def test_blocked_security_argument_names() -> None:
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
    with pytest.raises(PolicyViolationError, match="environment"):
        authorize_tool(
            "get_user",
            context=_ctx(),
            settings=settings,
            kwargs={"party_number": "abc", "environment": "prod"},
        )
