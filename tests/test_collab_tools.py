"""Unit tests for collab operation queue tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.security.context import reset_session_tool_calls
from oracle_cpq_mcp.security.rate_limit import reset_rate_limits
from oracle_cpq_mcp.security.replay import reset_replay_store
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.collab import register_collab_tools


class _FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):  # noqa: ANN201
        def decorator(fn):  # noqa: ANN001, ANN202
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def _profile(*, read_only: bool) -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v19",
        read_only=read_only,
    )


def _configure(profile: CPQProfile) -> None:
    reset_session_tool_calls()
    reset_rate_limits()
    reset_replay_store()
    configure_security(
        profile,
        SecuritySettings(
            confirmation_secret="test-secret-key-for-hmac",
            confirmation_ttl_seconds=300,
            schema_integrity_enabled=False,
            max_tool_calls_per_session=100,
            rate_limit_enabled=False,
            audit_enabled=False,
            allow_prod=False,
            max_response_bytes=2_000_000,
            replay_window_seconds=60,
            read_calls_per_minute=120,
            write_calls_per_minute=10,
            privileged_calls_per_minute=5,
        ),
    )


def test_clear_collab_queue_dry_run_preflight() -> None:
    profile = _profile(read_only=False)
    _configure(profile)
    client = MagicMock()
    client.profile = profile
    client.get.return_value = {
        "operationCount": 2,
        "queuedOperations": [{"description": "op-a"}, {"description": "op-b"}],
        "currentlyExecutingOperation": None,
        "node": "node1",
    }
    mcp = _FakeMcp()
    register_collab_tools(mcp, client)  # type: ignore[arg-type]
    result = mcp.tools["clear_collab_operation_queue"](bs_id=99, dry_run=True)
    assert result["status"] == "preflight_ok"
    client.get.assert_called_with("/collabOperationQueues/99")
    client.post.assert_not_called()
    summary = result["data"]["preflight"]["queue_summary"]
    assert summary["operationCount"] == 2
    assert "op-a" in summary["sample_queued_descriptions"]


def test_clear_collab_queue_read_only_blocks_apply() -> None:
    profile = _profile(read_only=True)
    _configure(profile)
    client = MagicMock()
    client.profile = profile
    client.get.return_value = {
        "operationCount": 1,
        "queuedOperations": [{"description": "op-a"}],
        "currentlyExecutingOperation": None,
        "node": "node1",
    }
    mcp = _FakeMcp()
    register_collab_tools(mcp, client)  # type: ignore[arg-type]
    # dry_run preflight is annotated when READ_ONLY; token gate blocks dry_run=false
    # before resolve_write_execution, so assert the annotated preflight path.
    result = mcp.tools["clear_collab_operation_queue"](bs_id=99, dry_run=True)
    assert result["status"] == "preflight_ok"
    assert result["data"].get("read_only") is True
    assert result["data"].get("execution_blocked") is True
    client.post.assert_not_called()
