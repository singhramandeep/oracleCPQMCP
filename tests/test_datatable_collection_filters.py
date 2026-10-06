"""Contract: datatable list tools pass CPQ q when q_expr is set."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.datatables import register_datatable_tools


@pytest.fixture()
def profile() -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v18",
        company_login_name="_host",
        read_only=True,
        custom_data_table_name="MyTable",
    )


@pytest.fixture()
def configured(profile: CPQProfile) -> CPQProfile:
    configure_security(
        profile,
        SecuritySettings(
            confirmation_secret="test-secret-key-for-hmac",
            confirmation_ttl_seconds=300,
            schema_integrity_enabled=False,
            max_tool_calls_per_session=50,
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
    return profile


class FakeMcp:
    def __init__(self) -> None:
        self.tools: dict = {}

    def tool(self, **_kwargs):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def test_get_datatable_rows_sends_q_expr(configured: CPQProfile) -> None:
    client = MagicMock()
    client.profile = configured
    client.get.return_value = {"items": [], "hasMore": False}
    mcp = FakeMcp()
    register_datatable_tools(mcp, client)
    mcp.tools["get_datatable_rows"](
        table_name="MyTable",
        limit=1,
        q_expr="{col:{$eq:'x'}}",
        only_data=True,
    )
    _path, kwargs = client.get.call_args
    params = kwargs["params"]
    assert params["q"] == "{col:{$eq:'x'}}"
    assert params["onlyData"] == "true"
    assert params["totalResults"] == "true"
