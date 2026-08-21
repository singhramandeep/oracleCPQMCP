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
    if columns is None:
        seen: list[str] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            for key in record:
                if key not in seen and key != "links":
                    seen.append(str(key))
        columns = seen
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_title[:31] or "Data"
    sheet.append(columns)
    for record in records:
        if not isinstance(record, dict):
            sheet.append([""] * len(columns))
            continue
        sheet.append([_display_value(record.get(col)) for col in columns])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
