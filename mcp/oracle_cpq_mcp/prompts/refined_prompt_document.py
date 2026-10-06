"""Prepare YES-gate refined prompt text for Office exports (no Variables block)."""

from __future__ import annotations

import re
from typing import Any

_MUSTACHE = re.compile(r"\{\{[a-z][a-z0-9_]*\}\}")
_HEADING_MARK = re.compile(r"^\s*(#{1,3}\s+|\*\*)")
_VARIABLES_MARK = re.compile(r"(?i)(?:#{1,3}\s*)?\*{0,2}Variables\*{0,2}\s*:?")


def strip_variables_section(text: str) -> str:
    """Drop the **Variables** / ## Variables block; keep parameter sections."""
    lines = str(text or "").splitlines()
    out: list[str] = []
    skipping = False
    for line in lines:
        stripped = line.strip()
        marker = _VARIABLES_MARK.search(line)
        if marker is not None:
            prefix = line[: marker.start()].rstrip()
            if prefix:
                out.append(prefix)
            skipping = True
            continue
        if skipping and _HEADING_MARK.match(stripped):
            skipping = False
        if skipping:
            continue
        out.append(line)
    return "\n".join(out).strip()


def strip_unused_placeholders(text: str) -> str:
    """Remove leftover {{snake_case}} tokens after unused keys are omitted."""
    cleaned = _MUSTACHE.sub("", text)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


def prepare_refined_prompt_for_document(text: str | None) -> str:
    """Return refined-prompt prose with parameters, without a Variables dump."""
    raw = str(text or "").strip()
    if not raw:
        return ""
    return strip_unused_placeholders(strip_variables_section(raw))


def compose_export_notes(
    notes: str | None,
    refined_prompt: str | None,
    *,
    enabled: bool,
) -> str | None:
    """Put the prepared refined prompt at the start of Word notes."""
    parts: list[str] = []
    if enabled:
        body = prepare_refined_prompt_for_document(refined_prompt)
        if body:
            head = body.lstrip().lower()[:96]
            if "refined prompt" not in head:
                body = "## Refined prompt\n" + body
            parts.append(body)
    if notes and str(notes).strip():
        parts.append(str(notes).strip())
    return "\n\n".join(parts) if parts else None


def prepend_refined_prompt_sheet(
    sheets: list[dict[str, Any]],
    refined_prompt: str | None,
    *,
    enabled: bool,
    max_sheets: int,
) -> list[dict[str, Any]]:
    """Insert a Refined prompt sheet as Excel sheet 1 when there is room."""
    if not enabled:
        return sheets
    body = prepare_refined_prompt_for_document(refined_prompt)
    if not body:
        return sheets
    if len(sheets) >= max_sheets:
        return sheets
    intro = {
        "name": "Refined prompt",
        "columns": ["refined_prompt"],
        "rows": [{"refined_prompt": body}],
    }
    return [intro, *sheets]
