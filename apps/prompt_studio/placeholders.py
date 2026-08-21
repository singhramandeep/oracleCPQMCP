"""Extract and fill {{snake_case}} placeholders in refined prompts."""

from __future__ import annotations

import re
from typing import Any

PLACEHOLDER_RE = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")


def extract_placeholders(text: str) -> list[str]:
    """Return unique placeholder names in first-seen order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for match in PLACEHOLDER_RE.finditer(text or ""):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def fill_placeholders(text: str, values: dict[str, Any]) -> str:
    """Substitute {{name}} with values; missing keys become empty string."""

    def _repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values or values[key] is None:
            return ""
        return str(values[key])

    return PLACEHOLDER_RE.sub(_repl, text or "")
