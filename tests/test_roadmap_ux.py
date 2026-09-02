"""Tests for local jobs, BML search, HTTP timeout, and envelope profile stamp."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet, _resolve_http_timeout
from oracle_cpq_mcp.core.local_jobs import create_job, read_job, start_background_job, update_job
from oracle_cpq_mcp.core.responses import stamp_response_context
from oracle_cpq_mcp.security.context import reset_session_tool_calls
from oracle_cpq_mcp.security.rate_limit import reset_rate_limits
from oracle_cpq_mcp.security.replay import reset_replay_store
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.bml import register_bml_tools


def _profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CPQProfile:
    monkeypatch.setenv("CPQ_LOCAL_DATA_DIR", str(tmp_path / "data"))
    return CPQProfile(
        customer_name="Test",
        customer_id="testco",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v19",
        http_timeout=120.0,
        read_only=True,
    )


def test_resolve_http_timeout_host_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CPQ_HTTP_TIMEOUT", "240")
    assert _resolve_http_timeout({"HTTP_TIMEOUT": "60"}) == 240.0


def test_resolve_http_timeout_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CPQ_HTTP_TIMEOUT", raising=False)
    assert _resolve_http_timeout({"HTTP_TIMEOUT": "180"}) == 180.0


def test_stamp_includes_profile() -> None:
    ctx = SimpleNamespace(environment="dev", customer_id="focalpoint")
    stamped = stamp_response_context({"status": "ok", "tool": "x", "data": {}}, ctx)
    assert stamped["profile"] == "focalpoint"
    assert stamped["customer_id"] == "focalpoint"
    assert stamped["environment"] == "dev"
    assert "retrieved_at" in stamped


def test_local_job_lifecycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    profile = _profile(tmp_path, monkeypatch)
    record = create_job(profile, kind="test", message="hi")
    job_id = record["job_id"]
    assert read_job(profile, job_id)["status"] == "queued"
    update_job(profile, job_id, status="succeeded", result={"ok": True})
    assert read_job(profile, job_id)["result"]["ok"] is True


def test_start_background_job_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    profile = _profile(tmp_path, monkeypatch)
    done = {"v": False}

    def worker(job_id: str) -> None:
        done["v"] = True
        update_job(profile, job_id, status="succeeded", message="done", result={"x": 1})

    record = start_background_job(
        profile, kind="unit", message="go", worker=worker
    )
    thread_job = record["job_id"]
    # Join via polling file
    import time

    for _ in range(50):
        current = read_job(profile, thread_job)
        if current and current.get("status") == "succeeded":
            break
        time.sleep(0.05)
    assert done["v"] is True
    assert read_job(profile, thread_job)["status"] == "succeeded"


def test_search_local_bml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    profile = _profile(tmp_path, monkeypatch)
    site = tmp_path / "data" / "testco" / "dev" / "bml" / "site"
    site.mkdir(parents=True)
    (site / "demo.bml").write_text("return ModelMaster;\n", encoding="utf-8")

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
    mcp = type("M", (), {"tools": {}, "tool": lambda self, **k: (lambda f: self.tools.__setitem__(f.__name__, f) or f)})()
    # Fake mcp.tool decorator
    class FakeMcp:
        def __init__(self) -> None:
            self.tools: dict = {}

        def tool(self, **_kwargs):  # noqa: ANN001
            def deco(fn):  # noqa: ANN001
                self.tools[fn.__name__] = fn
                return fn

            return deco

    fake = FakeMcp()
    register_bml_tools(fake, client)  # type: ignore[arg-type]
    result = fake.tools["search_local_bml"](query="ModelMaster")
    data = result.get("data", result) if isinstance(result, dict) else result
    assert data["match_count"] >= 1
    assert "ModelMaster" in data["matches"][0]["snippet"]


def test_local_resource_index(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    profile = _profile(tmp_path, monkeypatch)
    site = tmp_path / "data" / "testco" / "dev" / "bml" / "site"
    site.mkdir(parents=True)
    (site / "x.bml").write_text("ok\n", encoding="utf-8")

    registered: dict[str, Any] = {}

    class FakeMcp:
        def resource(self, uri: str):  # noqa: ANN001
            def deco(fn):  # noqa: ANN001
                registered[uri] = fn
                return fn

            return deco

    from oracle_cpq_mcp.prompts.local_resources import register_local_data_resources

    register_local_data_resources(FakeMcp(), profile)
    import json

    index = json.loads(registered["cpq://local"]())
    assert index["profile"] == "testco"
    assert index["bml"]["site_exists"] is True
    file_payload = json.loads(registered["cpq://local/bml/{path}"]("site/x.bml"))
    assert "ok" in file_payload["content"]


def test_elicit_or_fallback_unsupported() -> None:
    import asyncio

    from oracle_cpq_mcp.prompts.elicitation import elicit_or_fallback, fallback_payload

    outcome = asyncio.run(
        elicit_or_fallback(
            None, message="Pick one", response_type=str, choices=["a", "b"]
        )
    )
    assert outcome.status == "unsupported"
    assert outcome.needs_user_input is True
    payload = fallback_payload(outcome)
    assert payload["needs_user_input"] is True
    assert payload["choices"] == ["a", "b"]
