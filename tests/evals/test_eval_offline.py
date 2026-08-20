"""Offline eval runner driven by tests/evals/cases.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.core.errors import CPQAPIError
from oracle_cpq_mcp.security.context import reset_session_tool_calls
from oracle_cpq_mcp.security.rate_limit import reset_rate_limits
from oracle_cpq_mcp.security.replay import reset_replay_store
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.bml import register_bml_tools
from oracle_cpq_mcp.tools.commerce import register_commerce_tools
from oracle_cpq_mcp.tools.datatables import register_datatable_tools
from oracle_cpq_mcp.tools.discovery import register_discovery_tools
from oracle_cpq_mcp.tools.groups import register_group_tools
from oracle_cpq_mcp.tools.performance import register_performance_tools
from oracle_cpq_mcp.tools.transactions import register_transaction_tools
from oracle_cpq_mcp.tools.users import register_user_tools

CASES_PATH = Path(__file__).with_name("cases.json")


class FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):
        def decorator(fn: Any) -> Any:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


class EvalCPQClient:
    """Configurable fake client for a single eval case."""

    def __init__(self, profile: CPQProfile, case: dict[str, Any]) -> None:
        self.profile = profile
        self.case = case

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        if self.case.get("mock_error"):
            code = int(self.case["mock_error"].get("status_code", 500))
            raise CPQAPIError(
                f"CPQ API error {code}",
                status_code=code,
                method="GET",
                path=path,
                body={"title": "error"},
            )
        if "mock_user" in self.case and path.startswith("/users/") and path.count("/") == 2:
            return dict(self.case["mock_user"])
        if "mock" in self.case:
            return dict(self.case["mock"])
        if path.startswith("/users/") and path.count("/") == 2:
            return {"partyNumber": path.rsplit("/", 1)[-1], "login": "eval_user"}
        if path.startswith("/datatables/") and path.count("/") == 2:
            return {"name": path.rsplit("/", 1)[-1]}
        return {"items": [], "hasMore": False, "offset": 0, "limit": 100}

    def get_bytes(self, path: str, *, params: dict[str, Any] | None = None) -> bytes:
        return b"PK\x03\x04eval"

    def post(self, path: str, *, json_body: Any = None, params: dict[str, Any] | None = None) -> Any:
        return {}

    def patch(self, path: str, *, json_body: Any) -> Any:
        return {}


def _load_cases() -> list[dict[str, Any]]:
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    return list(payload["cases"])


def _lead(result: Any) -> dict[str, Any]:
    if isinstance(result, list):
        assert result and isinstance(result[0], dict)
        return result[0]
    assert isinstance(result, dict)
    return result


def _register_all(client: EvalCPQClient) -> dict[str, Any]:
    mcp = FakeMcp()
    register_user_tools(mcp, client)  # type: ignore[arg-type]
    register_group_tools(mcp, client)  # type: ignore[arg-type]
    register_datatable_tools(mcp, client)  # type: ignore[arg-type]
    register_bml_tools(mcp, client)  # type: ignore[arg-type]
    register_commerce_tools(mcp, client)  # type: ignore[arg-type]
    register_transaction_tools(mcp, client)  # type: ignore[arg-type]
    register_performance_tools(mcp, client)  # type: ignore[arg-type]
    register_discovery_tools(mcp)
    return mcp.tools


@pytest.mark.parametrize("case", _load_cases(), ids=lambda c: c["id"])
def test_eval_offline_case(case: dict[str, Any]) -> None:
    reset_session_tool_calls()
    reset_rate_limits()
    reset_replay_store()

    profile = CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v18",
        company_login_name="_host",
        read_only=False,
        custom_data_table_names=["ModelMaster"],
        commerce_process_var_names=["oraclecpqo"],
    )
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

    client = EvalCPQClient(profile, case)
    tools = _register_all(client)
    tool_name = case["tool"]
    result = tools[tool_name](**case.get("kwargs", {}))
    envelope = _lead(result)
    expect = case["expect"]

    assert envelope.get("status") == expect["status"]
    assert envelope.get("environment") == "dev"
    assert "retrieved_at" in envelope

    if expect.get("code"):
        assert envelope.get("code") == expect["code"]

    if expect.get("attachment"):
        assert isinstance(result, list) and len(result) >= 2
        data = envelope.get("data") or {}
        if "truncated" in expect:
            assert data.get("truncated") is expect["truncated"]
        if "row_count" in expect:
            assert data.get("row_count") == expect["row_count"]
        return

    data = envelope.get("data") or {}

    if "items_len" in expect:
        items = data.get("items") or []
        assert len(items) == expect["items_len"]

    if expect.get("has_pagination_next"):
        pagination = envelope.get("pagination") or data.get("pagination") or {}
        assert pagination.get("nextOffset") is not None or pagination.get("suggestedNextCall")

    if expect.get("data_login"):
        assert data.get("login") == expect["data_login"]

    if expect.get("data_contains_tool"):
        tools_list = data.get("tools") or data.get("items") or []
        names = {
            (t.get("name") if isinstance(t, dict) else None)
            for t in tools_list
        }
        # discover_tools_result shape may nest differently
        if expect["data_contains_tool"] not in names:
            blob = json.dumps(data)
            assert expect["data_contains_tool"] in blob
