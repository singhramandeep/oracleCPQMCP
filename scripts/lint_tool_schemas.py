#!/usr/bin/env python3
"""Fail-closed lint: catalog ↔ input models and Field descriptions.

Usage:
    python scripts/lint_tool_schemas.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running without installing the package when PYTHONPATH=mcp is set,
# or when invoked from repo root with mcp on sys.path.
_REPO_ROOT = Path(__file__).resolve().parents[1]
_MCP = _REPO_ROOT / "mcp"
if str(_MCP) not in sys.path:
    sys.path.insert(0, str(_MCP))

from pydantic.fields import PydanticUndefined  # noqa: E402

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG  # noqa: E402
from oracle_cpq_mcp.security.validation import TOOL_INPUT_MODELS  # noqa: E402

MIN_CATALOG_DESCRIPTION_LEN = 20


def collect_violations() -> list[str]:
    """Return human-readable lint violations (empty if compliant)."""
    violations: list[str] = []

    catalog_names = set(TOOL_CATALOG)
    model_names = set(TOOL_INPUT_MODELS)

    for name in sorted(catalog_names - model_names):
        violations.append(f"{name}: missing input model in TOOL_INPUT_MODELS")
    for name in sorted(model_names - catalog_names):
        violations.append(f"{name}: input model has no TOOL_CATALOG entry")

    for name, spec in sorted(TOOL_CATALOG.items()):
        desc = (spec.description or "").strip()
        if not desc:
            violations.append(f"{name}: catalog description is empty")
        elif len(desc) < MIN_CATALOG_DESCRIPTION_LEN:
            violations.append(
                f"{name}: catalog description too short "
                f"(<{MIN_CATALOG_DESCRIPTION_LEN} chars)"
            )

    for name, model_cls in sorted(TOOL_INPUT_MODELS.items()):
        for field_name, field_info in model_cls.model_fields.items():
            if field_info.annotation is None:
                violations.append(f"{name}.{field_name}: missing type annotation")
            description = (field_info.description or "").strip()
            if not description:
                violations.append(f"{name}.{field_name}: missing Field description")
            # Ensure required vs optional is explicit via default or required flag.
            has_default = field_info.default is not PydanticUndefined
            has_factory = field_info.default_factory is not None
            if not field_info.is_required() and not (has_default or has_factory):
                violations.append(
                    f"{name}.{field_name}: optional field has no default/default_factory"
                )

    return violations


def main() -> int:
    violations = collect_violations()
    if not violations:
        print(
            f"OK: {len(TOOL_CATALOG)} catalog tools, "
            f"{len(TOOL_INPUT_MODELS)} input models — schemas compliant."
        )
        return 0
    print(f"FAIL: {len(violations)} schema lint violation(s):", file=sys.stderr)
    for item in violations:
        print(f"  - {item}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
