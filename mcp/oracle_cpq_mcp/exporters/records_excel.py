"""Build simple Excel workbooks from lists of dict records."""

from __future__ import annotations

import io
from typing import Any

from openpyxl import Workbook

from oracle_cpq_mcp.exporters.branded_documents import (
    apply_header_style,
    open_excel_workbook,
)


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


def _write_sheet_rows(
    sheet: Any,
    *,
    records: list[dict[str, Any]],
    columns: list[str] | None,
    workbook: Workbook,
) -> None:
    cols = resolve_columns(records, columns)
    for col_index, col_name in enumerate(cols, start=1):
        sheet.cell(1, col_index, col_name)
    apply_header_style(sheet, row=1, columns=len(cols), workbook=workbook)
    for row_offset, record in enumerate(records):
        row_index = row_offset + 2
        if not isinstance(record, dict):
            for col_index in range(1, len(cols) + 1):
                sheet.cell(row_index, col_index, "")
            continue
        for col_index, col_name in enumerate(cols, start=1):
            sheet.cell(row_index, col_index, _display_value(record.get(col_name)))


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
    _write_sheet_rows(sheet, records=records, columns=columns, workbook=workbook)


def build_records_workbook(
    records: list[dict[str, Any]],
    *,
    sheet_title: str = "Data",
    columns: list[str] | None = None,
) -> bytes:
    """Create an in-memory .xlsx from homogeneous dict records.

    Uses ``.config/template/Excel Template.xlsx`` when valid.
    When *columns* is omitted, uses the union of keys across records (stable order
    from first occurrence).
    """
    workbook = open_excel_workbook()
    default = workbook.active
    assert default is not None
    default.title = (sheet_title or "Data")[:31] or "Data"
    _write_sheet_rows(default, records=records, columns=columns, workbook=workbook)
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

    workbook = open_excel_workbook()
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
            _write_sheet_rows(sheet, records=records, columns=columns, workbook=workbook)
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
