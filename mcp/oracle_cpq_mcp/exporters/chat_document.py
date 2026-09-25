"""Build simple Word (.docx) documents from tabular chat export payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Literal

from oracle_cpq_mcp.exporters.branded_documents import (
    add_bullet_paragraph,
    add_heading_paragraph,
    add_normal_paragraph,
    add_title_paragraph,
    assert_not_template_path,
    last_template_status,
    open_word_document,
    template_dir,
)
from oracle_cpq_mcp.exporters.mermaid_render import (
    load_png_file,
    render_mermaid_to_png,
)
from oracle_cpq_mcp.exporters.records_excel import _display_value, resolve_columns

_TABLE_FONT_PT = 8
_HEADER_FONT_PT = 8.5
_MIN_COLUMN_INCHES = 0.7
_MAX_PORTRAIT_COLUMNS = 4
_MAX_TABLE_COLUMNS = 7
_LABEL_COLUMN_INCHES = 1.8
_WEIGHT_CLAMP_MIN = 4
_WEIGHT_CLAMP_MAX = 80
_NARROW_MARGINS_INCHES = 0.5

LayoutMode = Literal["table", "landscape_table", "blocks"]


@dataclass
class DocxBuildResult:
    """Word payload plus diagram embedding telemetry for the tool envelope."""

    payload: bytes
    diagrams_embedded: int = 0
    diagrams_skipped: list[dict[str, str]] = field(default_factory=list)


def _content_width_inches(section: Any) -> float:
    """Usable content width in inches for *section*."""
    from docx.shared import Inches

    page = float(section.page_width)
    left = float(section.left_margin)
    right = float(section.right_margin)
    usable = page - left - right
    return max(usable / float(Inches(1)), 1.0)


def _column_weights(cols: list[str], records: list[Any]) -> list[float]:
    """Weight each column from clamped max display length across header + rows."""
    weights: list[float] = []
    for col in cols:
        longest = len(str(col))
        for record in records:
            if not isinstance(record, dict):
                continue
            text = _display_value(record.get(col))
            longest = max(longest, len(text))
        weights.append(float(min(max(longest, _WEIGHT_CLAMP_MIN), _WEIGHT_CLAMP_MAX)))
    return weights


def _widths_from_weights(weights: list[float], total_inches: float) -> list[float]:
    total = sum(weights) or float(len(weights))
    return [total_inches * (w / total) for w in weights]


def _fit_column_widths(
    weights: list[float],
    total_inches: float,
    *,
    min_inches: float = _MIN_COLUMN_INCHES,
) -> list[float] | None:
    """Return widths that honor *min_inches*, or ``None`` if they cannot fit."""
    n = len(weights)
    if n == 0:
        return []
    if n * min_inches > total_inches + 1e-9:
        return None
    widths = _widths_from_weights(weights, total_inches)
    if min(widths) >= min_inches - 1e-9:
        return widths
    # Floor short columns; redistribute leftover across columns still above the floor.
    floored = [max(w, min_inches) for w in widths]
    overflow = sum(floored) - total_inches
    flexible = [i for i, w in enumerate(widths) if w > min_inches]
    if not flexible:
        return [total_inches / n] * n
    flex_total = sum(widths[i] for i in flexible)
    adjusted = list(floored)
    for index in flexible:
        share = overflow * (widths[index] / flex_total) if flex_total else overflow / len(
            flexible
        )
        adjusted[index] = max(min_inches, adjusted[index] - share)
    # Fix floating drift on the last flexible column.
    drift = total_inches - sum(adjusted)
    adjusted[flexible[-1]] += drift
    return adjusted


def _decide_layout(
    cols: list[str],
    records: list[Any],
    *,
    portrait_width: float,
    landscape_width: float,
) -> LayoutMode:
    """Choose portrait table, landscape table, or per-row blocks."""
    n = len(cols)
    if n == 0:
        return "table"
    if n > _MAX_TABLE_COLUMNS:
        return "blocks"
    weights = _column_weights(cols, records)
    if n <= _MAX_PORTRAIT_COLUMNS and _fit_column_widths(weights, portrait_width):
        return "table"
    if _fit_column_widths(weights, landscape_width):
        return "landscape_table"
    return "blocks"


def _set_cell_text(cell: Any, text: str) -> None:
    """Replace cell content with a single paragraph of *text*."""
    cell.text = ""
    paragraph = cell.paragraphs[0]
    paragraph.add_run(str(text))


def _apply_fixed_layout(table: Any, widths_inches: list[float]) -> None:
    """Force fixed table layout and set every cell/column width."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches

    table.autofit = False
    table.allow_autofit = False
    tbl = table._tbl  # noqa: SLF001
    tbl_pr = tbl.tblPr
    if tbl_pr is None:
        tbl_pr = OxmlElement("w:tblPr")
        tbl.insert(0, tbl_pr)
    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")

    total = Inches(sum(widths_inches))
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:type"), "dxa")
    tbl_w.set(qn("w:w"), str(int(total)))

    for row in table.rows:
        for index, cell in enumerate(row.cells):
            if index >= len(widths_inches):
                break
            cell.width = Inches(widths_inches[index])


