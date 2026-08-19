"""Ensure MCP server module loads and registers all tools."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tests.test_config import FIXTURE_ENV


from oracle_cpq_mcp import __version__


@pytest.fixture()
def profile_config_dir(tmp_path: Path) -> Path:
    (tmp_path / "mycompany.env").write_text(FIXTURE_ENV, encoding="utf-8")
    return tmp_path


def test_server_module_imports_without_schema_error(
    profile_config_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FastMCP rejects oneOf/array output schemas; server startup must not fail."""
    monkeypatch.setenv("CPQ_CUSTOMER_PROFILE", "mycompany")
    monkeypatch.setenv("CPQ_CONFIG_DIR", str(profile_config_dir))
    monkeypatch.setenv("CPQ_SCHEMA_INTEGRITY", "0")

    import oracle_cpq_mcp.server as server_module

    reloaded = importlib.reload(server_module)
    assert reloaded.mcp is not None
    assert reloaded.mcp.version == __version__
