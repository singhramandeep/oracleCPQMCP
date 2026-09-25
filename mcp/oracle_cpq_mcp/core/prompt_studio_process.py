"""Probe and optionally start the local Prompt Studio (localhost FastAPI UI)."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
HEALTH_PATH = "/api/health"
HEALTH_TIMEOUT_S = 1.5
POLL_INTERVAL_S = 0.5
POLL_TIMEOUT_S = 8.0


def repo_root() -> Path:
    """Return the repository root (parent of ``mcp/`` and ``apps/``)."""
    # mcp/oracle_cpq_mcp/core/prompt_studio_process.py → parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def resolve_port(raw: str | None = None) -> int:
    """Parse ``CPQ_PROMPT_STUDIO_PORT`` or return the default."""
    value = raw if raw is not None else os.environ.get("CPQ_PROMPT_STUDIO_PORT")
    if value is None or str(value).strip() == "":
        return DEFAULT_PORT
    try:
        port = int(str(value).strip())
    except ValueError:
        return DEFAULT_PORT
    if not (1 <= port <= 65535):
        return DEFAULT_PORT
    return port


def studio_url(host: str = DEFAULT_HOST, port: int | None = None) -> str:
    p = DEFAULT_PORT if port is None else port
    return f"http://{host}:{p}"


def activation_commands() -> dict[str, str]:
    """Exact install/run/restart commands for agents to show when auto-start fails."""
    win = sys.platform == "win32"
    py = (
        ".\\.venv\\Scripts\\python.exe"
        if win
        else "./.venv/bin/python"
    )
    restart_mod = f"{py} -m apps.prompt_studio restart"
    restart_script = (
        ".\\scripts\\restart-prompt-studio.cmd"
        if win
        else "./scripts/restart-prompt-studio.sh"
    )
    return {
        "powershell": (
            f"{py} -m pip install '.[prompt-studio]'\n"
            f"{py} -m apps.prompt_studio\n"
            f"{py} -m apps.prompt_studio restart"
        ),
        "unix": (
            "./.venv/bin/python -m pip install '.[prompt-studio]'\n"
            "./.venv/bin/python -m apps.prompt_studio\n"
            "./.venv/bin/python -m apps.prompt_studio restart"
        ),
        "module": "python -m apps.prompt_studio",
        "restart": restart_mod,
        "restart_script": restart_script,
        "url": studio_url(),
    }


def _local_addr_matches_port(local: str, port: int) -> bool:
    """Return True when a netstat/lsof local address binds ``port``."""
    text = (local or "").strip()
    if not text:
        return False
    if text.startswith("[") and "]:" in text:
        return text.rsplit("]:", 1)[-1] == str(port)
    return text.endswith(f":{port}")


def list_pids_listening_on_port(port: int) -> list[int]:
    """Return PIDs listening on TCP ``port`` (best-effort; empty if unknown)."""
    pids: set[int] = set()
    if sys.platform == "win32":
        completed = subprocess.run(
            ["netstat", "-ano", "-p", "tcp"],
            capture_output=True,
            text=True,
            check=False,
        )
        for line in completed.stdout.splitlines():
            parts = line.split()
            if len(parts) < 5 or parts[0].upper() != "TCP":
                continue
            if not any(part.upper() == "LISTENING" for part in parts):
                continue
            local = parts[1]
            if not _local_addr_matches_port(local, port):
                continue
            try:
                pid = int(parts[-1])
            except ValueError:
                continue
            if pid > 0:
                pids.add(pid)
        return sorted(pids)

    completed = subprocess.run(
        ["lsof", "-nP", "-iTCP:" + str(port), "-sTCP:LISTEN", "-t"],
        capture_output=True,
        text=True,
        check=False,
    )
    for token in completed.stdout.split():
        try:
            pid = int(token.strip())
        except ValueError:
            continue
        if pid > 0:
            pids.add(pid)
    return sorted(pids)


def _kill_pid(pid: int) -> bool:
    """Terminate ``pid``. Returns True when the kill command reported success."""
    if pid <= 0:
        return False
    try:
        if sys.platform == "win32":
            completed = subprocess.run(
                ["taskkill", "/PID", str(pid), "/F", "/T"],
                capture_output=True,
                text=True,
                check=False,
            )
            return completed.returncode == 0
        import signal

        os.kill(pid, signal.SIGTERM)
        return True
    except OSError:
        return False


def stop_prompt_studio(*, port: int | None = None) -> dict[str, Any]:
    """Stop processes listening on the Prompt Studio port.

    Does not start a new process. Safe when nothing is listening.
    """
    p = port if port is not None else resolve_port()
    found = list_pids_listening_on_port(p)
    stopped: list[int] = []
    failed: list[int] = []
    for pid in found:
        if _kill_pid(pid):
            stopped.append(pid)
        else:
            failed.append(pid)
    return {
        "port": p,
        "url": studio_url(port=p),
        "found": found,
        "stopped": stopped,
        "failed": failed,
        "already_stopped": len(found) == 0,
        "message": (
            f"No process was listening on port {p}."
            if not found
            else (
                f"Stopped Prompt Studio on port {p} "
                f"(pids={stopped or 'none'}; failed={failed or 'none'})."
            )
        ),
    }


def _pin_library_env(root: Path, env: dict[str, str]) -> dict[str, str]:
    from oracle_cpq_mcp.prompts.saved_library import pin_saved_prompts_env

    return pin_saved_prompts_env(root, env)


def probe_health(
    *,
    host: str = DEFAULT_HOST,
    port: int | None = None,
    timeout_s: float = HEALTH_TIMEOUT_S,
) -> bool:
    """Return True if Prompt Studio ``/api/health`` responds with status ok."""
    p = DEFAULT_PORT if port is None else port
    url = f"{studio_url(host, p)}{HEALTH_PATH}"
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as resp:
            if getattr(resp, "status", 200) != 200:
                return False
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        return isinstance(data, dict) and data.get("status") == "ok"
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return False


def _spawn_studio(root: Path) -> subprocess.Popen[Any]:
    env = _pin_library_env(root, os.environ.copy())
    cmd = [sys.executable, "-m", "apps.prompt_studio"]
    log_dir = root / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "prompt_studio.log"
        log_file = open(log_path, "a", encoding="utf-8")  # noqa: SIM115
    except OSError:
        log_file = subprocess.DEVNULL

    kwargs: dict[str, Any] = {
        "cwd": str(root),
        "env": env,
        "stdout": log_file,
        "stderr": subprocess.STDOUT if log_file is not subprocess.DEVNULL else subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        # DETACHED_PROCESS (0x8) | CREATE_NEW_PROCESS_GROUP (0x200) | CREATE_NO_WINDOW (0x08000000)
        kwargs["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000
        kwargs["close_fds"] = True
    else:
        kwargs["start_new_session"] = True

    return subprocess.Popen(cmd, **kwargs)


def ensure_prompt_studio(
    *,
    host: str = DEFAULT_HOST,
    port: int | None = None,
    poll_timeout_s: float = POLL_TIMEOUT_S,
    poll_interval_s: float = POLL_INTERVAL_S,
    spawn_fn: Any | None = None,
    probe_fn: Any | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Ensure Prompt Studio is reachable; start it in the background if needed.

    Always returns a data dict suitable for the MCP success envelope (never raises
    for start failure — includes activation commands instead).
    """
    p = port if port is not None else resolve_port()
    url = studio_url(host, p)
    probe = probe_fn or probe_health
    base: dict[str, Any] = {
        "host": host,
        "port": p,
        "url": url,
        "health_path": HEALTH_PATH,
        "activation_commands": activation_commands(),
    }

    if probe(host=host, port=p):
        return {
            **base,
            "running": True,
            "started": False,
            "message": f"Prompt Studio is already running at {url}",
        }

    root_path = root or repo_root()
    spawn = spawn_fn or (lambda r: _spawn_studio(r))
    pid: int | None = None
    try:
        proc = spawn(root_path)
        pid = getattr(proc, "pid", None)
    except OSError as exc:
        logger.warning("Failed to spawn Prompt Studio: %s", exc)
        return {
            **base,
            "running": False,
            "started": False,
            "error": f"Failed to start Prompt Studio: {exc}",
            "hint": (
                "Install extras and run manually from the repo root "
                "(see activation_commands)."
            ),
            "message": "Prompt Studio is not running and auto-start failed.",
        }

    deadline = time.monotonic() + poll_timeout_s
    while time.monotonic() < deadline:
        if probe(host=host, port=p):
            return {
                **base,
                "running": True,
                "started": True,
                "pid": pid,
                "message": f"Prompt Studio started at {url}",
            }
        time.sleep(poll_interval_s)

    return {
        **base,
        "running": False,
        "started": False,
        "pid": pid,
        "error": (
            f"Started process (pid={pid}) but {url}{HEALTH_PATH} did not become ready "
            f"within {poll_timeout_s:.0f}s."
        ),
        "hint": (
            "Install the prompt-studio extra if missing, then run the module from "
            "the repo root (see activation_commands)."
        ),
        "message": "Prompt Studio auto-start did not become healthy in time.",
    }


__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "activation_commands",
    "ensure_prompt_studio",
    "list_pids_listening_on_port",
    "probe_health",
    "repo_root",
    "resolve_port",
    "stop_prompt_studio",
    "studio_url",
]