def _style_header_row(table: Any) -> None:
    """Bold header cells and mark the row as repeating across pages."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt

    if not table.rows:
        return
    header = table.rows[0]
    tr = header._tr  # noqa: SLF001
    tr_pr = tr.get_or_add_trPr()
    if tr_pr.find(qn("w:tblHeader")) is None:
        tr_pr.append(OxmlElement("w:tblHeader"))
    for cell in header.cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(_HEADER_FONT_PT)


def _set_table_font(table: Any, *, body_pt: float = _TABLE_FONT_PT) -> None:
    """Apply body font size to all non-header rows (header sized separately)."""
    from docx.shared import Pt

    for row_index, row in enumerate(table.rows):
        if row_index == 0:
            continue
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(body_pt)


def _ensure_orientation(document: Any, *, landscape: bool) -> Any:
    """Start a new section with landscape or portrait orientation and narrow margins."""
    from docx.enum.section import WD_ORIENT
    from docx.shared import Inches

    # Force a section break so orientation only wraps this sheet's content.
    document.add_section()
    section = document.sections[-1]
    if landscape:
        if section.page_width < section.page_height:
            section.page_width, section.page_height = (
                section.page_height,
                section.page_width,
            )
        section.orientation = WD_ORIENT.LANDSCAPE
    else:
        if section.page_width > section.page_height:
            section.page_width, section.page_height = (
                section.page_height,
                section.page_width,
            )
        section.orientation = WD_ORIENT.PORTRAIT
    margin = Inches(_NARROW_MARGINS_INCHES)
    section.left_margin = margin
    section.right_margin = margin
    section.top_margin = margin
    section.bottom_margin = margin
    return section


def _pick_table_style(document: Any, table: Any) -> None:
    style_names = {s.name for s in document.styles}
    for candidate in ("Table Grid", "Light Grid Accent 1", "Table Normal"):
        if candidate in style_names:
            try:
                table.style = candidate
                break
            except Exception:
                continue


def _add_grid_table(
    document: Any,
    *,
    cols: list[str],
    records: list[Any],
    content_width: float,
) -> Any:
    """Add a fixed-layout grid table sized to *content_width* inches."""
    weights = _column_weights(cols, records)
    widths = _fit_column_widths(weights, content_width) or _widths_from_weights(
        weights, content_width
    )
    table = document.add_table(rows=1 + len(records), cols=len(cols))
    _pick_table_style(document, table)
    for col_index, col_name in enumerate(cols):
        _set_cell_text(table.rows[0].cells[col_index], str(col_name))
    for row_index, record in enumerate(records):
        cells = table.rows[row_index + 1].cells
        if not isinstance(record, dict):
            for col_index in range(len(cols)):
                _set_cell_text(cells[col_index], "")
            continue
        for col_index, col_name in enumerate(cols):
            _set_cell_text(cells[col_index], _display_value(record.get(col_name)))
    _apply_fixed_layout(table, widths)
    _style_header_row(table)
    _set_table_font(table)
    return table


def _add_record_blocks(
    document: Any,
    *,
    cols: list[str],
    records: list[Any],
    content_width: float,
) -> None:
    """Render each record as a heading plus a two-column label/value table."""
    label_w = min(_LABEL_COLUMN_INCHES, content_width * 0.35)
    value_w = max(content_width - label_w, _MIN_COLUMN_INCHES)
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            add_normal_paragraph(document, f"(row {index + 1}: empty)")
            continue
        title = _display_value(record.get(cols[0])) if cols else f"Row {index + 1}"
        if not title.strip():
            title = f"Row {index + 1}"
        add_heading_paragraph(document, title, level=3)
        table = document.add_table(rows=len(cols), cols=2)
        _pick_table_style(document, table)
        for row_index, col_name in enumerate(cols):
            _set_cell_text(table.rows[row_index].cells[0], str(col_name))
            _set_cell_text(
                table.rows[row_index].cells[1],
                _display_value(record.get(col_name)),
            )
        _apply_fixed_layout(table, [label_w, value_w])
        for row in table.rows:
            for run in row.cells[0].paragraphs[0].runs:
                run.bold = True
        _set_table_font(table)


def _landscape_page_width_inches(section: Any) -> float:
    """Estimate landscape usable width from the current portrait section."""
    from docx.shared import Inches

    # Swap page dimensions conceptually; keep current margins if already set.
    long_side = max(float(section.page_width), float(section.page_height))
    margin = float(Inches(_NARROW_MARGINS_INCHES))
    return max((long_side - 2 * margin) / float(Inches(1)), 1.0)


def _append_sheet_table(
    document: Any,
    *,
    sheet_title: str,
    cols: list[str],
    records: list[Any],
) -> None:
    """Choose layout and append one sheet's title + table/blocks."""
    if not cols:
        add_heading_paragraph(document, sheet_title, level=2)
        add_normal_paragraph(document, "(empty table)")
        return

    section = document.sections[-1]
    portrait_width = _content_width_inches(section)
    landscape_width = _landscape_page_width_inches(section)
    mode = _decide_layout(
        cols,
        records,
        portrait_width=portrait_width,
        landscape_width=landscape_width,
    )

    if mode == "landscape_table":
        section = _ensure_orientation(document, landscape=True)
        width = _content_width_inches(section)
        add_heading_paragraph(document, sheet_title, level=2)
        _add_grid_table(
            document, cols=cols, records=records, content_width=width
        )
        return

    if mode == "blocks":
        # Reset to portrait if a prior sheet left us in landscape.
        if section.orientation.name == "LANDSCAPE" or (
            float(section.page_width) > float(section.page_height)
        ):
            section = _ensure_orientation(document, landscape=False)
            width = _content_width_inches(section)
        else:
            width = portrait_width
        add_heading_paragraph(document, sheet_title, level=2)
        _add_record_blocks(
            document, cols=cols, records=records, content_width=width
        )
        return

    add_heading_paragraph(document, sheet_title, level=2)
    _add_grid_table(
        document, cols=cols, records=records, content_width=portrait_width
    )


