"""Extract and fill {{snake_case}} placeholders in refined prompts."""

from __future__ import annotations

import re
from typing import Any

PLACEHOLDER_RE = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")
VAR_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


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


def validate_var_name(name: str) -> str:
    """Return normalized var name or raise ValueError."""
    cleaned = (name or "").strip().lower()
    if not VAR_NAME_RE.match(cleaned):
        raise ValueError(
            "Variable name must be snake_case starting with a letter "
            "(e.g. token_a, customer_profile)."
        )
    return cleaned


def suggest_var_name(selected: str, existing: set[str] | None = None) -> str:
    """Suggest a snake_case variable name from selected literal text."""
    taken = existing or set()
    raw = (selected or "").strip()
    if not raw:
        return _next_token_name(taken)

    parts = re.findall(r"[a-z0-9]+", raw.lower())
    if not parts:
        return _next_token_name(taken)

    candidate = "_".join(parts)[:40]
    if not VAR_NAME_RE.match(candidate):
        candidate = f"var_{candidate}"[:40]
        candidate = re.sub(r"[^a-z0-9_]", "", candidate)
        if not candidate or not candidate[0].isalpha():
            candidate = _next_token_name(taken)

    base = candidate
    suffix = 2
    while candidate in taken:
        candidate = f"{base}_{suffix}"
        suffix += 1
    return candidate


def _next_token_name(taken: set[str]) -> str:
    for letter in "abcdefghijklmnopqrstuvwxyz":
        name = f"token_{letter}"
        if name not in taken:
            return name
    return "token_a"


def wrap_selection(text: str, start: int, end: int, var_name: str) -> str:
    """Replace text[start:end] with {{var_name}}."""
    name = validate_var_name(var_name)
    if start < 0 or end < start or end > len(text):
        raise ValueError("Invalid selection range for wrap_selection")
    return text[:start] + "{{" + name + "}}" + text[end:]


def reconcile_variables(
    refined_prompt: str,
    variables: dict[str, Any] | None,
) -> dict[str, Any]:
    """Keep hints for placeholders still present; add empty hints for new ones."""
    existing = dict(variables or {})
    result: dict[str, Any] = {}
    for name in extract_placeholders(refined_prompt):
        if name in existing:
            result[name] = existing[name]
        else:
            result[name] = ""
    return result
