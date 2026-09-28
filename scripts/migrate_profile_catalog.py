#!/usr/bin/env python3
"""Deprecated: use oracle-cpq migrate-yaml / scripts/migrate_profile_yaml.py.

Thin wrapper around ``oracle_cpq_mcp.cli.migrate_catalog``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MCP = str(_REPO_ROOT / "mcp")
if _MCP in sys.path:
    sys.path.remove(_MCP)
sys.path.insert(0, _MCP)

from oracle_cpq_mcp.cli.migrate_catalog import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
