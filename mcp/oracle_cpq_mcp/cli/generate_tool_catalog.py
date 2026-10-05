"""Generate a formal Markdown tool catalog from the live MCP catalog."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any, get_args, get_origin

from pydantic.fields import PydanticUndefined

from oracle_cpq_mcp.core.config import find_project_root
from oracle_cpq_mcp.registry.tool_registry import (
    FUSION_CX_MODULE_NAMES,
    TOOL_CATALOG,
    ToolSpec,
)
from oracle_cpq_mcp.schemas.tool_outputs import (
    TOOL_OUTPUT_SCHEMAS,
    get_tool_output_schema,
)
from oracle_cpq_mcp.security.validation import TOOL_INPUT_MODELS

_DOMAIN_ORDER = (
    "users",
    "groups",
    "datatables",
    "bml",
    "commerce",
    "performance",
    "parts",
    "tasks",
    "configuration",
    "metrics",
    "collab",
    "admin",
    "sales",
    "prm",
    "service",
    "field_service",
    "subscription",
    "incentive_compensation",
    "meta",
)


def _escape_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def _annotation_str(annotation: Any) -> str:
    if annotation is None:
        return "Any"
    origin = get_origin(annotation)
    if origin is None:
        return getattr(annotation, "__name__", str(annotation).replace("typing.", ""))
    args = get_args(annotation)
    if not args:
        return getattr(origin, "__name__", str(origin))
    inner = ", ".join(_annotation_str(a) for a in args)
    name = getattr(origin, "__name__", str(origin))
    if name == "Union" or str(origin) == "typing.Union":
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and type(None) in args:
            return f"{_annotation_str(non_none[0])} | None"
        return " | ".join(_annotation_str(a) for a in args)
    if name == "Literal":
        vals = ", ".join(repr(a) for a in args[:6])
        if len(args) > 6:
            vals += ", …"
        return f"Literal[{vals}]"
    return f"{name}[{inner}]"


_FILTER_FIELD_NAMES = frozenset(
    {
        "status_filter",
        "q_expr",
        "query",
        "tag",
        "tool",
        "tool_domain",
        "domain",
        "operation",
        "cx_module",
    }
)


def _is_filter_field(name: str, description: str | None) -> bool:
    """Classify an input field as a query/filter vs a general parameter."""
    lower = name.lower()
    if lower in _FILTER_FIELD_NAMES:
        return True
    if lower.endswith("_filter") or "filter" in lower:
        return True
    desc = (description or "").lower()
    if "filter" in desc and "confirmation" not in desc:
        return True
    return False


def _format_field(name: str, field: Any) -> str:
    typ = _annotation_str(field.annotation)
    if field.is_required():
        return f"`{name}` ({typ}, required)"
    default = field.default
    if default is PydanticUndefined:
        default_s = "optional"
    elif default is None:
        default_s = "default None"
    else:
        default_s = f"default {default!r}"
    return f"`{name}` ({typ}, {default_s})"


def format_parameters_and_filters(tool_name: str) -> tuple[str, str]:
    """Split validation-model fields into (parameters, filters) cell strings."""
    model_cls = TOOL_INPUT_MODELS.get(tool_name)
    if model_cls is None:
        return "_(no input model)_", "-"
    params: list[str] = []
    filters: list[str] = []
    for name, field in model_cls.model_fields.items():
        desc = field.description
        cell = _format_field(name, field)
        if _is_filter_field(name, desc):
            filters.append(cell)
        else:
            params.append(cell)
    params_s = "; ".join(params) if params else "-"
    filters_s = "; ".join(filters) if filters else "-"
    return params_s, filters_s


def format_output(tool_name: str, *, operation: str) -> str:
    """Short human label for the tool output contract."""
    if tool_name in TOOL_OUTPUT_SCHEMAS and TOOL_OUTPUT_SCHEMAS[tool_name] is None:
        return "attachment/list (no root object schema)"
    schema = get_tool_output_schema(tool_name)
    if schema is None:
        return "unspecified / flexible"
    props = (schema or {}).get("properties") if isinstance(schema, dict) else None
    if isinstance(props, dict) and "tools" in props:
        return "discover_tools schema"
    if isinstance(props, dict) and {"status", "tool", "data"}.issubset(props.keys()):
        if operation == "write":
            return "write envelope `{status, tool, data}`"
        return "read envelope `{status, tool, data}`"
    title = str((schema or {}).get("title") or "") if isinstance(schema, dict) else ""
    if title:
        return title
    return "JSON object envelope"


def _truncate(text: str, limit: int = 220) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def format_method_and_urls(spec: ToolSpec) -> tuple[str, str, str]:
    """Return (Method, CPQ REST URL, Fusion REST URL) cells for the catalog table.

    Paths are relative to the site base URL. Standalone uses
    ``/rest/{rest_api_version}``; fusion uses ``/cpq/rest/{rest_api_version}``.
    ``CPQClient`` selects one prefix when ``cpq_mode: fusion`` and
    ``fusion_enabled: true``. CX REST paths (``/crmRestApi/...``) use the
    profile ``cx.url`` with no CPQ prefix.
    """
    local = "— (local / no CPQ REST)"
    if not spec.http_method and not spec.api_path:
        return "—", local, local
    method = spec.http_method or "—"
    if spec.api_path:
        path = spec.api_path if spec.api_path.startswith("/") else f"/{spec.api_path}"
        if path.startswith("/crmRestApi") or spec.cx_module in FUSION_CX_MODULE_NAMES:
            label = spec.cx_module.replace("_", " ").title()
            return method, f"— (CX {label} REST; not CPQ)", path
        cpq_url = f"/rest/{{rest_api_version}}{path}"
        fusion_url = f"/cpq/rest/{{rest_api_version}}{path}"
    else:
        cpq_url = "—"
        fusion_url = "—"
    return method, cpq_url, fusion_url


def format_method_and_endpoint(spec: ToolSpec) -> tuple[str, str]:
    """Compatibility wrapper: Method + combined Endpoint shorthand (tests/legacy)."""
    method, cpq_url, fusion_url = format_method_and_urls(spec)
    if cpq_url.startswith("/") and fusion_url.startswith("/"):
        # Strip leading /rest/ and /cpq/rest/ to rebuild historical shorthand.
        path = cpq_url.removeprefix("/rest/{rest_api_version}")
        endpoint = f"/rest|cpq/rest/{{rest_api_version}}{path}"
        return method, endpoint
    return method, cpq_url


def _split_field_list(cell: str) -> list[str]:
    """Turn a '; '-joined parameters/filters cell into items."""
    if cell in ("-", "—", "_(no input model)_"):
        return []
    return [part.strip() for part in cell.split(";") if part.strip()]


def _fields_cell(cell: str) -> str:
    """Join parameter/filter fields with <br> for a single table cell."""
    items = _split_field_list(cell)
    if not items:
        return "—"
    return "<br>".join(_escape_cell(item) for item in items)


def _tool_anchor(name: str) -> str:
    """GitHub-style heading anchor for #### `name`."""
    return name.lower().replace("_", "-")


