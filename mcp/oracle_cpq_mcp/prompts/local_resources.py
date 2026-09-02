"""MCP resources for local ``data/`` cache (BML + snapshot index)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from oracle_cpq_mcp.core.config import CPQProfile
from oracle_cpq_mcp.core.local_data import list_snapshots, profile_env_root


def _safe_under(root: Path, relative: str) -> Path | None:
    """Resolve *relative* under *root*; reject path escape."""
    cleaned = (relative or "").replace("\\", "/").lstrip("/")
    if not cleaned or ".." in cleaned.split("/"):
        return None
    target = (root / cleaned).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None
    return target


def register_local_data_resources(mcp: Any, profile: CPQProfile) -> None:
    """Register ``cpq://local/...`` resources for the active profile/env."""

    @mcp.resource("cpq://local")
    def local_index() -> str:
        """JSON index of local snapshots and BML paths for the active profile."""
        root = profile_env_root(profile)
        bml_site = root / "bml" / "site"
        bml_zip_dir = root / "bml"
        snapshots = list_snapshots(profile)
        payload = {
            "profile": profile.customer_id,
            "environment": profile.environment,
            "root": str(root.resolve()),
            "snapshots": snapshots,
            "bml": {
                "site_dir": str(bml_site.resolve()) if bml_site.is_dir() else None,
                "site_exists": bml_site.is_dir(),
                "bml_dir": str(bml_zip_dir.resolve()) if bml_zip_dir.is_dir() else None,
            },
            "hint": (
                "Use search_local_bml for text search. Read specific files via "
                "cpq://local/bml/{relative_path} under site/ (e.g. site/commerce/...)."
            ),
        }
        return json.dumps(payload, indent=2)

    @mcp.resource("cpq://local/bml/{path}")
    def local_bml_file(path: str) -> str:
        """Return text of one file under data/.../bml/ (site/ or functions/)."""
        bml_root = profile_env_root(profile) / "bml"
        target = _safe_under(bml_root, path)
        if target is None:
            return json.dumps(
                {
                    "error": "invalid_path",
                    "path": path,
                    "hint": "Use a relative path under bml/ without '..'.",
                }
            )
        if not target.is_file():
            return json.dumps(
                {
                    "error": "not_found",
                    "path": path,
                    "resolved": str(target),
                    "hint": "Run start_bml_site_export or get_all_bml_code first.",
                }
            )
        try:
            text = target.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return json.dumps({"error": "read_failed", "message": str(exc)})
        # Cap huge files for MCP resource payloads
        max_chars = 200_000
        truncated = len(text) > max_chars
        return json.dumps(
            {
                "path": path,
                "absolute_path": str(target.resolve()),
                "truncated": truncated,
                "content": text[:max_chars],
            },
            indent=2,
        )
