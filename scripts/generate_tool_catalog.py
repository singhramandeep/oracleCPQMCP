#!/usr/bin/env python3
"""Generate a formal Markdown tool catalog from the live MCP catalog.

Thin wrapper — prefer ``oracle-cpq generate-tool-catalog`` after ``pip install -e .``.

Usage (from repo root):
    python scripts/generate_tool_catalog.py
    python scripts/generate_tool_catalog.py --out docs/TOOL_CATALOG.md
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MCP = str(_REPO_ROOT / "mcp")
if _MCP in sys.path:
    sys.path.remove(_MCP)
sys.path.insert(0, _MCP)

from oracle_cpq_mcp.cli.generate_tool_catalog import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