def _append_mini_toc(lines: list[str], label: str, specs: list[ToolSpec]) -> None:
    if not specs:
        return
    links = ", ".join(f"[`{s.name}`](#{_tool_anchor(s.name)})" for s in specs)
    lines.append(f"- **{label}:** {links}")


def _url_cell(url: str) -> str:
    if url.startswith("/"):
        return f"`{_escape_cell(url)}`"
    return _escape_cell(url)


def _append_tool_property_table(lines: list[str], spec: ToolSpec) -> None:
    method, cpq_url, fusion_url = format_method_and_urls(spec)
    method_cell = f"`{_escape_cell(method)}`" if method != "—" else "—"
    tags = ", ".join(f"`{t}`" for t in sorted(spec.tags)) or "—"
    params_s, filters_s = format_parameters_and_filters(spec.name)
    output = format_output(spec.name, operation=spec.operation)
    rows = [
        ("Version", f"`{spec.version}`"),
        ("CX module", f"`{spec.cx_module}`"),
        ("Op / Risk", f"`{spec.operation}` / `{spec.risk}`"),
        ("Method", method_cell),
        ("CPQ REST URL", _url_cell(cpq_url)),
        ("Fusion REST URL", _url_cell(fusion_url)),
        ("Tags", _escape_cell(tags)),
        ("Parameters", _fields_cell(params_s)),
        ("Filters", _fields_cell(filters_s)),
        ("Output", _escape_cell(output)),
        ("Description", _escape_cell(_truncate(spec.description))),
    ]
    lines.extend(
        [
            f"#### `{spec.name}`",
            "",
            "| | |",
            "|---|---|",
        ]
    )
    for label, value in rows:
        lines.append(f"| **{label}** | {value} |")
    lines.append("")


def _append_op_section(lines: list[str], heading: str, specs: list[ToolSpec]) -> None:
    if not specs:
        return
    lines.extend([f"### {heading}", ""])
    for spec in specs:
        _append_tool_property_table(lines, spec)


