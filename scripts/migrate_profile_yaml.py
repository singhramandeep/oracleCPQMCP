#!/usr/bin/env python3
"""Migrate a legacy `.config/<id>.env` into a unified `.config/<id>.yaml`.

Thin wrapper — prefer ``oracle-cpq migrate-yaml`` after ``pip install -e .``.

Usage:
  python scripts/migrate_profile_yaml.py mycompany
  python scripts/migrate_profile_yaml.py mycompany --force
  python scripts/migrate_profile_yaml.py mycompany --dry-run
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MCP = str(_REPO_ROOT / "mcp")
if _MCP in sys.path:
    sys.path.remove(_MCP)
sys.path.insert(0, _MCP)

from oracle_cpq_mcp.cli.migrate_yaml import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
