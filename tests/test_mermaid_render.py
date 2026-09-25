"""Unit tests for local Mermaid PNG rendering (no Node/mmdc required)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from oracle_cpq_mcp.exporters.mermaid_render import (
    MermaidRenderResult,
    load_png_file,
    mmdc_available,
    render_mermaid_to_png,
)

_MINI_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_render_mermaid_empty_source() -> None:
    result = render_mermaid_to_png("   ")
    assert result.ok is False
    assert result.skipped_reason == "empty mermaid source"


def test_render_mermaid_without_mmdc(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "oracle_cpq_mcp.exporters.mermaid_render._mmdc_command",
        lambda: None,
    )
    result = render_mermaid_to_png("flowchart LR\n  A --> B")
    assert result.png_bytes is None
    assert result.skipped_reason is not None
    assert "mmdc not on PATH" in result.skipped_reason


def test_render_mermaid_success_mocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_mmdc = tmp_path / "mmdc.cmd"
    fake_mmdc.write_text("", encoding="utf-8")

    def fake_run(cmd: list[str], **kwargs: object) -> MagicMock:
        # mmdc -i in -o out -b white
        out_path = Path(cmd[cmd.index("-o") + 1])
        out_path.write_bytes(_MINI_PNG)
        completed = MagicMock()
        completed.returncode = 0
        completed.stderr = ""
        completed.stdout = ""
        return completed

    monkeypatch.setattr(
        "oracle_cpq_mcp.exporters.mermaid_render._mmdc_command",
        lambda: str(fake_mmdc),
    )
    monkeypatch.setattr(
        "oracle_cpq_mcp.exporters.mermaid_render.subprocess.run",
        fake_run,
    )
    result = render_mermaid_to_png("flowchart LR\n  A --> B")
    assert result.ok is True
    assert result.png_bytes == _MINI_PNG
    assert result.skipped_reason is None


def test_load_png_file_ok(tmp_path: Path) -> None:
    path = tmp_path / "x.png"
    path.write_bytes(_MINI_PNG)
    result = load_png_file(path)
    assert result.ok is True
    assert result.png_bytes == _MINI_PNG


def test_load_png_file_rejects_non_png(tmp_path: Path) -> None:
    path = tmp_path / "x.png"
    path.write_bytes(b"not-a-png")
    result = load_png_file(path)
    assert result.ok is False
    assert result.skipped_reason == "image_path is not a PNG"


def test_mmdc_available_is_bool() -> None:
    assert isinstance(mmdc_available(), bool)


def test_mermaid_render_result_ok_flag() -> None:
    assert MermaidRenderResult(_MINI_PNG).ok is True
    assert MermaidRenderResult(None, "nope").ok is False
    assert MermaidRenderResult(b"", "empty").ok is False
