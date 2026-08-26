"""Helpers for post-response Excel/Word exports under data/{profile}/{env}/exports/."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from oracle_cpq_mcp.core.config import CPQProfile
from oracle_cpq_mcp.core.local_data import profile_env_root, safe_segment

MAX_EXPORT_SHEETS = 20
MAX_EXPORT_ROWS = 10_000
_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")


def exports_dir(profile: CPQProfile) -> Path:
    """Return ``data/{profile}/{env}/exports`` (created by callers as needed)."""
    return profile_env_root(profile) / "exports"


def safe_export_stem(title: str, *, fallback: str = "export") -> str:
    cleaned = _SAFE_FILENAME.sub("_", (title or "").strip()).strip("._")
    return (cleaned or fallback)[:80]


def export_filename(title: str, *, extension: str) -> str:
    """Build ``{safe_title}_{UTC_timestamp}.{extension}``."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ext = extension.lstrip(".")
    return f"{safe_export_stem(title)}_{stamp}.{ext}"


def file_uri(path: Path) -> str:
    """Return a ``file:///`` URI for *path* (Windows-safe)."""
    resolved = path.resolve()
    # pathlib.as_uri() handles Windows drive letters.
    return resolved.as_uri()


def count_sheet_rows(sheets: list[dict[str, Any]]) -> int:
    total = 0
    for spec in sheets:
        if not isinstance(spec, dict):
            continue
        rows = spec.get("rows")
        if rows is None:
            rows = spec.get("records") or []
        if isinstance(rows, list):
            total += len(rows)
    return total


def validate_sheets_payload(sheets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize and enforce sheet/row caps for export tools."""
    if not sheets:
        raise ValueError("sheets must be a non-empty list")
    if len(sheets) > MAX_EXPORT_SHEETS:
        raise ValueError(f"sheets exceeds max of {MAX_EXPORT_SHEETS}")
    total_rows = count_sheet_rows(sheets)
    if total_rows > MAX_EXPORT_ROWS:
        raise ValueError(
            f"Total rows across sheets ({total_rows}) exceeds max of {MAX_EXPORT_ROWS}"
        )
    normalized: list[dict[str, Any]] = []
    for index, spec in enumerate(sheets):
        if not isinstance(spec, dict):
            raise ValueError(f"sheets[{index}] must be an object")
        name = str(spec.get("name") or spec.get("title") or f"Sheet{index + 1}").strip()
        rows = spec.get("rows")
        if rows is None:
            rows = spec.get("records")
        if rows is None:
            rows = []
        if not isinstance(rows, list):
            raise ValueError(f"sheets[{index}].rows must be a list")
        columns = spec.get("columns")
        if columns is not None:
            if not isinstance(columns, list) or not all(isinstance(c, str) for c in columns):
                raise ValueError(f"sheets[{index}].columns must be a list of strings")
        out: dict[str, Any] = {
            "name": name[:31] or f"Sheet{index + 1}",
            "rows": rows,
        }
        if columns is not None:
            out["columns"] = columns
        normalized.append(out)
    return normalized


def relative_export_path(profile: CPQProfile, filename: str) -> str:
    """Repo-relative POSIX-ish path string for chat display."""
    return (
        f"data/{safe_segment(profile.customer_id)}/"
        f"{safe_segment(profile.environment)}/exports/{filename}"
    )


def write_export_bytes(profile: CPQProfile, filename: str, payload: bytes) -> Path:
    """Write *payload* under the profile exports dir and return the absolute path."""
    directory = exports_dir(profile)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_bytes(payload)
    return path


__all__ = [
    "MAX_EXPORT_ROWS",
    "MAX_EXPORT_SHEETS",
    "count_sheet_rows",
    "export_filename",
    "exports_dir",
    "file_uri",
    "quote",
    "relative_export_path",
    "safe_export_stem",
    "validate_sheets_payload",
    "write_export_bytes",
]
