"""Shared fixtures for security tests."""

from __future__ import annotations

import pytest

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.security.context import reset_session_tool_calls
from oracle_cpq_mcp.security.rate_limit import reset_rate_limits
from oracle_cpq_mcp.security.replay import reset_replay_store
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security


@pytest.fixture()
def security_settings() -> SecuritySettings:
    return SecuritySettings(
        confirmation_secret="test-secret-key-for-hmac",
        confirmation_ttl_seconds=300,
        schema_integrity_enabled=False,
        max_tool_calls_per_session=20,
        rate_limit_enabled=True,
        audit_enabled=False,
        allow_prod=False,
        max_response_bytes=2_000_000,
        replay_window_seconds=60,
        read_calls_per_minute=120,
        write_calls_per_minute=10,
        privileged_calls_per_minute=5,
    )


@pytest.fixture()
def test_profile() -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v18",
        company_login_name="_host",
        read_only=False,
    )


@pytest.fixture(autouse=True)
def _reset_security_state(security_settings: SecuritySettings, test_profile: CPQProfile) -> None:
    reset_session_tool_calls()
    reset_rate_limits()
    reset_replay_store()
    configure_security(test_profile, security_settings)
