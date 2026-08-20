"""Ensure README documents match the live tool catalog."""

from __future__ import annotations

from pathlib import Path

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"

_CATALOG_DOMAINS = frozenset(spec.domain for spec in TOOL_CATALOG.values())


def test_tool_catalog_count() -> None:
    assert len(TOOL_CATALOG) == 67


def test_readme_documents_sixty_seven_tools() -> None:
    text = README.read_text(encoding="utf-8")
    assert "67 MCP tools" in text
    assert "41 MCP tools" not in text
    assert "30 MCP tools" not in text
    assert "29 MCP tools" not in text
    assert "21 MCP tools" not in text
    assert "19 MCP tools" not in text
    assert "14 MCP tools" not in text


def test_readme_documents_bml_commerce_and_performance() -> None:
    text = README.read_text(encoding="utf-8")
    assert "get_all_bml_code" in text
    assert "BML" in text
    assert "commerce" in text.lower()
    assert "list_performance_logs" in text
    assert "performance" in text.lower()
    assert "list_transactions" in text
    assert "list_parts" in text
    assert "get_task" in text
    assert "list_product_families" in text
    assert "Untested" in text
    assert "Testing status" in text


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
