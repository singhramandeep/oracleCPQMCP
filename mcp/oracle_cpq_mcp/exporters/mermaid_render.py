"""Local Mermaid → PNG rendering for Word exports (no public Kroki/HTTP).

Uses ``mmdc`` from ``@mermaid-js/mermaid-cli`` when available on PATH.
Pre-rendered PNG paths are validated separately by the Word builder.

On Windows, ``mmdc.cmd`` spawns Node → Puppeteer/Chromium. Timeouts must
kill the **process tree** (``taskkill /T``) or orphans keep blocking the MCP
stdio server until the host raises -32001 / Connection closed.
"""

from __future__ import annotations

import logging
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_MMDC_TIMEOUT_SECONDS = 8
DEFAULT_MMDC_TOTAL_BUDGET_SECONDS = 12
MIN_MMDC_REMAINING_SECONDS = 2
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


def _mmdc_argv(cmd: str, input_path: Path, output_path: Path) -> list[str]:
    """Build argv for mmdc; wrap Windows ``.cmd`` shims via ``cmd.exe /c``."""
    args = ["-i", str(input_path), "-o", str(output_path), "-b", "white"]
    if sys.platform == "win32" and cmd.lower().endswith((".cmd", ".bat")):
        return ["cmd.exe", "/c", cmd, *args]
    return [cmd, *args]


def _kill_process_tree(pid: int) -> None:
    """Force-kill *pid* and children (Windows taskkill /T; POSIX killpg)."""
    if pid <= 0:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F", "/T"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            return
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.info("Mermaid process-tree kill failed: %s", type(exc).__name__)


def _truncate_err(text: str | None, *, limit: int = 200) -> str:
    cleaned = (text or "").strip().replace("\n", " ")
    return cleaned[:limit]


def _safe_rmtree(path: Path) -> None:
    """Best-effort temp cleanup; never block the tool on Windows file locks."""
    try:
        shutil.rmtree(path, ignore_errors=True)
    except OSError:
        logger.debug("Mermaid temp cleanup ignored for %s", path, exc_info=True)


def render_mermaid_to_png(
    source: str,
    *,
    timeout_seconds: int = DEFAULT_MMDC_TIMEOUT_SECONDS,
) -> MermaidRenderResult:
    """Rasterize Mermaid source to PNG via local ``mmdc``.

    Does not call network renderers. On failure returns ``png_bytes=None`` and a
    short ``skipped_reason`` (no credentials or full command dumps). Always
    hard-kills the mmdc process tree on timeout so Chromium cannot hang MCP.
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

    timeout = max(MIN_MMDC_REMAINING_SECONDS, int(timeout_seconds))
    tmp_dir: Path | None = None
    proc: subprocess.Popen[str] | None = None
    try:
        tmp_dir = Path(tempfile.mkdtemp(prefix="cpq_mermaid_"))
        input_path = tmp_dir / "diagram.mmd"
        output_path = tmp_dir / "diagram.png"
        input_path.write_text(text, encoding="utf-8")
        argv = _mmdc_argv(cmd, input_path, output_path)
        popen_kwargs: dict[str, object] = {
            "stdout": subprocess.DEVNULL,
            "stderr": subprocess.PIPE,
            "text": True,
        }
        if sys.platform != "win32":
            popen_kwargs["start_new_session"] = True
        proc = subprocess.Popen(argv, **popen_kwargs)  # type: ignore[arg-type]
        try:
            _stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill_process_tree(proc.pid)
            try:
                proc.wait(timeout=2)
            except (subprocess.TimeoutExpired, OSError):
                pass
            return MermaidRenderResult(
                None, f"mmdc timed out after {timeout_seconds}s"
            )
        if proc.returncode != 0:
            err = _truncate_err(stderr)
            reason = f"mmdc failed (exit {proc.returncode})"
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
    except OSError as exc:
        logger.info("Mermaid render OSError: %s", type(exc).__name__)
        if proc is not None and proc.poll() is None:
            _kill_process_tree(proc.pid)
        return MermaidRenderResult(None, f"mmdc OS error: {type(exc).__name__}")
    finally:
        if proc is not None and proc.poll() is None:
            _kill_process_tree(proc.pid)
            try:
                proc.wait(timeout=1)
            except (subprocess.TimeoutExpired, OSError):
                pass
        if tmp_dir is not None:
            # Brief yield so Windows releases Chromium locks after kill.
            time.sleep(0.05)
            _safe_rmtree(tmp_dir)


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
    "DEFAULT_MMDC_TOTAL_BUDGET_SECONDS",
    "MAX_PNG_BYTES",
    "MIN_MMDC_REMAINING_SECONDS",
    "MermaidRenderResult",
    "load_png_file",
    "mmdc_available",
    "render_mermaid_to_png",
]