def _resolve_diagram_png(spec: dict[str, Any]) -> tuple[bytes | None, str | None]:
    """Return PNG bytes or a skip reason for one diagram spec."""
    image_path_raw = spec.get("image_path")
    mermaid = spec.get("mermaid")
    mermaid_text = str(mermaid).strip() if mermaid is not None else ""

    if image_path_raw and str(image_path_raw).strip():
        path = Path(str(image_path_raw).strip()).expanduser()
        try:
            resolved = path.resolve()
            assert_not_template_path(resolved)
            # Extra guard: refuse reading *from* the template directory too.
            try:
                resolved.relative_to(template_dir().resolve())
            except ValueError:
                pass
            else:
                return None, "image_path must not be under .config/template/"
            if resolved.suffix.lower() != ".png":
                return None, "image_path must be a .png file"
            result = load_png_file(resolved)
            if result.ok and result.png_bytes is not None:
                return result.png_bytes, None
            return None, result.skipped_reason or "image_path load failed"
        except ValueError as exc:
            return None, str(exc)[:200]
        except OSError as exc:
            return None, f"image_path error: {type(exc).__name__}"

    if mermaid_text:
        result = render_mermaid_to_png(mermaid_text)
        if result.ok and result.png_bytes is not None:
            return result.png_bytes, None
        return None, result.skipped_reason or "mermaid render failed"

    return None, "diagram needs mermaid and/or image_path"


def _png_pixel_size(png_bytes: bytes) -> tuple[int, int]:
    """Return (width, height) from PNG IHDR, or (0, 0) if not a PNG."""
    if len(png_bytes) < 24 or png_bytes[:8] != b"\x89PNG\r\n\x1a\n":
        return 0, 0
    width = int.from_bytes(png_bytes[16:20], "big")
    height = int.from_bytes(png_bytes[20:24], "big")
    return width, height


# Tall Mermaid flowcharts otherwise fill ~20in of page height when width-fitted.
_MAX_DIAGRAM_HEIGHT_INCHES = 7.5


def _diagram_display_inches(
    pixel_width: int,
    pixel_height: int,
    *,
    max_width: float,
    max_height: float = _MAX_DIAGRAM_HEIGHT_INCHES,
) -> tuple[float, float]:
    """Fit a diagram into max_width × max_height while preserving aspect ratio."""
    if pixel_width <= 0 or pixel_height <= 0:
        return max_width, max_height
    aspect = pixel_height / float(pixel_width)
    width = max_width
    height = width * aspect
    if height > max_height:
        height = max_height
        width = height / aspect
    return width, height


