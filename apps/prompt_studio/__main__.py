"""Run Prompt Studio: python -m apps.prompt_studio [start|stop|restart]

Commands:
  start (default)  Run the UI in the foreground (Ctrl+C to stop).
  stop             Kill whatever is listening on the Studio port (default 8765).
  restart          Stop listeners on the port, then start in the foreground.

Examples (repo root, project venv):

  .\\.venv\\Scripts\\python.exe -m apps.prompt_studio
  .\\.venv\\Scripts\\python.exe -m apps.prompt_studio stop
  .\\.venv\\Scripts\\python.exe -m apps.prompt_studio restart

Or: .\\scripts\\restart-prompt-studio.cmd  /  ./scripts/restart-prompt-studio.sh
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _ensure_import_paths() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    mcp_path = repo_root / "mcp"
    for path in (str(repo_root), str(mcp_path)):
        if path not in sys.path:
            sys.path.insert(0, path)
    return repo_root


def _pin_library_env(repo_root: Path) -> None:
    """Align Studio with MCP defaults so both read the same saved_prompts.json."""
    from oracle_cpq_mcp.prompts.saved_library import pin_saved_prompts_env

    pinned = pin_saved_prompts_env(repo_root, dict(os.environ))
    os.environ["CPQ_CONFIG_DIR"] = pinned["CPQ_CONFIG_DIR"]
    os.environ["CPQ_SAVED_PROMPTS_PATH"] = pinned["CPQ_SAVED_PROMPTS_PATH"]


def _run_server(repo_root: Path) -> None:
    _pin_library_env(repo_root)

    try:
        import uvicorn
    except ImportError:
        print(
            "Prompt Studio needs fastapi and uvicorn.\n"
            "  .\\.venv\\Scripts\\python.exe -m pip install '.[prompt-studio]'\n"
            "  .\\.venv\\Scripts\\python.exe -m apps.prompt_studio\n"
            "Or: pip install 'fastapi>=0.115' 'uvicorn[standard]>=0.30'",
            file=sys.stderr,
        )
        raise SystemExit(1) from None

    try:
        from apps.prompt_studio.app import app
    except ImportError as exc:
        missing = getattr(exc, "name", None) or str(exc)
        print(
            f"Failed to load Prompt Studio ({missing}).\n"
            "Use the project venv and install extras:\n"
            "  .\\.venv\\Scripts\\python.exe -m pip install '.[prompt-studio]'\n"
            "  .\\.venv\\Scripts\\python.exe -m apps.prompt_studio",
            file=sys.stderr,
        )
        raise SystemExit(1) from None

    from oracle_cpq_mcp.core.prompt_studio_process import resolve_port, studio_url

    port = resolve_port()
    print(f"Prompt Studio -> {studio_url(port=port)}  (Ctrl+C to stop)")
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False)


def _cmd_stop() -> int:
    from oracle_cpq_mcp.core.prompt_studio_process import stop_prompt_studio

    result = stop_prompt_studio()
    print(result["message"])
    if result.get("failed"):
        return 1
    return 0


def _cmd_restart(repo_root: Path) -> None:
    from oracle_cpq_mcp.core.prompt_studio_process import stop_prompt_studio

    result = stop_prompt_studio()
    print(result["message"])
    if result.get("failed"):
        print(
            "Some processes could not be stopped; not starting a new instance.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    # Brief pause so the OS releases the port after taskkill/SIGTERM.
    import time

    time.sleep(0.4)
    _run_server(repo_root)


def main(argv: list[str] | None = None) -> None:
    repo_root = _ensure_import_paths()
    parser = argparse.ArgumentParser(
        prog="python -m apps.prompt_studio",
        description="Local Prompt Studio (saved prompts UI).",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="start",
        choices=("start", "stop", "restart"),
        help="start (default), stop, or restart",
    )
    args = parser.parse_args(argv)

    if args.command == "stop":
        raise SystemExit(_cmd_stop())
    if args.command == "restart":
        _cmd_restart(repo_root)
        return
    _run_server(repo_root)


if __name__ == "__main__":
    main()
