"""Tool definition integrity verification (rug-pull protection)."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG

logger = logging.getLogger(__name__)

MANIFEST_PATH = Path(__file__).with_name("tool_manifest.json")


def canonicalize_tool_definitions() -> list[dict[str, Any]]:
    """Build canonical tool definition records for hashing."""
    records: list[dict[str, Any]] = []
    for name in sorted(TOOL_CATALOG):
        spec = TOOL_CATALOG[name]
        records.append(
            {
                "name": spec.name,
                "domain": spec.domain,
                "operation": spec.operation,
                "description": spec.description,
                "read_only": spec.read_only,
                "destructive": spec.destructive,
                "risk": spec.risk,
                "http_method": spec.http_method,
                "api_path": spec.api_path,
                "tags": sorted(spec.tags),
            }
        )
    return records


def compute_tool_manifest_hash() -> str:
    """Compute SHA-256 hash of canonical tool definitions."""
    canonical = canonicalize_tool_definitions()
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_expected_manifest_hash() -> str | None:
    """Load expected hash from committed manifest file."""
    if not MANIFEST_PATH.exists():
        return None
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
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
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return tool_hash
