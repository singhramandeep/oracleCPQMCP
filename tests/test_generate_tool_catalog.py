"""Tests for scripts/generate_tool_catalog.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "generate_tool_catalog.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_tool_catalog", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generate_tool_catalog_writes_all_tools(tmp_path: Path) -> None:
    gen = _load_generator()
    out = tmp_path / "TOOL_CATALOG.md"
    path = gen.write_catalog(out)
    text = path.read_text(encoding="utf-8")
    assert text.strip()
    assert f"**Total tools:** {len(TOOL_CATALOG)}" in text
    for name in TOOL_CATALOG:
        assert f"`{name}`" in text
    # One table header per domain that has tools
    domains = {spec.domain for spec in TOOL_CATALOG.values()}
    for domain in domains:
        assert f"## {domain}" in text


def test_generate_tool_catalog_main_default(tmp_path: Path, monkeypatch) -> None:
    gen = _load_generator()
    out = tmp_path / "out.md"
    assert gen.main(["--out", str(out)]) == 0
    assert out.is_file()
    body = out.read_text(encoding="utf-8")
    assert f"**Total tools:** {len(TOOL_CATALOG)}" in body
    assert all(f"`{name}`" in body for name in TOOL_CATALOG)
