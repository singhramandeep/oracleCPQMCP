"""Resolve and open branded Office templates from ``.config/template``.

Word / PowerPoint: copy the template to a temp file, open the copy, clear body
content only so headers/footers, logos, themes, and style definitions remain.
Excel: load workbook and capture header-row style from the sample cell.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from copy import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.worksheet import Worksheet

from oracle_cpq_mcp.core.config import config_dir, find_project_root

logger = logging.getLogger(__name__)

TemplateKind = Literal["word", "excel", "pptx"]
TemplateSource = Literal["env", "config", "working"]

TEMPLATE_FILENAMES: dict[TemplateKind, str] = {
    "word": "Word Template.docx",
    "excel": "Excel Template.xlsx",
    "pptx": "PowerPoint Template.pptx",
}

_TEMPLATE_ENV_KEYS: dict[TemplateKind, str] = {
    "word": "CPQ_WORD_TEMPLATE",
    "excel": "CPQ_EXCEL_TEMPLATE",
    "pptx": "CPQ_PPTX_TEMPLATE",
}

# Fallback header look when the Excel template has no styled sample row.
_DEFAULT_HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
_DEFAULT_HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
_DEFAULT_HEADER_ALIGNMENT = Alignment(
    horizontal="center", vertical="center", wrap_text=True
)
_DEFAULT_HEADER_BORDER = Border(
    left=Side(style="thin", color="B0B0B0"),
    right=Side(style="thin", color="B0B0B0"),
    top=Side(style="thin", color="B0B0B0"),
    bottom=Side(style="thin", color="B0B0B0"),
)

_WORD_TITLE_CANDIDATES = ("Title", "Heading 1")
_WORD_H1_CANDIDATES = ("Heading 1",)
_WORD_H2_CANDIDATES = ("Heading 2",)
_WORD_H3_CANDIDATES = ("Heading 3",)
_WORD_NORMAL_CANDIDATES = ("Normal",)
_WORD_LIST_BULLET_CANDIDATES = ("List Bullet", "List Paragraph")


@dataclass(frozen=True)
class TemplateStatus:
    """Result of the last template resolve/open attempt for a kind."""

    kind: TemplateKind
    applied: bool
    path: str | None = None
    reason: str | None = None
    source: TemplateSource | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "applied": self.applied,
            "path": self.path,
            "reason": self.reason,
            "source": self.source,
        }


_last_status: dict[TemplateKind, TemplateStatus] = {}


def template_dir() -> Path:
    """Return ``<config_dir>/template`` (honors ``CPQ_CONFIG_DIR``)."""
    return config_dir() / "template"


def working_template_dir() -> Path:
    """Writable template copy dir (``data/templates`` or ``CPQ_TEMPLATE_WORK_DIR``).

    Agents may write here; ``.config/template/`` remains read-only.
    """
    import os

    if env_dir := os.environ.get("CPQ_TEMPLATE_WORK_DIR"):
        return Path(env_dir).expanduser().resolve()
    return find_project_root() / "data" / "templates"


def last_template_status(kind: TemplateKind | None = None) -> TemplateStatus | dict[str, Any]:
    """Return the last open status for *kind*, or a map of all kinds if omitted."""
    if kind is not None:
        return _last_status.get(
            kind,
            TemplateStatus(kind=kind, applied=False, reason="not_attempted"),
        )
    return {k: last_template_status(k) for k in TEMPLATE_FILENAMES}  # type: ignore[return-value]


def _set_status(status: TemplateStatus) -> TemplateStatus:
    _last_status[status.kind] = status
    return status


def assert_not_template_path(path: Path) -> None:
    """Raise ``ValueError`` if *path* resolves under the branding template directory.

    Agents and MCP must treat ``.config/template/`` as read-only. Call this before
    any filesystem write so a mistaken destination under the template dir fails closed.
    """
    resolved = path.resolve()
    root = template_dir().resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return
    raise ValueError(
        f"Refusing to write under template directory ({root}): {resolved}"
    )


def _looks_like_office_package(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(2) == b"PK"
    except OSError:
        return False


def _validate_template_file(path: Path) -> str | None:
    """Return a reject reason, or ``None`` when *path* is a usable Office package."""
    if not path.is_file():
        return "missing"
    try:
        size = path.stat().st_size
    except OSError:
        return "unreadable"
    if size <= 0:
        return "empty"
    if not _looks_like_office_package(path):
        return "invalid_package"
    return None


def _env_template_path(kind: TemplateKind) -> Path | None:
    import os

    raw = os.environ.get(_TEMPLATE_ENV_KEYS[kind])
    if not raw or not str(raw).strip():
        return None
    return Path(str(raw).strip()).expanduser()


def resolve_template(kind: TemplateKind) -> Path | None:
    """Return the first valid template path (env → config → working dir).

    Missing, zero-byte, or non-ZIP files are skipped. Sets ``last_template_status``
    with ``source`` when a candidate is accepted, or the last reject ``reason``.
    """
    candidates: list[tuple[TemplateSource, Path]] = []
    env_path = _env_template_path(kind)
    if env_path is not None:
        candidates.append(("env", env_path))
    candidates.append(("config", template_dir() / TEMPLATE_FILENAMES[kind]))
    candidates.append(("working", working_template_dir() / TEMPLATE_FILENAMES[kind]))

    last_reason = "missing"
    last_path: str | None = None
    preferred_reason: str | None = None
    preferred_path: str | None = None
    for source, path in candidates:
        reason = _validate_template_file(path)
        if reason is None:
            _set_status(
                TemplateStatus(
                    kind=kind,
                    applied=False,
                    path=str(path.resolve()),
                    reason=None,
                    source=source,
                )
            )
            return path.resolve()
        last_reason = reason
        last_path = str(path)
        if reason != "missing" and preferred_reason is None:
            preferred_reason = reason
            preferred_path = str(path)
        if reason in ("empty", "invalid_package"):
            logger.warning(
                "Ignoring %s document template (%s): %s",
                source,
                reason,
                path,
            )

    _set_status(
        TemplateStatus(
            kind=kind,
            applied=False,
            path=preferred_path or last_path,
            reason=preferred_reason or last_reason,
            source=None,
        )
    )
    return None


def copy_template_to_working(kind: TemplateKind, source_path: Path) -> Path:
    """Copy *source_path* into ``working_template_dir()`` as the canonical filename.

    Never writes under ``.config/template/``. Raises ``ValueError`` if the source
    is not a valid Office package or the destination would land under the
    read-only template directory.
    """
    source = source_path.expanduser().resolve()
    reason = _validate_template_file(source)
    if reason is not None:
        raise ValueError(f"Source template is not usable ({reason}): {source}")

    dest_dir = working_template_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = (dest_dir / TEMPLATE_FILENAMES[kind]).resolve()
    assert_not_template_path(dest)
    shutil.copy2(source, dest)
    return dest


def _clone_template_to_temp(source: Path, *, suffix: str) -> Path:
    """Copy *source* to a temp path (caller owns cleanup). Never writes under template dir."""
    import os

    fd, name = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    dest = Path(name)
    assert_not_template_path(dest)
    shutil.copy2(source, dest)
    return dest


def open_word_document() -> Any:
    """Clone ``Word Template.docx`` when valid; otherwise a blank ``Document``.

    Requires ``python-docx``. Clears placeholder body content from the clone
    while preserving styles, headers/footers, and section properties.
    """
    try:
        from docx import Document  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "python-docx is not installed. Install with: pip install python-docx "
            'or pip install -e ".[docs]"'
        ) from exc

    path = resolve_template("word")
    if path is None:
        logger.warning(
            "Word template not applied — using blank Document "
            "(expected %s under %s or %s, or set CPQ_WORD_TEMPLATE)",
            TEMPLATE_FILENAMES["word"],
            template_dir(),
            working_template_dir(),
        )
        return Document()

    prior = last_template_status("word")
    prior_source = prior.source if isinstance(prior, TemplateStatus) else None

    tmp_path: Path | None = None
    try:
        tmp_path = _clone_template_to_temp(path, suffix=".docx")
        document = Document(str(tmp_path))
    except Exception:
        logger.exception(
            "Failed to open Word template %s; using blank document (template not applied)",
            path,
        )
        _set_status(
            TemplateStatus(
                kind="word",
                applied=False,
                path=str(path),
                reason="open_failed",
                source=prior_source,
            )
        )
        return Document()
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

    _clear_word_body(document)
    _set_status(
        TemplateStatus(
            kind="word",
            applied=True,
            path=str(path),
            reason=None,
            source=prior_source,
        )
    )
    return document


def _clear_word_body(document: Any) -> None:
    """Remove body children except ``sectPr`` so styles/headers remain."""
    body = document.element.body
    for child in list(body):
        tag = child.tag
        if isinstance(tag, str) and tag.endswith("}sectPr"):
            continue
        body.remove(child)


def _style_names(document: Any) -> set[str]:
    try:
        return {s.name for s in document.styles}
    except Exception:
        return set()


def pick_document_style(document: Any, candidates: tuple[str, ...]) -> str | None:
    """Return the first style name from *candidates* that exists on *document*."""
    names = _style_names(document)
    for name in candidates:
        if name in names:
            return name
    return None


def apply_paragraph_style(paragraph: Any, candidates: tuple[str, ...]) -> str | None:
    """Set *paragraph* style to the first available candidate; return the name used."""
    document = paragraph.part.document
    style_name = pick_document_style(document, candidates)
    if style_name is None:
        return None
    try:
        paragraph.style = style_name
    except Exception:
        logger.debug("Could not apply style %s", style_name, exc_info=True)
        return None
    return style_name


def add_styled_paragraph(
    document: Any,
    text: str,
    *,
    style_candidates: tuple[str, ...],
) -> Any:
    """Add a paragraph and apply the first matching template style."""
    paragraph = document.add_paragraph(text)
    apply_paragraph_style(paragraph, style_candidates)
    return paragraph


def add_title_paragraph(document: Any, text: str) -> Any:
    """Add a title using ``Title`` (fallback ``Heading 1``)."""
    return add_styled_paragraph(document, text, style_candidates=_WORD_TITLE_CANDIDATES)


def add_heading_paragraph(document: Any, text: str, *, level: int = 1) -> Any:
    """Add a heading using ``Heading N`` styles from the template when present."""
    if level <= 1:
        candidates = _WORD_H1_CANDIDATES
    elif level == 2:
        candidates = _WORD_H2_CANDIDATES
    else:
        candidates = _WORD_H3_CANDIDATES
    style_name = pick_document_style(document, candidates)
    if style_name is not None:
        return add_styled_paragraph(document, text, style_candidates=candidates)
    # Fallback to python-docx built-in heading helper.
    return document.add_heading(text, level=min(max(level, 1), 9))


def add_normal_paragraph(document: Any, text: str) -> Any:
    """Add body text using ``Normal`` when present."""
    return add_styled_paragraph(document, text, style_candidates=_WORD_NORMAL_CANDIDATES)


def add_bullet_paragraph(document: Any, text: str) -> Any:
    """Add a bullet item using ``List Bullet`` when present; else ``- `` + Normal."""
    style_name = pick_document_style(document, _WORD_LIST_BULLET_CANDIDATES)
    if style_name is not None:
        return add_styled_paragraph(
            document, text, style_candidates=_WORD_LIST_BULLET_CANDIDATES
        )
    return add_normal_paragraph(document, f"- {text}" if text else "-")


def open_pptx_presentation() -> Any:
    """Clone ``PowerPoint Template.pptx`` when valid; otherwise a blank ``Presentation``.

    Requires ``python-pptx``. Clears slides from the clone while preserving slide
    masters / theme when possible, then ensures at least one blank content slide.
    """
    try:
        from pptx import Presentation  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "python-pptx is not installed. Install with: pip install python-pptx "
            'or pip install -e ".[docs]"'
        ) from exc

    path = resolve_template("pptx")
    if path is None:
        logger.warning(
            "PowerPoint template not applied — using blank Presentation "
            "(expected %s under %s or %s, or set CPQ_PPTX_TEMPLATE)",
            TEMPLATE_FILENAMES["pptx"],
            template_dir(),
            working_template_dir(),
        )
        return Presentation()

    prior = last_template_status("pptx")
    prior_source = prior.source if isinstance(prior, TemplateStatus) else None

    tmp_path: Path | None = None
    try:
        tmp_path = _clone_template_to_temp(path, suffix=".pptx")
        presentation = Presentation(str(tmp_path))
    except Exception:
        logger.exception(
            "Failed to open PowerPoint template %s; using blank presentation "
            "(template not applied)",
            path,
        )
        _set_status(
            TemplateStatus(
                kind="pptx",
                applied=False,
                path=str(path),
                reason="open_failed",
                source=prior_source,
            )
        )
        return Presentation()
    finally:
        if tmp_path is not None:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass

    _clear_pptx_slides(presentation)
    _set_status(
        TemplateStatus(
            kind="pptx",
            applied=True,
            path=str(path),
            reason=None,
            source=prior_source,
        )
    )
    return presentation


def _clear_pptx_slides(presentation: Any) -> None:
    """Remove existing slides but keep slide master / layouts from the template."""
    try:
        from pptx.enum.shapes import PP_PLACEHOLDER  # noqa: F401
    except ImportError:
        pass

    slide_ids = list(presentation.slides._sldIdLst)  # noqa: SLF001 — pptx public pattern
    for sld_id in slide_ids:
        presentation.part.drop_rel(sld_id.rId)
        presentation.slides._sldIdLst.remove(sld_id)  # noqa: SLF001

    # Ensure one blank content slide for callers to fill.
    try:
        blank_layout = presentation.slide_layouts[6]
    except IndexError:
        blank_layout = presentation.slide_layouts[0]
    presentation.slides.add_slide(blank_layout)


def open_excel_workbook() -> Workbook:
    """Open ``Excel Template.xlsx`` when valid; otherwise a blank ``Workbook``.

    Clears cells on the active sheet so exporters can reuse sheet/theme styles.
    Captures a header style sample from row 1 (if present) onto
    ``workbook.cpq_header_style`` for ``apply_header_style``.
    """
    path = resolve_template("excel")
    if path is None:
        logger.warning(
            "Excel template not applied — using blank Workbook "
            "(expected %s under %s or %s, or set CPQ_EXCEL_TEMPLATE)",
            TEMPLATE_FILENAMES["excel"],
            template_dir(),
            working_template_dir(),
        )
        workbook = Workbook()
        workbook.cpq_header_style = _default_header_style()  # type: ignore[attr-defined]
        return workbook

    prior = last_template_status("excel")
    prior_source = prior.source if isinstance(prior, TemplateStatus) else None

    try:
        workbook = load_workbook(str(path))
    except Exception:
        logger.exception(
            "Failed to open Excel template %s; using blank workbook (template not applied)",
            path,
        )
        _set_status(
            TemplateStatus(
                kind="excel",
                applied=False,
                path=str(path),
                reason="open_failed",
                source=prior_source,
            )
        )
        workbook = Workbook()
        workbook.cpq_header_style = _default_header_style()  # type: ignore[attr-defined]
        return workbook

    header_style = _extract_header_style(workbook)
    workbook.cpq_header_style = header_style  # type: ignore[attr-defined]
    _clear_excel_sheets(workbook)
    _set_status(
        TemplateStatus(
            kind="excel",
            applied=True,
            path=str(path),
            reason=None,
            source=prior_source,
        )
    )
    return workbook


def _default_header_style() -> dict[str, Any]:
    return {
        "font": copy(_DEFAULT_HEADER_FONT),
        "fill": copy(_DEFAULT_HEADER_FILL),
        "alignment": copy(_DEFAULT_HEADER_ALIGNMENT),
        "border": copy(_DEFAULT_HEADER_BORDER),
    }


def _extract_header_style(workbook: Workbook) -> dict[str, Any]:
    """Prefer styled sample from active sheet row 1; else defaults."""
    sheet = workbook.active
    if sheet is None:
        return _default_header_style()
    sample = sheet.cell(1, 1)
    has_custom = bool(
        sample.font
        and (
            sample.font.bold
            or (
                sample.fill is not None
                and sample.fill.patternType
                and sample.fill.patternType != "none"
            )
        )
    )
    if not has_custom:
        return _default_header_style()
    return {
        "font": copy(sample.font),
        "fill": copy(sample.fill),
        "alignment": copy(sample.alignment),
        "border": copy(sample.border),
    }


def _clear_excel_sheets(workbook: Workbook) -> None:
    """Remove all rows so ``append`` / row-1 writes start on a clean sheet."""
    for sheet in workbook.worksheets:
        max_row = sheet.max_row or 0
        if max_row >= 1:
            sheet.delete_rows(1, max_row)


def apply_header_style(
    sheet: Worksheet,
    *,
    row: int = 1,
    columns: int,
    workbook: Workbook | None = None,
) -> None:
    """Apply template (or default) header styling to ``sheet`` row ``row``."""
    style = None
    if workbook is not None:
        style = getattr(workbook, "cpq_header_style", None)
    if not isinstance(style, dict):
        style = _default_header_style()
    for col_index in range(1, max(columns, 0) + 1):
        cell = sheet.cell(row, col_index)
        if "font" in style and style["font"] is not None:
            cell.font = copy(style["font"])
        if "fill" in style and style["fill"] is not None:
            cell.fill = copy(style["fill"])
        if "alignment" in style and style["alignment"] is not None:
            cell.alignment = copy(style["alignment"])
        if "border" in style and style["border"] is not None:
            cell.border = copy(style["border"])


__all__ = [
    "TEMPLATE_FILENAMES",
    "TemplateSource",
    "TemplateStatus",
    "add_bullet_paragraph",
    "add_heading_paragraph",
    "add_normal_paragraph",
    "add_styled_paragraph",
    "add_title_paragraph",
    "apply_header_style",
    "apply_paragraph_style",
    "assert_not_template_path",
    "copy_template_to_working",
    "last_template_status",
    "open_excel_workbook",
    "open_pptx_presentation",
    "open_word_document",
    "pick_document_style",
    "resolve_template",
    "template_dir",
    "working_template_dir",
]
