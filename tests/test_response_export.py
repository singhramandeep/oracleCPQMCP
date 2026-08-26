"""Tests for post-response Excel / Word export helpers and tools."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from openpyxl import load_workbook

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.exporters.chat_document import build_docx_from_tables
from oracle_cpq_mcp.exporters.records_excel import build_multi_sheet_workbook
from oracle_cpq_mcp.exporters.response_export import (
    MAX_EXPORT_SHEETS,
    validate_sheets_payload,
    write_export_bytes,
)
from oracle_cpq_mcp.security.context import reset_session_tool_calls
from oracle_cpq_mcp.security.rate_limit import reset_rate_limits
from oracle_cpq_mcp.security.replay import reset_replay_store
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.response_export import register_response_export_tools

try:
    import docx  # noqa: F401

    HAS_DOCX = True
except ImportError:  # pragma: no cover
    HAS_DOCX = False


class FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):
        def decorator(fn: Any) -> Any:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


class FakeClient:
    def __init__(self, profile: CPQProfile) -> None:
        self.profile = profile


def _profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CPQProfile:
    monkeypatch.setenv("CPQ_LOCAL_DATA_DIR", str(tmp_path / "data"))
    cfg = tmp_path / ".config"
    cfg.mkdir()
    (cfg / "demo.env").write_text(
        "CUSTOMER_NAME=Demo\nDEFAULT_ENVIRONMENT=dev\n"
        "DEV_URL=https://dev.example.com\n"
        "DEV_USERNAME=user\nDEV_PASSWORD=secret\n"
        "POST_RESPONSE_EXPORT=ask\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CPQ_CONFIG_DIR", str(cfg))
    monkeypatch.setenv("CPQ_CUSTOMER_PROFILE", "demo")
    return CPQProfile(
        customer_name="Demo",
        customer_id="demo",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v18",
        company_login_name="_host",
        read_only=True,
        post_response_export="ask",
    )


def _register(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    reset_session_tool_calls()
    reset_rate_limits()
    reset_replay_store()
    profile = _profile(tmp_path, monkeypatch)
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
    mcp = FakeMcp()
    register_response_export_tools(mcp, FakeClient(profile))  # type: ignore[arg-type]
    return mcp.tools


_SHEETS = [
    {
        "name": "Alpha",
        "columns": ["id", "label"],
        "rows": [{"id": 1, "label": "one"}, {"id": 2, "label": "two"}],
    },
    {
        "name": "Beta",
        "rows": [{"code": "x", "qty": 3}],
    },
]


def test_build_multi_sheet_workbook_two_sheets() -> None:
    payload = build_multi_sheet_workbook(_SHEETS)
    workbook = load_workbook(filename=BytesIO(payload))
    assert workbook.sheetnames == ["Alpha", "Beta"]
    alpha = workbook["Alpha"]
    assert [c.value for c in alpha[1]] == ["id", "label"]
    assert alpha[2][0].value == "1"
    beta = workbook["Beta"]
    assert [c.value for c in beta[1]] == ["code", "qty"]


def test_validate_sheets_payload_caps() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        validate_sheets_payload([])
    too_many = [{"name": f"S{i}", "rows": []} for i in range(MAX_EXPORT_SHEETS + 1)]
    with pytest.raises(ValueError, match="max"):
        validate_sheets_payload(too_many)


@pytest.mark.skipif(not HAS_DOCX, reason="python-docx not installed")
def test_build_docx_from_tables() -> None:
    from docx import Document

    payload = build_docx_from_tables(
        title="Sample",
        sheets=_SHEETS,
        notes="Intro line",
    )
    assert payload[:2] == b"PK"
    document = Document(BytesIO(payload))
    texts = [p.text for p in document.paragraphs]
    assert "Sample" in texts
    assert "Intro line" in texts
    assert len(document.tables) == 2


@pytest.mark.skipif(HAS_DOCX, reason="only when python-docx missing")
def test_build_docx_requires_dependency() -> None:
    with pytest.raises(RuntimeError, match="python-docx"):
        build_docx_from_tables(title="X", sheets=_SHEETS)


def test_offer_export_response_needs_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools = _register(tmp_path, monkeypatch)
    result = tools["offer_export_response"](title="Demo table", sheets=_SHEETS)
    assert result["status"] == "ok"
    assert result["data"]["needs_user_input"] is True
    assert any("excel" in c for c in result["data"]["choices"])


def test_export_response_excel_writes_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools = _register(tmp_path, monkeypatch)
    result = tools["export_response_excel"](title="Demo table", sheets=_SHEETS)
    assert isinstance(result, list)
    lead = result[0]
    assert lead["status"] == "ok"
    path = Path(lead["data"]["absolute_path"])
    assert path.exists()
    assert path.suffix == ".xlsx"
    assert "exports" in lead["data"]["path"]


@pytest.mark.skipif(not HAS_DOCX, reason="python-docx not installed")
def test_export_response_word_writes_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools = _register(tmp_path, monkeypatch)
    result = tools["export_response_word"](
        title="Demo table", sheets=_SHEETS, notes="Hello"
    )
    assert isinstance(result, list)
    lead = result[0]
    assert lead["status"] == "ok"
    assert lead["data"]["uri"].startswith("file:")
    assert Path(lead["data"]["absolute_path"]).exists()


def test_set_post_response_export_writes_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tools = _register(tmp_path, monkeypatch)
    result = tools["set_post_response_export"](policy="never")
    assert result["data"]["policy"] == "never"
    text = (tmp_path / ".config" / "demo.env").read_text(encoding="utf-8")
    assert "POST_RESPONSE_EXPORT=never" in text


def test_write_export_bytes_roundtrip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = _profile(tmp_path, monkeypatch)
    path = write_export_bytes(profile, "sample.xlsx", b"abc")
    assert path.read_bytes() == b"abc"
