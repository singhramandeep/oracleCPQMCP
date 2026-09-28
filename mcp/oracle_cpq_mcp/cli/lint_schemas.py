"""Fail-closed lint: catalog ↔ input models and Field descriptions."""

from __future__ import annotations

import sys

from pydantic.fields import PydanticUndefined

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.security.schema_integrity import (
    SEMVER_RE,
    collect_version_bump_violations,
    load_manifest,
)
from oracle_cpq_mcp.security.validation import TOOL_INPUT_MODELS

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
        title = (spec.title or "").strip()
        if not title:
            violations.append(f"{name}: catalog title is empty")
        version = (spec.version or "").strip()
        if not version:
            violations.append(f"{name}: catalog version is empty")
        elif not SEMVER_RE.match(version):
            violations.append(
                f"{name}: catalog version {version!r} must be semver MAJOR.MINOR.PATCH"
            )
        if not spec.icons:
            violations.append(f"{name}: catalog icons resolved empty (need ≥1)")

    for name, model_cls in sorted(TOOL_INPUT_MODELS.items()):
        for field_name, field_info in model_cls.model_fields.items():
            if field_info.annotation is None:
                violations.append(f"{name}.{field_name}: missing type annotation")
            description = (field_info.description or "").strip()
            if not description:
                violations.append(f"{name}.{field_name}: missing Field description")
            has_default = field_info.default is not PydanticUndefined
            has_factory = field_info.default_factory is not None
            if not field_info.is_required() and not (has_default or has_factory):
                violations.append(
                    f"{name}.{field_name}: optional field has no default/default_factory"
                )

    manifest = load_manifest()
    previous_versions = (manifest or {}).get("tool_versions")
    if isinstance(previous_versions, dict):
        violations.extend(collect_version_bump_violations(previous_versions))

    return violations


def main(argv: list[str] | None = None) -> int:
    del argv  # no CLI flags today; kept for oracle-cpq dispatch parity
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
