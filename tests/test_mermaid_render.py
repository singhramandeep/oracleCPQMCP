"""Unit tests for local Mermaid PNG rendering (no Node/mmdc required)."""

from __future__ import annotations

from pathlib import Path

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

    class FakeProc:
        def __init__(self) -> None:
            self.pid = 4242
            self.returncode = 0
            self._out_path: Path | None = None

        def communicate(self, timeout: float | None = None) -> tuple[str, str]:
            assert self._out_path is not None
            self._out_path.write_bytes(_MINI_PNG)
            return "", ""

        def poll(self) -> int | None:
            return self.returncode

        def wait(self, timeout: float | None = None) -> int:
            return self.returncode

    fake_proc = FakeProc()

    def fake_popen(argv: list[str], **kwargs: object) -> FakeProc:
        # argv may be [cmd, -i, in, -o, out, ...] or [cmd.exe, /c, cmd, -i, ...]
        out_path = Path(argv[argv.index("-o") + 1])
        fake_proc._out_path = out_path
        return fake_proc

    monkeypatch.setattr(
        "oracle_cpq_mcp.exporters.mermaid_render._mmdc_command",
        lambda: str(fake_mmdc),
    )
    monkeypatch.setattr(
        "oracle_cpq_mcp.exporters.mermaid_render.subprocess.Popen",
        fake_popen,
    )
    result = render_mermaid_to_png("flowchart LR\n  A --> B")
    assert result.ok is True
    assert result.png_bytes == _MINI_PNG
    assert result.skipped_reason is None


def test_render_mermaid_timeout_kills_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import subprocess

    fake_mmdc = tmp_path / "mmdc"
    fake_mmdc.write_text("", encoding="utf-8")
    killed: list[int] = []

    class HangingProc:
        pid = 9991
        returncode: int | None = None
        stderr = None

        def communicate(self, timeout: float | None = None) -> tuple[str, str]:
            raise subprocess.TimeoutExpired(cmd="mmdc", timeout=timeout or 1)

        def poll(self) -> int | None:
            return self.returncode

        def wait(self, timeout: float | None = None) -> int:
            self.returncode = -9
            return -9

    monkeypatch.setattr(
        "oracle_cpq_mcp.exporters.mermaid_render._mmdc_command",
        lambda: str(fake_mmdc),
    )
    monkeypatch.setattr(
        "oracle_cpq_mcp.exporters.mermaid_render.subprocess.Popen",
        lambda *a, **k: HangingProc(),
    )
    monkeypatch.setattr(
        "oracle_cpq_mcp.exporters.mermaid_render._kill_process_tree",
        lambda pid: killed.append(pid),
    )
    result = render_mermaid_to_png(
        "flowchart LR\n  A --> B", timeout_seconds=2
    )
    assert result.ok is False
    assert result.skipped_reason is not None
    assert "timed out" in result.skipped_reason
    assert killed == [9991]


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
