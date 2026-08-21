"""Tool definition integrity verification (rug-pull protection)."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Any

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG

logger = logging.getLogger(__name__)

MANIFEST_PATH = Path(__file__).with_name("tool_manifest.json")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _icon_records(spec: Any) -> list[dict[str, Any]]:
    return [
        {
            "src": icon.src,
            "mimeType": icon.mime_type,
            "sizes": list(icon.sizes) if icon.sizes else None,
        }
        for icon in spec.icons
    ]


def tool_identity_record(spec: Any, *, include_version: bool) -> dict[str, Any]:
    """Canonical record used for hashing a single tool definition."""
    record: dict[str, Any] = {
        "name": spec.name,
        "title": spec.title,
        "domain": spec.domain,
        "operation": spec.operation,
        "description": spec.description,
        "read_only": spec.read_only,
        "destructive": spec.destructive,
        "risk": spec.risk,
        "http_method": spec.http_method,
        "api_path": spec.api_path,
        "tags": sorted(spec.tags),
        "icons": _icon_records(spec),
    }
    if include_version:
        record["version"] = spec.version
    return record


def tool_definition_sha256(spec: Any, *, include_version: bool = False) -> str:
    """SHA-256 of one tool's canonical identity (version excluded by default)."""
    payload = json.dumps(
        tool_identity_record(spec, include_version=include_version),
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonicalize_tool_definitions() -> list[dict[str, Any]]:
    """Build canonical tool definition records for hashing."""
    records: list[dict[str, Any]] = []
    for name in sorted(TOOL_CATALOG):
        records.append(tool_identity_record(TOOL_CATALOG[name], include_version=True))
    return records


def compute_tool_manifest_hash() -> str:
    """Compute SHA-256 hash of canonical tool definitions."""
    canonical = canonicalize_tool_definitions()
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_tool_versions_map() -> dict[str, dict[str, str]]:
    """Per-tool version + identity hash (hash excludes version for bump detection)."""
    return {
        name: {
            "version": spec.version,
            "definition_sha256": tool_definition_sha256(spec, include_version=False),
        }
        for name, spec in sorted(TOOL_CATALOG.items())
    }


def load_manifest() -> dict[str, Any] | None:
    """Load committed tool_manifest.json if present."""
    if not MANIFEST_PATH.exists():
        return None
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def load_expected_manifest_hash() -> str | None:
    """Load expected hash from committed manifest file."""
    data = load_manifest()
    if data is None:
        return None
    return data.get("tool_definitions_sha256")


def verify_schema_integrity(*, enabled: bool) -> None:
    """Fail closed when schema integrity is enabled and hash mismatches."""
    if not enabled:
        logger.info("Schema integrity check disabled (CPQ_SCHEMA_INTEGRITY=0)")
        return

    current = compute_tool_manifest_hash()
    expected = load_expected_manifest_hash()
    if expected is None:
        logger.warning(
            "No tool_manifest.json found; writing current hash for reference: %s",
            current,
        )
        return

    if current != expected:
        raise RuntimeError(
            f"Tool definition hash mismatch. Expected {expected}, got {current}. "
            "Update tool_manifest.json after intentional tool changes."
        )
    logger.info("Tool schema integrity verified (sha256=%s...)", current[:12])


def write_manifest_file() -> str:
    """Write current tool manifest hash (utility for maintenance)."""
    tool_hash = compute_tool_manifest_hash()
    manifest = {
        "tool_definitions_sha256": tool_hash,
        "tool_count": len(TOOL_CATALOG),
        "tools": [r["name"] for r in canonicalize_tool_definitions()],
        "tool_versions": build_tool_versions_map(),
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return tool_hash


def collect_version_bump_violations(
    previous_versions: dict[str, Any] | None,
) -> list[str]:
    """Require a version bump when a tool's identity hash changed."""
    violations: list[str] = []
    if not previous_versions:
        return violations
    for name, spec in sorted(TOOL_CATALOG.items()):
        prev = previous_versions.get(name)
        if not isinstance(prev, dict):
            continue
        prev_hash = prev.get("definition_sha256")
        prev_version = prev.get("version")
        if not prev_hash or not prev_version:
            continue
        current_hash = tool_definition_sha256(spec, include_version=False)
        if current_hash != prev_hash and spec.version == prev_version:
            violations.append(
                f"{name}: definition changed but version is still {spec.version!r}; "
                f"bump ToolSpec.version (was identity sha {prev_hash[:12]}...)"
            )
    return violations
