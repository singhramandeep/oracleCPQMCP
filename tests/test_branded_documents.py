"""Tests for branded Office template resolution and exporters."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill

from oracle_cpq_mcp.exporters import branded_documents as bd
from oracle_cpq_mcp.exporters.chat_document import build_docx_from_tables
from oracle_cpq_mcp.exporters.records_excel import build_multi_sheet_workbook

try:
    from docx import Document

    HAS_DOCX = True
except ImportError:  # pragma: no cover
    HAS_DOCX = False

try:
    from pptx import Presentation

    HAS_PPTX = True
except ImportError:  # pragma: no cover
    HAS_PPTX = False


def _config_with_template_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    cfg = tmp_path / ".config"
    tmpl = cfg / "template"
    tmpl.mkdir(parents=True)
    work = tmp_path / "data" / "templates"
    work.mkdir(parents=True)
    monkeypatch.setenv("CPQ_CONFIG_DIR", str(cfg))
    monkeypatch.setenv("CPQ_TEMPLATE_WORK_DIR", str(work))
    monkeypatch.delenv("CPQ_WORD_TEMPLATE", raising=False)
    monkeypatch.delenv("CPQ_EXCEL_TEMPLATE", raising=False)
    monkeypatch.delenv("CPQ_PPTX_TEMPLATE", raising=False)
    return tmpl


def test_resolve_template_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _config_with_template_dir(tmp_path, monkeypatch)
    assert bd.resolve_template("word") is None
    status = bd.last_template_status("word")
    assert status.applied is False
    assert status.reason == "missing"
    assert bd.resolve_template("excel") is None
    assert bd.resolve_template("pptx") is None


def test_resolve_template_rejects_empty_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    empty = tmpl / "Word Template.docx"
    empty.write_bytes(b"")
    assert bd.resolve_template("word") is None
    status = bd.last_template_status("word")
    assert status.applied is False
    assert status.reason == "empty"


def test_resolve_template_rejects_non_zip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    bad = tmpl / "Excel Template.xlsx"
    bad.write_text("not-a-zip", encoding="utf-8")
    assert bd.resolve_template("excel") is None
    assert bd.last_template_status("excel").reason == "invalid_package"


def test_open_excel_workbook_from_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    source = Workbook()
    cell = source.active["A1"]
    cell.value = "Header"
    cell.font = Font(bold=True, color="FFFFFF", name="Calibri", size=11)
    cell.fill = PatternFill("solid", fgColor="1F4E79")
    path = tmpl / "Excel Template.xlsx"
    source.save(path)

    workbook = bd.open_excel_workbook()
    assert workbook.active is not None
    assert workbook.active["A1"].value is None
    assert getattr(workbook, "cpq_header_style", None) is not None
    assert workbook.cpq_header_style["font"].bold is True
    assert bd.last_template_status("excel").applied is True


def test_open_excel_workbook_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config_with_template_dir(tmp_path, monkeypatch)
    workbook = bd.open_excel_workbook()
    assert workbook.active is not None
    assert getattr(workbook, "cpq_header_style", None) is not None
    assert bd.last_template_status("excel").applied is False


def test_build_multi_sheet_uses_template_header_style(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    source = Workbook()
    cell = source.active["A1"]
    cell.value = "Header"
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill("solid", fgColor="1F4E79")
    source.save(tmpl / "Excel Template.xlsx")

    payload = build_multi_sheet_workbook(
        [
            {
                "name": "Alpha",
                "columns": ["id", "label"],
                "rows": [{"id": 1, "label": "one"}],
            }
        ]
    )
    workbook = load_workbook(BytesIO(payload))
    header = workbook["Alpha"]["A1"]
    assert header.value == "id"
    assert header.font.bold is True
    assert workbook["Alpha"]["A2"].value == "1"


@pytest.mark.skipif(not HAS_DOCX, reason="python-docx not installed")
def test_open_word_document_from_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    seed = Document()
    seed.add_paragraph("PLACEHOLDER_TO_CLEAR")
    seed.save(str(tmpl / "Word Template.docx"))

    document = bd.open_word_document()
    texts = [p.text for p in document.paragraphs]
    assert "PLACEHOLDER_TO_CLEAR" not in texts
    assert bd.last_template_status("word").applied is True


@pytest.mark.skipif(not HAS_DOCX, reason="python-docx not installed")
def test_open_word_preserves_section_header(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    seed = Document()
    header = seed.sections[0].header
    header.paragraphs[0].text = "BRAND_HEADER_MARK"
    seed.add_paragraph("BODY_PLACEHOLDER")
    seed.save(str(tmpl / "Word Template.docx"))

    document = bd.open_word_document()
    body_texts = [p.text for p in document.paragraphs]
    assert "BODY_PLACEHOLDER" not in body_texts
    header_texts = [p.text for p in document.sections[0].header.paragraphs]
    assert "BRAND_HEADER_MARK" in header_texts

    payload = build_docx_from_tables(
        title="Export Title",
        sheets=[{"name": "SheetA", "columns": ["col"], "rows": [{"col": "v"}]}],
        notes="Body note",
    ).payload
    filled = Document(BytesIO(payload))
    filled_header = [p.text for p in filled.sections[0].header.paragraphs]
    assert "BRAND_HEADER_MARK" in filled_header


@pytest.mark.skipif(not HAS_DOCX, reason="python-docx not installed")
def test_build_docx_applies_title_heading_normal_styles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    seed = Document()
    seed.save(str(tmpl / "Word Template.docx"))

    payload = build_docx_from_tables(
        title="Branded Title",
        sheets=[
            {
                "name": "Section One",
                "columns": ["a"],
                "rows": [{"a": "x"}],
            }
        ],
        notes="Note line",
    ).payload
    document = Document(BytesIO(payload))
    by_text = {p.text: p for p in document.paragraphs}
    assert by_text["Branded Title"].style.name in ("Title", "Heading 1")
    assert by_text["Section One"].style.name == "Heading 2"
    assert by_text["Note line"].style.name == "Normal"


@pytest.mark.skipif(not HAS_DOCX, reason="python-docx not installed")
def test_open_word_empty_template_falls_back_blank(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    (tmpl / "Word Template.docx").write_bytes(b"")

    document = bd.open_word_document()
    assert document is not None
    assert bd.last_template_status("word").applied is False
    assert bd.last_template_status("word").reason == "empty"

    payload = build_docx_from_tables(
        title="Fallback",
        sheets=[{"name": "T", "columns": ["a"], "rows": [{"a": "1"}]}],
    ).payload
    assert payload[:2] == b"PK"


@pytest.mark.skipif(not HAS_DOCX, reason="python-docx not installed")
def test_build_docx_from_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    seed = Document()
    seed.add_paragraph("PLACEHOLDER")
    seed.save(str(tmpl / "Word Template.docx"))

    payload = build_docx_from_tables(
        title="Branded",
        sheets=[
            {
                "name": "T1",
                "columns": ["a"],
                "rows": [{"a": "x"}],
            }
        ],
        notes="Note line",
    ).payload
    assert payload[:2] == b"PK"
    document = Document(BytesIO(payload))
    texts = [p.text for p in document.paragraphs]
    assert "PLACEHOLDER" not in texts
    assert "Branded" in texts
    assert "Note line" in texts
    assert len(document.tables) == 1


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_open_pptx_presentation_from_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    seed = Presentation()
    # Default presentation already has one slide; save as template.
    seed.save(str(tmpl / "PowerPoint Template.pptx"))

    presentation = bd.open_pptx_presentation()
    assert presentation is not None
    assert len(presentation.slides) >= 1
    assert bd.last_template_status("pptx").applied is True


@pytest.mark.skipif(not HAS_PPTX, reason="python-pptx not installed")
def test_open_pptx_missing_falls_back_blank(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config_with_template_dir(tmp_path, monkeypatch)
    presentation = bd.open_pptx_presentation()
    assert presentation is not None
    assert bd.last_template_status("pptx").applied is False
    assert bd.last_template_status("pptx").reason == "missing"


def test_assert_not_template_path_rejects_under_template(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="Refusing to write under template directory"):
        bd.assert_not_template_path(tmpl / "Word Template.docx")


def test_assert_not_template_path_allows_exports_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config_with_template_dir(tmp_path, monkeypatch)
    exports = tmp_path / "data" / "customer" / "dev" / "exports"
    exports.mkdir(parents=True)
    bd.assert_not_template_path(exports / "report.xlsx")


def test_resolve_template_env_wins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    config_doc = tmpl / "Word Template.docx"
    config_doc.write_bytes(b"PK\x03\x04" + b"\x00" * 20)
    env_doc = tmp_path / "custom.docx"
    env_doc.write_bytes(b"PK\x03\x04" + b"\x00" * 40)
    monkeypatch.setenv("CPQ_WORD_TEMPLATE", str(env_doc))

    resolved = bd.resolve_template("word")
    assert resolved is not None
    assert resolved == env_doc.resolve()
    status = bd.last_template_status("word")
    assert status.source == "env"
    assert status.reason is None


def test_resolve_template_config_before_working(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    config_doc = tmpl / "Word Template.docx"
    config_doc.write_bytes(b"PK\x03\x04" + b"config")
    work = tmp_path / "data" / "templates"
    (work / "Word Template.docx").write_bytes(b"PK\x03\x04" + b"working")

    resolved = bd.resolve_template("word")
    assert resolved == config_doc.resolve()
    assert bd.last_template_status("word").source == "config"


def test_resolve_template_working_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _config_with_template_dir(tmp_path, monkeypatch)
    work_doc = tmp_path / "data" / "templates" / "Word Template.docx"
    work_doc.write_bytes(b"PK\x03\x04" + b"working-only")

    resolved = bd.resolve_template("word")
    assert resolved == work_doc.resolve()
    assert bd.last_template_status("word").source == "working"


def test_resolve_template_skips_empty_env_uses_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    empty_env = tmp_path / "empty.docx"
    empty_env.write_bytes(b"")
    monkeypatch.setenv("CPQ_WORD_TEMPLATE", str(empty_env))
    config_doc = tmpl / "Word Template.docx"
    config_doc.write_bytes(b"PK\x03\x04" + b"ok")

    resolved = bd.resolve_template("word")
    assert resolved == config_doc.resolve()
    assert bd.last_template_status("word").source == "config"


def test_copy_template_to_working(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    source = tmpl / "New Microsoft Word Document.docx"
    source.write_bytes(b"PK\x03\x04" + b"branded")

    dest = bd.copy_template_to_working("word", source)
    work = tmp_path / "data" / "templates"
    assert dest == (work / "Word Template.docx").resolve()
    assert dest.read_bytes().startswith(b"PK")
    assert dest.is_file()


def test_copy_template_to_working_refuses_template_dir_dest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmpl = _config_with_template_dir(tmp_path, monkeypatch)
    source = tmp_path / "ok.docx"
    source.write_bytes(b"PK\x03\x04" + b"ok")
    monkeypatch.setenv("CPQ_TEMPLATE_WORK_DIR", str(tmpl))

    with pytest.raises(ValueError, match="Refusing to write under template directory"):
        bd.copy_template_to_working("word", source)
