"""Run Prompt Studio: python -m apps.prompt_studio"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_import_paths() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    mcp_path = repo_root / "mcp"
    for path in (str(repo_root), str(mcp_path)):
        if path not in sys.path:
            sys.path.insert(0, path)
    return repo_root


def main() -> None:
    _ensure_import_paths()

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

    print("Prompt Studio -> http://127.0.0.1:8765  (Ctrl+C to stop)")
    uvicorn.run(app, host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()
