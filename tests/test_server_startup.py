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


def test_server_startup_fusion_mode_without_basic_auth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fusion profiles have no username/password — startup must not access them."""
    yaml_text = """\
version: 1.03
customer_name: Fusion Startup
cpq_mode: fusion
fusion_enabled: true
default_environment: dev
rest_api_version: v19
environments:
  dev:
    url: https://fusion-dev.example.com
    oauth_token_url: https://idcs.example.com/oauth2/v1/token
    oauth_client_id: client-id
    oauth_client_secret: client-secret
    oauth_scope: urn:opc:resource:fusion:demo:cpq/
"""
    (tmp_path / "fusion.yaml").write_text(yaml_text, encoding="utf-8")
    monkeypatch.setenv("CPQ_CUSTOMER_PROFILE", "fusion")
    monkeypatch.setenv("CPQ_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("CPQ_ENVIRONMENT", "dev")
    monkeypatch.setenv("CPQ_SCHEMA_INTEGRITY", "0")

    import oracle_cpq_mcp.server as server_module

    reloaded = importlib.reload(server_module)
    assert reloaded._profile.cpq_mode == "fusion"
    assert reloaded._profile.fusion_enabled is True
    assert reloaded._profile.uses_fusion is True
    assert reloaded._profile.credentials == []
