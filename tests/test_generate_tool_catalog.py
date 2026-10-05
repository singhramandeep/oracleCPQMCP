"""Tests for oracle_cpq_mcp.cli.generate_tool_catalog."""

from __future__ import annotations

from pathlib import Path

from oracle_cpq_mcp.cli import generate_tool_catalog as gen
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG


def test_format_method_and_urls_rest_and_local() -> None:
    users = TOOL_CATALOG["list_users"]
    method, cpq_url, fusion_url = gen.format_method_and_urls(users)
    assert method == "GET"
    assert cpq_url == "/rest/{rest_api_version}/users"
    assert fusion_url == "/cpq/rest/{rest_api_version}/users"

    local = TOOL_CATALOG["discover_tools"]
    method_l, cpq_l, fusion_l = gen.format_method_and_urls(local)
    assert method_l == "—"
    assert cpq_l == "— (local / no CPQ REST)"
    assert fusion_l == "— (local / no CPQ REST)"

    territories = TOOL_CATALOG["list_territories"]
    method_t, cpq_t, fusion_t = gen.format_method_and_urls(territories)
    assert method_t == "GET"
    assert "CX" in cpq_t and "not CPQ" in cpq_t
    assert fusion_t == "/crmRestApi/resources/11.13.18.05/territories"


def test_format_method_and_endpoint_compat_shorthand() -> None:
    users = TOOL_CATALOG["list_users"]
    method, endpoint = gen.format_method_and_endpoint(users)
    assert method == "GET"
    assert endpoint == "/rest|cpq/rest/{rest_api_version}/users"


def test_generate_tool_catalog_per_tool_tables(tmp_path: Path) -> None:
    out = tmp_path / "TOOL_CATALOG.md"
    path = gen.write_catalog(out)
    text = path.read_text(encoding="utf-8")
    assert text.strip()
    assert f"**Total tools:** {len(TOOL_CATALOG)}" in text
    assert "### Read tools" in text
    assert "### Write tools" in text
    assert "#### `list_users`" in text
    assert "| **CX module** |" in text
    assert "| **CPQ REST URL** |" in text
    assert "| **Fusion REST URL** |" in text
    assert "CRM REST" in text
    assert "`/crmRestApi/" in text or "/crmRestApi/" in text
    assert "| **Endpoint** |" not in text
    assert "| **Parameters** |" in text
    assert "`/rest/{rest_api_version}/users`" in text
    assert "`/cpq/rest/{rest_api_version}/users`" in text
    assert "| Tool | Version | Risk | Method | Endpoint |" not in text
    assert "### Tool reference" not in text
    for name in TOOL_CATALOG:
        assert f"`{name}`" in text
    domains = {spec.domain for spec in TOOL_CATALOG.values()}
    for domain in domains:
        assert f"## {domain}" in text


def test_generate_tool_catalog_main_default(tmp_path: Path) -> None:
    out = tmp_path / "out.md"
    assert gen.main(["--out", str(out)]) == 0
    assert out.is_file()
    body = out.read_text(encoding="utf-8")
    assert f"**Total tools:** {len(TOOL_CATALOG)}" in body
    assert all(f"`{name}`" in body for name in TOOL_CATALOG)
    assert "HTTP / API" not in body