def _render_domain(lines: list[str], domain: str, specs: list[ToolSpec]) -> None:
    specs = sorted(specs, key=lambda s: s.name)
    reads = [s for s in specs if s.operation == "read"]
    writes = [s for s in specs if s.operation == "write"]
    other = [s for s in specs if s.operation not in ("read", "write")]
    lines.extend([f"## {domain}", "", f"_{len(specs)} tool(s)_", ""])
    _append_mini_toc(lines, "Read", reads)
    _append_mini_toc(lines, "Write", writes)
    if other:
        _append_mini_toc(lines, "Other", other)
    lines.append("")
    _append_op_section(lines, "Read tools", reads)
    _append_op_section(lines, "Write tools", writes)
    if other:
        _append_op_section(lines, "Other tools", other)


def build_catalog_markdown() -> str:
    """Render the full TOOL_CATALOG.md body."""
    by_domain: dict[str, list[ToolSpec]] = defaultdict(list)
    for spec in TOOL_CATALOG.values():
        by_domain[spec.domain].append(spec)

    lines: list[str] = [
        "# Oracle CPQ MCP - Tool Catalog",
        "",
        "> **Auto-generated.** Do not edit by hand.",
        "> Regenerate with:",
        ">",
        "> ```bash",
        "> oracle-cpq generate-tool-catalog",
        "> # or: python scripts/generate_tool_catalog.py",
        "> ```",
        "",
        f"**Total tools:** {len(TOOL_CATALOG)}",
        "",
        "This document is the formal per-tool reference for the GitHub repository. "
        "Each domain lists **Read tools** then **Write tools**. "
        "Every tool has one property table (Version, CX module, Op/Risk, Method, "
        "CPQ REST URL, Fusion REST URL, Tags, Parameters, Filters, Output, Description) "
        "so API path and inputs stay together.",
        "",
        "**CPQ REST URL** and **Fusion REST URL** are paths relative to the site base URL. "
        "Standalone (`cpq.hosted: standalone` or omitted): **CPQ REST URL** "
        "(`/rest/{rest_api_version}` + API path). "
        "Fusion-hosted CPQ (`cpq.hosted: fusion`): **Fusion REST URL** "
        "(`/cpq/rest/{rest_api_version}` + API path). "
        "`{rest_api_version}` comes from the profile (e.g. `v18` / `v19`). "
        "`CPQClient` applies the prefix from nested `cpq.hosted` / `cpq.auth` "
        "(legacy `cpq_mode` / `fusion_enabled` still migrate). "
        "Sales/PRM tools put the **CRM REST** path (`/crmRestApi/resources/11.13.18.05/…`) "
        "in the Fusion REST URL column (base `cx.url`); the CPQ column is "
        "`— (CX … REST; not CPQ)`. "
        "Local/meta tools show `— (local / no CPQ REST)` in both columns.",
        "",
        "## Domains",
        "",
    ]
    for domain in _DOMAIN_ORDER:
        if domain in by_domain:
            lines.append(f"- [{domain}](#{domain})")
    for domain in sorted(by_domain):
        if domain not in _DOMAIN_ORDER:
            lines.append(f"- [{domain}](#{domain})")
    lines.append("")

    ordered_domains = [d for d in _DOMAIN_ORDER if d in by_domain]
    ordered_domains.extend(sorted(d for d in by_domain if d not in _DOMAIN_ORDER))

    for domain in ordered_domains:
        _render_domain(lines, domain, by_domain[domain])

    lines.extend(
        [
            "---",
            "",
            "## Regeneration",
            "",
            "After adding or changing tools in `mcp/oracle_cpq_mcp/registry/tool_registry.py` "
            "(and matching input models), run:",
            "",
            "```bash",
            "oracle-cpq generate-tool-catalog",
            "# or: python scripts/generate_tool_catalog.py",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_catalog(out_path: Path) -> Path:
    """Write the catalog markdown to *out_path*."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    body = build_catalog_markdown()
    out_path.write_text(body, encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    repo_root = find_project_root()
    default_out = repo_root / "docs" / "TOOL_CATALOG.md"
    parser = argparse.ArgumentParser(
        description="Generate docs/TOOL_CATALOG.md from the live MCP tool catalog."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=default_out,
        help=f"Output markdown path (default: {default_out})",
    )
    args = parser.parse_args(argv)
    out = args.out if args.out.is_absolute() else (repo_root / args.out).resolve()
    path = write_catalog(out)
    print(f"Wrote {len(TOOL_CATALOG)} tools -> {path}")
    return 0
