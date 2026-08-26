"""Unit tests for list_metrics enrichment and q wiring."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.security.context import reset_session_tool_calls
from oracle_cpq_mcp.security.rate_limit import reset_rate_limits
from oracle_cpq_mcp.security.replay import reset_replay_store
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.metrics import register_metrics_tools


class _FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):  # noqa: ANN201
        def decorator(fn):  # noqa: ANN001, ANN202
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def test_list_metrics_attaches_descriptions_and_builds_q() -> None:
    profile = CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v19",
        metric_descriptions={"QUOTES": "Total number of quotes"},
    )
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

    client = MagicMock()
    client.profile = profile
    captured: dict[str, Any] = {}

    def _get(path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        captured["path"] = path
        captured["params"] = params or {}
        return {
            "items": [
                {
                    "name": "QUOTES",
                    "value": 42,
                    "dateAdded": "2026-08-20T00:00:00.000Z",
                }
            ],
            "hasMore": False,
            "offset": 0,
            "limit": 100,
            "count": 1,
        }

    client.get.side_effect = _get

    mcp = _FakeMcp()
    register_metrics_tools(mcp, client)  # type: ignore[arg-type]
    result = mcp.tools["list_metrics"](
        name="QUOTES",
        start_time="2026-08-11T00:00:00.000Z",
        date_added_from="2026-08-11T00:00:00.000Z",
    )
    assert captured["path"] == "/metrics"
    q = captured["params"].get("q")
    assert q is not None
    assert "'name':{'$eq':'QUOTES'}" in q
    assert "'startTime'" in q
    assert "'dateAdded'" in q

    assert result["status"] == "ok"
    items = result["data"]["items"]
    assert items[0]["description"] == "Total number of quotes"
    assert items[0]["value"] == 42
