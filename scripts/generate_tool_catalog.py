#!/usr/bin/env python3
"""Generate a formal Markdown tool catalog from the live MCP catalog.

Usage (from repo root):
    python scripts/generate_tool_catalog.py
    python scripts/generate_tool_catalog.py --out docs/TOOL_CATALOG.md
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, get_args, get_origin

from pydantic.fields import PydanticUndefined

# Prefer the workspace package over any stale site-packages copy.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_MCP = str(_REPO_ROOT / "mcp")
if _MCP in sys.path:
    sys.path.remove(_MCP)
sys.path.insert(0, _MCP)

from oracle_cpq_mcp.registry.tool_registry import (  # noqa: E402
    TOOL_CATALOG,
    ToolSpec,
)
from oracle_cpq_mcp.schemas.tool_outputs import (  # noqa: E402
    TOOL_OUTPUT_SCHEMAS,
    get_tool_output_schema,
)
from oracle_cpq_mcp.security.validation import TOOL_INPUT_MODELS  # noqa: E402

DEFAULT_OUT = _REPO_ROOT / "docs" / "TOOL_CATALOG.md"

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
        # Optional[X] → X | None
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
        "> python scripts/generate_tool_catalog.py",
        "> ```",
        "",
        f"**Total tools:** {len(TOOL_CATALOG)}",
        "",
        "This document is the formal per-tool reference for the GitHub repository. "
        "Each row is one MCP tool function with **Parameters** and **Filters** "
        "(from Pydantic validation models), output contract, tags, and API metadata "
        "from `TOOL_CATALOG`.",
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
        specs = sorted(by_domain[domain], key=lambda s: s.name)
        lines.extend(
            [
                f"## {domain}",
                "",
                f"_{len(specs)} tool(s)_",
                "",
                "| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |",
                "|------|---------|----|------|------|------------|------------|---------|--------|",
            ]
        )
        for spec in specs:
            tool_cell = f"`{spec.name}`"
            if spec.title and spec.title.lower().replace(" ", "_") != spec.name:
                tool_cell = f"`{spec.name}`<br>{_escape_cell(spec.title)}"
            http_api = "—"
            if spec.http_method or spec.api_path:
                method = spec.http_method or ""
                path = spec.api_path or ""
                http_api = _escape_cell(f"{method} {path}".strip())
            tags = ", ".join(f"`{t}`" for t in sorted(spec.tags))
            params_s, filters_s = format_parameters_and_filters(spec.name)
            row = (
                f"| {tool_cell} "
                f"| `{spec.version}` "
                f"| `{spec.operation}` "
                f"| `{spec.risk}` "
                f"| {_escape_cell(tags)} "
                f"| {http_api} "
                f"| {_escape_cell(params_s)} "
                f"| {_escape_cell(filters_s)} "
                f"| {_escape_cell(format_output(spec.name, operation=spec.operation))} |"
            )
            lines.append(row)

        lines.extend(["", "### Descriptions", ""])
        for spec in specs:
            lines.append(f"- **`{spec.name}`** — {_escape_cell(_truncate(spec.description))}")
        lines.append("")

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
            "python scripts/generate_tool_catalog.py",
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
    parser = argparse.ArgumentParser(
        description="Generate docs/TOOL_CATALOG.md from the live MCP tool catalog."
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help=f"Output markdown path (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args(argv)
    out = args.out if args.out.is_absolute() else (_REPO_ROOT / args.out).resolve()
    path = write_catalog(out)
    print(f"Wrote {len(TOOL_CATALOG)} tools -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
