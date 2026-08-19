"""Ensure README documents match the live tool catalog."""

from __future__ import annotations

from pathlib import Path

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"

_CATALOG_DOMAINS = frozenset(spec.domain for spec in TOOL_CATALOG.values())


def test_tool_catalog_count() -> None:
    assert len(TOOL_CATALOG) == 19


def test_readme_documents_nineteen_tools() -> None:
    text = README.read_text(encoding="utf-8")
    assert "19 MCP tools" in text
    assert "14 MCP tools" not in text


def test_readme_documents_bml_and_commerce() -> None:
    text = README.read_text(encoding="utf-8")
    assert "get_all_bml_code" in text
    assert "BML" in text
    assert "commerce" in text.lower()


def test_readme_tool_summary_covers_all_domains() -> None:
    text = README.read_text(encoding="utf-8")
    start = text.index("## MCP tools (summary)")
    end = text.index("<details>", start)
    summary_section = text[start:end]
    for domain in _CATALOG_DOMAINS:
        if domain == "meta":
            assert "Meta" in summary_section or "discover_tools" in summary_section
        elif domain == "datatables":
            assert "datatables" in summary_section.lower() or "Data tables" in summary_section
        else:
            assert domain in summary_section.lower()
