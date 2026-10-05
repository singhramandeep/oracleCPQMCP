"""Tests for customer knowledge memory (core + tools helpers)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from oracle_cpq_mcp.core.config import load_profile, update_profile_env_key
from oracle_cpq_mcp.core.knowledge import (
    BASE_KNOWLEDGE_FILENAME,
    KnowledgeError,
    append_customer_knowledge_entry,
    default_customer_knowledge_filename,
    ensure_customer_knowledge_stub,
    read_customer_knowledge_file,
    resolve_customer_knowledge_path,
    resolve_knowledge_basename,
    scan_for_secrets,
)


@pytest.fixture()
def project_root(tmp_path: Path) -> Path:
    (tmp_path / "knowledge").mkdir()
    return tmp_path


def test_default_filename() -> None:
    assert default_customer_knowledge_filename("hunterFusion") == "hunterFusion.md"


def test_path_traversal_rejected(project_root: Path) -> None:
    with pytest.raises(KnowledgeError, match="basename"):
        resolve_knowledge_basename("../etc/passwd", project_root=project_root)
    with pytest.raises(KnowledgeError, match="basename"):
        resolve_knowledge_basename("sub/dir.md", project_root=project_root)


def test_refuse_shared_base_knowledge(project_root: Path) -> None:
    with pytest.raises(KnowledgeError, match="shared"):
        resolve_knowledge_basename(BASE_KNOWLEDGE_FILENAME, project_root=project_root)


def test_append_creates_dated_env_entry(project_root: Path) -> None:
    path = resolve_knowledge_basename("acme.md", project_root=project_root)
    ensure_customer_knowledge_stub(path, customer_name="Acme")
    meta = append_customer_knowledge_entry(
        path,
        environment="dev",
        title="Commerce process",
        body="- process_var_name=oraclecpqo\n- use base commerce process alias",
        tags=["commerce"],
    )
    text = path.read_text(encoding="utf-8")
    assert "## Commerce process" in text
    assert "env: dev" in text
    assert "tags: commerce" in text
    assert "oraclecpqo" in text
    assert meta["bytes_appended"] > 0
    assert meta["exists"] is True


def test_secret_like_content_rejected(project_root: Path) -> None:
    path = resolve_knowledge_basename("acme.md", project_root=project_root)
    ensure_customer_knowledge_stub(path, customer_name="Acme")
    with pytest.raises(KnowledgeError, match="secret"):
        append_customer_knowledge_entry(
            path,
            environment="dev",
            title="Bad",
            body="password: hunter2",
        )
    assert scan_for_secrets("Bearer abcdefghijklmnop") is not None
    assert scan_for_secrets("oauth_client_secret=xyz") is not None


def test_resolve_uses_profile_field_or_default(project_root: Path) -> None:
    profile = SimpleNamespace(
        customer_id="focalpoint",
        customer_knowledge_file="site.md",
    )
    path = resolve_customer_knowledge_path(profile, project_root=project_root)  # type: ignore[arg-type]
    assert path.name == "site.md"

    profile2 = SimpleNamespace(
        customer_id="focalpoint",
        customer_knowledge_file=None,
    )
    path2 = resolve_customer_knowledge_path(profile2, project_root=project_root)  # type: ignore[arg-type]
    assert path2.name == "focalpoint.md"


def test_read_missing_file(project_root: Path) -> None:
    path = project_root / "knowledge" / "missing.md"
    meta = read_customer_knowledge_file(path)
    assert meta["exists"] is False
    assert meta["text"] == ""
    assert meta["character_count"] == 0


@pytest.fixture()
def config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cfg = tmp_path / ".config"
    cfg.mkdir()
    monkeypatch.setenv("CPQ_CONFIG_DIR", str(cfg))
    monkeypatch.delenv("CPQ_ENVIRONMENT", raising=False)
    monkeypatch.delenv("CPQ_FRUGAL_MODE", raising=False)
    return cfg


def test_ensure_sets_yaml_customer_knowledge_file(
    config_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "knowledge").mkdir()
    yaml_text = """\
version: 1.04
customer_name: Memory Corp
cpq_mode: standalone
default_environment: dev
rest_api_version: v18
environments:
  dev:
    url: https://mem-dev.example.com
    credentials:
      - username: u1
        password: p1
"""
    (config_dir / "memorycorp.yaml").write_text(yaml_text, encoding="utf-8")
    profile = load_profile("memorycorp")
    assert profile.customer_knowledge_file is None

    path = update_profile_env_key(
        "memorycorp", "CUSTOMER_KNOWLEDGE_FILE", "memorycorp.md"
    )
    assert path.is_file()
    reloaded = load_profile("memorycorp")
    assert reloaded.customer_knowledge_file == "memorycorp.md"


def test_catalog_has_customer_knowledge_tools() -> None:
    from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
    from oracle_cpq_mcp.security.validation import TOOL_INPUT_MODELS

    for name in (
        "get_customer_knowledge",
        "ensure_customer_knowledge",
        "append_customer_knowledge",
    ):
        assert name in TOOL_CATALOG
        assert TOOL_CATALOG[name].domain == "meta"
        assert name in TOOL_INPUT_MODELS
