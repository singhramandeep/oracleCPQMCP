"""Tests for HMAC confirmation tokens."""

from __future__ import annotations

import pytest

from oracle_cpq_mcp.security.confirmation import (
    issue_confirmation_token,
    validate_confirmation_token,
)
from oracle_cpq_mcp.security.context import SecurityContext
from oracle_cpq_mcp.security.exceptions import ConfirmationInvalidError
from oracle_cpq_mcp.security.settings import SecuritySettings


@pytest.fixture()
def ctx() -> SecurityContext:
    return SecurityContext(
        request_id="r1",
        trace_id="t1",
        customer_id="test",
        environment="dev",
        read_only=False,
    )


@pytest.fixture()
def settings() -> SecuritySettings:
    return SecuritySettings(
        confirmation_secret="super-secret-key",
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


def test_issue_and_validate_token(ctx: SecurityContext, settings: SecuritySettings) -> None:
    args = {
        "party_number": "abc",
        "patch_body": {"email": "x@y.com"},
        "dry_run": False,
    }
    issued = issue_confirmation_token("update_user", args, context=ctx, settings=settings)
    validate_confirmation_token(
        "update_user",
        args,
        issued["confirmation_token"],
        context=ctx,
        settings=settings,
    )


def test_rejects_altered_arguments(ctx: SecurityContext, settings: SecuritySettings) -> None:
    args = {
        "party_number": "abc",
        "patch_body": {"email": "x@y.com"},
        "dry_run": False,
    }
    issued = issue_confirmation_token("update_user", args, context=ctx, settings=settings)
    altered = dict(args)
    altered["patch_body"] = {"email": "evil@y.com"}
    with pytest.raises(ConfirmationInvalidError):
        validate_confirmation_token(
            "update_user",
            altered,
            issued["confirmation_token"],
            context=ctx,
            settings=settings,
        )


def test_rejects_missing_token(ctx: SecurityContext, settings: SecuritySettings) -> None:
    with pytest.raises(ConfirmationInvalidError):
        validate_confirmation_token(
            "update_user",
            {"party_number": "abc", "patch_body": {"a": 1}, "dry_run": False},
            None,
            context=ctx,
            settings=settings,
        )
