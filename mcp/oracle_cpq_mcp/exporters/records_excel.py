"""Build simple Excel workbooks from lists of dict records."""

from __future__ import annotations

import io
from typing import Any

from openpyxl import Workbook


def _display_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        display = value.get("displayValue")
        if display is not None:
            return str(display)
        nested = value.get("value")
        return "" if nested is None else str(nested)
    if isinstance(value, (list, tuple)):
        return ", ".join(_display_value(v) for v in value)
    return str(value)


def resolve_columns(
    records: list[dict[str, Any]],
    columns: list[str] | None = None,
) -> list[str]:
    """Return explicit columns or the union of keys across *records* (stable order)."""
    if columns is not None:
        return [str(c) for c in columns]
    seen: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        for key in record:
            if key not in seen and key != "links":
                seen.append(str(key))
    return seen


def _append_records_sheet(
    workbook: Workbook,
    *,
    sheet_title: str,
    records: list[dict[str, Any]],
    columns: list[str] | None = None,
    replace_active: bool = False,
) -> None:
    title = (sheet_title or "Data")[:31] or "Data"
    if replace_active and workbook.active is not None and workbook.active.max_row == 1:
        sheet = workbook.active
        sheet.title = title
    else:
        sheet = workbook.create_sheet(title=title)
    cols = resolve_columns(records, columns)
    sheet.append(cols)
    for record in records:
        if not isinstance(record, dict):
            sheet.append([""] * len(cols))
            continue
        sheet.append([_display_value(record.get(col)) for col in cols])


def build_records_workbook(
    records: list[dict[str, Any]],
    *,
    sheet_title: str = "Data",
    columns: list[str] | None = None,
) -> bytes:
    """Create an in-memory .xlsx from homogeneous dict records.

    When *columns* is omitted, uses the union of keys across records (stable order
    from first occurrence).
    """
    workbook = Workbook()
    # Replace the default empty sheet.
    default = workbook.active
    assert default is not None
    default.title = (sheet_title or "Data")[:31] or "Data"
    cols = resolve_columns(records, columns)
    default.append(cols)
    for record in records:
        if not isinstance(record, dict):
            default.append([""] * len(cols))
            continue
        default.append([_display_value(record.get(col)) for col in cols])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def build_multi_sheet_workbook(
    sheets: list[dict[str, Any]],
) -> bytes:
    """Create an in-memory .xlsx with one worksheet per sheet dict.

    Each sheet dict accepts:
    - ``name`` / ``title``: worksheet title (truncated to 31 chars)
    - ``columns``: optional column order
    - ``rows`` / ``records``: list of row dicts
    """
    if not sheets:
        raise ValueError("sheets must be non-empty")

    workbook = Workbook()
    # Remove the blank default sheet after the first real sheet is written.
    first = True
    for index, spec in enumerate(sheets):
        if not isinstance(spec, dict):
            raise ValueError(f"sheets[{index}] must be an object")
        title = str(spec.get("name") or spec.get("title") or f"Sheet{index + 1}")
        records = spec.get("rows")
        if records is None:
            records = spec.get("records")
        if records is None:
            records = []
        if not isinstance(records, list):
            raise ValueError(f"sheets[{index}].rows must be a list")
        columns = spec.get("columns")
        if columns is not None and not isinstance(columns, list):
            raise ValueError(f"sheets[{index}].columns must be a list of strings")
        if first:
            sheet = workbook.active
            assert sheet is not None
            sheet.title = title[:31] or f"Sheet{index + 1}"
            cols = resolve_columns(records, columns)
            sheet.append(cols)
            for record in records:
                if not isinstance(record, dict):
                    sheet.append([""] * len(cols))
                    continue
                sheet.append([_display_value(record.get(col)) for col in cols])
            first = False
        else:
            _append_records_sheet(
                workbook,
                sheet_title=title,
                records=records,
                columns=columns,
            )
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
