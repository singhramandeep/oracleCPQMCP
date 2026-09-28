"""Tests for Prompt Studio read-only profile YAML and workspace path APIs."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def config_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config = tmp_path / ".config"
    config.mkdir()
    prompts = tmp_path / ".prompts"
    prompts.mkdir()
    (prompts / "saved_prompts.json").write_text(
        '{"version": 1, "prompts": []}\n', encoding="utf-8"
    )
    logs = tmp_path / "logs"
    logs.mkdir()
    data = tmp_path / "data" / "acme" / "dev" / "exports"
    data.mkdir(parents=True)

    yaml_text = """version: 1
customer_name: Acme
default_environment: dev
rest_api_version: v18
company_login_name: _host
read_only: true
debug_mode: true
environments:
  dev:
    url: https://acme-dev.example.com
    credentials:
      - username: api.user
        password: super-secret-password
"""
    (config / "acme.yaml").write_text(yaml_text, encoding="utf-8")
    (config / ".profile.yaml.example").write_text(
        "version: 1\ncustomer_name: Example\n", encoding="utf-8"
    )
    (logs / "acme-dev.log").write_text("========== 2026-01-01 ==========\n", encoding="utf-8")

    monkeypatch.setenv("CPQ_CONFIG_DIR", str(config))
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(prompts / "saved_prompts.json"))
    monkeypatch.setenv("CPQ_PROMPT_STUDIO_PATH", str(config / "prompt_studio.json"))
    monkeypatch.setenv("CPQ_DEBUG_LOG_DIR", str(logs))
    monkeypatch.setenv("CPQ_LOCAL_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(
        "oracle_cpq_mcp.core.config.find_project_root",
        lambda: tmp_path,
    )
    monkeypatch.setattr(
        "oracle_cpq_mcp.core.local_data.find_project_root",
        lambda: tmp_path,
    )

    from apps.prompt_studio.app import create_app

    return TestClient(create_app()), tmp_path


def test_list_config_profiles(config_client) -> None:
    client, _ = config_client
    res = client.get("/api/config/profiles")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] >= 1
    names = {p["customer_id"] for p in body["profiles"]}
    assert "acme" in names
    assert ".profile" not in names


def test_get_config_profile_redacts_secrets(config_client) -> None:
    client, _ = config_client
    res = client.get("/api/config/profiles/acme")
    assert res.status_code == 200
    body = res.json()
    assert body["customer_id"] == "acme"
    assert body["kind"] == "yaml"
    assert "super-secret-password" not in body["yaml_redacted"]
    assert "[REDACTED]" in body["yaml_redacted"]
    assert body["document"]["environments"]["dev"]["credentials"][0]["password"] == (
        "[REDACTED]"
    )


def test_config_profile_rejects_traversal(config_client) -> None:
    client, _ = config_client
    # Path-segment tricks and dotted ids must not open arbitrary files.
    assert client.get("/api/config/profiles/..acme").status_code == 400
    assert client.get("/api/config/profiles/../acme").status_code == 404
    assert client.get("/api/config/profiles/acme/../../secret").status_code == 404


def test_workspace_paths(config_client) -> None:
    client, tmp_path = config_client
    res = client.get(
        "/api/workspace/paths",
        params={"profile": "acme", "environment": "dev"},
    )
    assert res.status_code == 200
    body = res.json()
    paths = body["paths"]
    assert paths["profile_yaml"]["exists"] is True
    assert paths["profile_yaml"]["path"].endswith("acme.yaml")
    assert paths["saved_prompts"]["exists"] is True
    assert paths["logs_dir"]["exists"] is True
    assert paths["debug_log"]["exists"] is True
    assert "acme-dev.log" in paths["debug_log"]["path"]
    assert paths["exports_dir"]["exists"] is True
    assert "exports" in paths["exports_dir"]["path"]
    assert paths["local_data_root"]["exists"] is True


def test_ui_mentions_profiles_paths_view(config_client) -> None:
    client, _ = config_client
    html = client.get("/").text
    assert 'data-view="config"' in html
    assert 'id="configView"' in html
    assert 'id="modalFeedback"' in html
    js = client.get("/static/app.js").text
    assert "renderSourceStats" in js
    assert "loadConfigProfiles" in js
    assert "rating" in js
