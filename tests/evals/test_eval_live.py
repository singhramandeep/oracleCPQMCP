"""Optional live sandbox eval (skipped unless CPQ_LIVE_EVAL=1)."""

from __future__ import annotations

import os

import pytest

from oracle_cpq_mcp.core.config import load_profile
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.security.settings import SecuritySettings, load_security_settings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.discovery import register_discovery_tools
from oracle_cpq_mcp.tools.users import register_user_tools

pytestmark = pytest.mark.live_eval


def _live_enabled() -> bool:
    return os.environ.get("CPQ_LIVE_EVAL", "").lower() in ("1", "true", "yes")


@pytest.fixture()
def live_client() -> CPQClient:
    if not _live_enabled():
        pytest.skip("Set CPQ_LIVE_EVAL=1 and configure CPQ_CUSTOMER_PROFILE to run live evals")
    profile = load_profile()
    settings = load_security_settings()
    # Never mutate in live evals
    if not profile.read_only:
        settings = SecuritySettings(
            confirmation_secret=settings.confirmation_secret,
            confirmation_ttl_seconds=settings.confirmation_ttl_seconds,
            schema_integrity_enabled=False,
            max_tool_calls_per_session=50,
            rate_limit_enabled=False,
            audit_enabled=False,
            allow_prod=settings.allow_prod,
            max_response_bytes=settings.max_response_bytes,
            replay_window_seconds=settings.replay_window_seconds,
            read_calls_per_minute=settings.read_calls_per_minute,
            write_calls_per_minute=settings.write_calls_per_minute,
            privileged_calls_per_minute=settings.privileged_calls_per_minute,
        )
    configure_security(profile, settings)
    return CPQClient(profile)


class _CaptureMcp:
    def __init__(self) -> None:
        self.tools: dict = {}

    def tool(self, **_kwargs):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def test_live_list_users_stamped(live_client: CPQClient) -> None:
    mcp = _CaptureMcp()
    register_user_tools(mcp, live_client)
    register_discovery_tools(mcp)
    result = mcp.tools["list_users"](limit=5, offset=0)
    assert isinstance(result, dict)
    assert result.get("status") == "ok"
    assert result.get("environment") == live_client.profile.environment
    assert result.get("customer_id") == live_client.profile.customer_id
    assert "retrieved_at" in result
    assert "data" in result


def test_live_discover_tools(live_client: CPQClient) -> None:
    mcp = _CaptureMcp()
    register_discovery_tools(mcp)
    result = mcp.tools["discover_tools"](domain="users", limit=10)
    assert result.get("status") == "ok"
    assert "retrieved_at" in result
