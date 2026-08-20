"""Pytest wrapper for scripts/lint_tool_schemas.py."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lint_tool_schemas import collect_violations  # noqa: E402


def test_tool_schemas_are_compliant() -> None:
    violations = collect_violations()
    assert not violations, "Schema lint failed:\n" + "\n".join(violations)