def _add_diagram_picture(document: Any, png_bytes: bytes) -> None:
    """Insert a centered PNG fitted to content width, capped for tall charts."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches

    max_width = _content_width_inches(document.sections[-1])
    px_w, px_h = _png_pixel_size(png_bytes)
    width_in, height_in = _diagram_display_inches(
        px_w, px_h, max_width=max_width
    )
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    run.add_picture(
        BytesIO(png_bytes),
        width=Inches(width_in),
        height=Inches(height_in),
    )


def _append_notes(document: Any, notes: str | None) -> None:
    """Render lightweight structured notes (## / ### / - / *) into the document.

    Plain lines become Normal paragraphs. Blank lines are skipped (paragraph breaks).
    Full Markdown is intentionally unsupported.
    """
    if not notes or not str(notes).strip():
        return
    for raw_line in str(notes).strip().splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("### "):
            add_heading_paragraph(document, stripped[4:].strip(), level=3)
            continue
        if stripped.startswith("## "):
            add_heading_paragraph(document, stripped[3:].strip(), level=2)
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            add_bullet_paragraph(document, stripped[2:].strip())
            continue
        add_normal_paragraph(document, stripped)


def _append_diagrams(
    document: Any,
    diagrams: list[dict[str, Any]] | None,
) -> tuple[int, list[dict[str, str]]]:
    """Render diagrams after notes; return (embedded_count, skipped)."""
    if not diagrams:
        return 0, []
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    embedded = 0
    skipped: list[dict[str, str]] = []
    for index, spec in enumerate(diagrams):
        if not isinstance(spec, dict):
            skipped.append(
                {
                    "title": f"diagram[{index}]",
                    "reason": "diagram must be an object",
                }
            )
            continue
        title = str(spec.get("title") or f"Diagram {index + 1}").strip() or (
            f"Diagram {index + 1}"
        )
        add_heading_paragraph(document, title, level=2)
        png_bytes, reason = _resolve_diagram_png(spec)
        if png_bytes is None:
            mermaid = spec.get("mermaid")
            if mermaid and str(mermaid).strip():
                add_normal_paragraph(
                    document,
                    f"(Diagram not rendered: {reason or 'unknown'}. Mermaid source follows.)",
                )
                add_normal_paragraph(document, str(mermaid).strip())
            else:
                add_normal_paragraph(
                    document,
                    f"(Diagram not rendered: {reason or 'unknown'}.)",
                )
            skipped.append({"title": title, "reason": reason or "unknown"})
            continue
        try:
            _add_diagram_picture(document, png_bytes)
            embedded += 1
        except Exception as exc:  # noqa: BLE001 — keep export alive
            add_normal_paragraph(
                document,
                f"(Diagram embed failed: {type(exc).__name__}.)",
            )
            mermaid = spec.get("mermaid")
            if mermaid and str(mermaid).strip():
                add_normal_paragraph(document, str(mermaid).strip())
            skipped.append(
                {
                    "title": title,
                    "reason": f"embed failed: {type(exc).__name__}",
                }
            )
            continue
        caption = spec.get("caption")
        if caption and str(caption).strip():
            caption_para = add_normal_paragraph(document, str(caption).strip())
            caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return embedded, skipped


def build_docx_from_tables(
    *,
    title: str,
    sheets: list[dict[str, Any]],
    notes: str | None = None,
    diagrams: list[dict[str, Any]] | None = None,
) -> DocxBuildResult:
    """Create an in-memory .docx with a title, optional notes/diagrams, and tables.

    Clones ``Word Template.docx`` when resolved (env → ``.config/template`` →
    ``data/templates``). Requires optional dependency ``python-docx`` (install via
    ``pip install python-docx`` or ``pip install -e ".[docs]"``).

    Wide tables auto-switch to landscape or per-row label/value blocks so columns
    stay readable. Diagrams are placed after notes and before tables.

    Notes support lightweight markers: ``##`` / ``###`` headings, ``-`` / ``*``
    bullets; other lines are Normal paragraphs.
    """
    if not sheets:
        raise ValueError("sheets must be non-empty")

    try:
        document = open_word_document()
    except RuntimeError:
        raise

    add_title_paragraph(document, title.strip() or "Export")
    _append_notes(document, notes)

    diagrams_embedded, diagrams_skipped = _append_diagrams(document, diagrams)

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
        _append_sheet_table(
            document,
            sheet_title=sheet_title,
            cols=cols,
            records=records,
        )

    buffer = BytesIO()
    document.save(buffer)
    return DocxBuildResult(
        payload=buffer.getvalue(),
        diagrams_embedded=diagrams_embedded,
        diagrams_skipped=diagrams_skipped,
    )


def word_template_status_dict() -> dict[str, Any]:
    """Return the last Word template open status for export envelopes."""
    status = last_template_status("word")
    if hasattr(status, "as_dict"):
        return status.as_dict()
    return {"kind": "word", "applied": False, "reason": "unknown"}


__all__ = [
    "DocxBuildResult",
    "build_docx_from_tables",
    "word_template_status_dict",
]
