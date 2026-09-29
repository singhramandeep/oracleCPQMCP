"""Fusion-mode list_users: Bearer auth + /cpq/rest/{version}/users."""

from __future__ import annotations

from typing import Any

import httpx
import respx

from oracle_cpq_mcp.core.config import CPQProfile
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.security.context import reset_session_tool_calls
from oracle_cpq_mcp.security.rate_limit import reset_rate_limits
from oracle_cpq_mcp.security.replay import reset_replay_store
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.users import register_user_tools


class _FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):  # noqa: ANN201
        def decorator(fn):  # noqa: ANN001, ANN202
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def _fusion_profile() -> CPQProfile:
    return CPQProfile(
        customer_name="Fusion",
        customer_id="example_fusion",
        environment="dev",
        base_url="https://example-fusion-dev.fa.ocs.oraclecloud.com",
        credentials=[],
        rest_version="v19",
        mode="fusion",
        oauth_token_url="https://idcs.example.com/oauth2/v1/token",
        oauth_client_id="cid",
        oauth_client_secret="csecret",
        oauth_scope="urn:opc:resource:fusion:example-dev:cpq/",
        read_only=True,
        debug_mode=False,
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


@respx.mock
def test_list_users_fusion_uses_bearer_and_cpq_rest_path() -> None:
    token_url = "https://idcs.example.com/oauth2/v1/token"
    profile = _fusion_profile()
    _configure(profile)
    client = CPQClient(profile)

    respx.post(token_url).mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "fusion-user-token-xyz",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
        )
    )
    users_route = respx.get(
        "https://example-fusion-dev.fa.ocs.oraclecloud.com/cpq/rest/v19/users"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"items": [{"login": "alice", "partyNumber": "1"}], "hasMore": False},
        )
    )

    mcp = _FakeMcp()
    register_user_tools(mcp, client)
    result = mcp.tools["list_users"](limit=5, offset=0)

    assert result["status"] == "ok"
    assert result["profile"] == "example_fusion"
    assert result["environment"] == "dev"
    assert users_route.called
    request_url = str(users_route.calls.last.request.url)
    auth = users_route.calls.last.request.headers["Authorization"]
    assert auth == "Bearer fusion-user-token-xyz"
    assert request_url.startswith(
        "https://example-fusion-dev.fa.ocs.oraclecloud.com/cpq/rest/v19/users"
    )
