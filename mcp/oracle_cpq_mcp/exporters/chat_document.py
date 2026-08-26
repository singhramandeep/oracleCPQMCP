"""Build simple Word (.docx) documents from tabular chat export payloads."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from oracle_cpq_mcp.exporters.records_excel import _display_value, resolve_columns


def build_docx_from_tables(
    *,
    title: str,
    sheets: list[dict[str, Any]],
    notes: str | None = None,
) -> bytes:
    """Create an in-memory .docx with a title, optional notes, and one table per sheet.

    Requires optional dependency ``python-docx`` (install via ``pip install python-docx``
    or ``pip install -e ".[docs]"``).
    """
    try:
        from docx import Document  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - exercised via tool error path
        raise RuntimeError(
            "python-docx is not installed. Install with: pip install python-docx "
            'or pip install -e ".[docs]"'
        ) from exc

    if not sheets:
        raise ValueError("sheets must be non-empty")

    document = Document()
    document.add_heading(title.strip() or "Export", level=1)
    if notes and str(notes).strip():
        for paragraph in str(notes).strip().splitlines() or [""]:
            document.add_paragraph(paragraph)

    for index, spec in enumerate(sheets):
        if not isinstance(spec, dict):
            raise ValueError(f"sheets[{index}] must be an object")
        sheet_title = str(spec.get("name") or spec.get("title") or f"Table {index + 1}")
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
        cols = resolve_columns(records, columns)

        document.add_heading(sheet_title, level=2)
        if not cols:
            document.add_paragraph("(empty table)")
            continue

        table = document.add_table(rows=1 + len(records), cols=len(cols))
        table.style = "Table Grid"
        header_cells = table.rows[0].cells
        for col_index, col_name in enumerate(cols):
            header_cells[col_index].text = str(col_name)
        for row_index, record in enumerate(records):
            cells = table.rows[row_index + 1].cells
            if not isinstance(record, dict):
                for col_index in range(len(cols)):
                    cells[col_index].text = ""
                continue
            for col_index, col_name in enumerate(cols):
                cells[col_index].text = _display_value(record.get(col_name))

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()
