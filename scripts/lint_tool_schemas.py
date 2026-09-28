#!/usr/bin/env python3
"""Fail-closed lint: catalog ↔ input models and Field descriptions.

Thin wrapper — prefer ``oracle-cpq lint-schemas`` after ``pip install -e .``.

Usage:
    python scripts/lint_tool_schemas.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MCP = str(_REPO_ROOT / "mcp")
if _MCP in sys.path:
    sys.path.remove(_MCP)
sys.path.insert(0, _MCP)

from oracle_cpq_mcp.cli.lint_schemas import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
