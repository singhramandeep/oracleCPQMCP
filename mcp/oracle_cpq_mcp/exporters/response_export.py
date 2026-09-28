"""Helpers for post-response Excel/Word exports under data/{profile}/{env}/exports/."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from oracle_cpq_mcp.core.config import CPQProfile
from oracle_cpq_mcp.core.local_data import profile_env_root, safe_segment
from oracle_cpq_mcp.exporters.branded_documents import assert_not_template_path

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


def coerce_sheet_records(
    rows: list[Any],
    columns: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Normalize sheet rows to dict records.

    Accepts the MCP/export convention of either:
    - list of dicts (already keyed by column), or
    - list of lists/tuples aligned with *columns*.

    Word and Excel writers only read dict rows; list-of-list payloads used to
    produce empty cells / ``(row N: empty)`` placeholders.
    """
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    col_names: list[str] | None = None
    if columns is not None:
        col_names = [str(c) for c in columns]

    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if isinstance(row, dict):
            records.append(row)
            continue
        if isinstance(row, (list, tuple)):
            if col_names is None:
                keys = [f"col_{i + 1}" for i in range(len(row))]
            else:
                keys = col_names
            record: dict[str, Any] = {}
            for col_index, key in enumerate(keys):
                record[key] = row[col_index] if col_index < len(row) else None
            records.append(record)
            continue
        raise ValueError(
            f"rows[{index}] must be an object or a list/tuple of cell values"
        )
    return records


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
        try:
            records = coerce_sheet_records(rows, columns if isinstance(columns, list) else None)
        except ValueError as exc:
            raise ValueError(f"sheets[{index}]: {exc}") from exc
        out: dict[str, Any] = {
            "name": name[:31] or f"Sheet{index + 1}",
            "rows": records,
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
    assert_not_template_path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    assert_not_template_path(path)
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
