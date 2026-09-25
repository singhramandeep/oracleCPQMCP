"""Local Mermaid → PNG rendering for Word exports (no public Kroki/HTTP).

Uses ``mmdc`` from ``@mermaid-js/mermaid-cli`` when available on PATH.
Pre-rendered PNG paths are validated separately by the Word builder.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_MMDC_TIMEOUT_SECONDS = 60
MAX_PNG_BYTES = 8 * 1024 * 1024  # 8 MiB


@dataclass(frozen=True)
class MermaidRenderResult:
    """Outcome of a local Mermaid render attempt."""

    png_bytes: bytes | None
    skipped_reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.png_bytes is not None and len(self.png_bytes) > 0


def mmdc_available() -> bool:
    """Return True when ``mmdc`` (or ``mmdc.cmd`` on Windows) is on PATH."""
    return shutil.which("mmdc") is not None or shutil.which("mmdc.cmd") is not None


def _mmdc_command() -> str | None:
    return shutil.which("mmdc") or shutil.which("mmdc.cmd")


def render_mermaid_to_png(
    source: str,
    *,
    timeout_seconds: int = DEFAULT_MMDC_TIMEOUT_SECONDS,
) -> MermaidRenderResult:
    """Rasterize Mermaid source to PNG via local ``mmdc``.

    Does not call network renderers. On failure returns ``png_bytes=None`` and a
    short ``skipped_reason`` (no credentials or full command dumps).
    """
    text = (source or "").strip()
    if not text:
        return MermaidRenderResult(None, "empty mermaid source")

    cmd = _mmdc_command()
    if cmd is None:
        return MermaidRenderResult(
            None,
            "mmdc not on PATH (install @mermaid-js/mermaid-cli or pass image_path)",
        )

    try:
        with tempfile.TemporaryDirectory(prefix="cpq_mermaid_") as tmp:
            tmp_dir = Path(tmp)
            input_path = tmp_dir / "diagram.mmd"
            output_path = tmp_dir / "diagram.png"
            input_path.write_text(text, encoding="utf-8")
            completed = subprocess.run(
                [cmd, "-i", str(input_path), "-o", str(output_path), "-b", "white"],
                capture_output=True,
                timeout=max(5, int(timeout_seconds)),
                check=False,
                text=True,
            )
            if completed.returncode != 0:
                err = (completed.stderr or completed.stdout or "").strip()
                err = err.replace("\n", " ")[:200]
                reason = f"mmdc failed (exit {completed.returncode})"
                if err:
                    reason = f"{reason}: {err}"
                logger.info("Mermaid render skipped: %s", reason)
                return MermaidRenderResult(None, reason)
            if not output_path.is_file():
                return MermaidRenderResult(None, "mmdc produced no PNG file")
            payload = output_path.read_bytes()
            if not payload:
                return MermaidRenderResult(None, "mmdc produced empty PNG")
            if len(payload) > MAX_PNG_BYTES:
                return MermaidRenderResult(
                    None,
                    f"PNG exceeds max size ({MAX_PNG_BYTES} bytes)",
                )
            if payload[:8] != b"\x89PNG\r\n\x1a\n":
                return MermaidRenderResult(None, "mmdc output is not a PNG")
            return MermaidRenderResult(payload, None)
    except subprocess.TimeoutExpired:
        return MermaidRenderResult(None, f"mmdc timed out after {timeout_seconds}s")
    except OSError as exc:
        logger.info("Mermaid render OSError: %s", type(exc).__name__)
        return MermaidRenderResult(None, f"mmdc OS error: {type(exc).__name__}")


def load_png_file(path: Path) -> MermaidRenderResult:
    """Load and validate a PNG from disk (size + magic bytes)."""
    try:
        if not path.is_file():
            return MermaidRenderResult(None, f"image_path not found: {path.name}")
        payload = path.read_bytes()
    except OSError as exc:
        return MermaidRenderResult(None, f"image_path read error: {type(exc).__name__}")
    if not payload:
        return MermaidRenderResult(None, "image_path is empty")
    if len(payload) > MAX_PNG_BYTES:
        return MermaidRenderResult(
            None,
            f"image_path exceeds max size ({MAX_PNG_BYTES} bytes)",
        )
    if payload[:8] != b"\x89PNG\r\n\x1a\n":
        return MermaidRenderResult(None, "image_path is not a PNG")
    return MermaidRenderResult(payload, None)


__all__ = [
    "DEFAULT_MMDC_TIMEOUT_SECONDS",
    "MAX_PNG_BYTES",
    "MermaidRenderResult",
    "load_png_file",
    "mmdc_available",
    "render_mermaid_to_png",
]
