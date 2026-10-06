"""Tests for refined-prompt text placed at the start of Office exports."""

from __future__ import annotations

from oracle_cpq_mcp.prompts.refined_prompt_document import (
    compose_export_notes,
    prepare_refined_prompt_for_document,
    prepend_refined_prompt_sheet,
    strip_variables_section,
)


def test_strip_variables_keeps_search_parameters() -> None:
    text = (
        "### Refined prompt (Better token usage)\n"
        "**Title:** Partner counts\n"
        "**Search / CPQ collections:** limit=1; total_results=true\n"
        "**Variables:** {{q_expr}}=; {{limit}}=1\n"
        "**Tools:** get_datatable_rows\n"
    )
    out = strip_variables_section(text)
    assert "Search / CPQ collections" in out
    assert "limit=1" in out
    assert "Variables" not in out
    assert "{{q_expr}}" not in out or "Tools" in out
    assert "get_datatable_rows" in out


def test_prepare_drops_mustache_placeholders() -> None:
    text = "Use {{q_expr}} on users. **Variables:** x=1\n**Tools:** list_users"
    out = prepare_refined_prompt_for_document(text)
    assert "{{q_expr}}" not in out
    assert "Variables" not in out
    assert "list_users" in out


def test_compose_notes_puts_refined_prompt_first() -> None:
    notes = compose_export_notes(
        "Later notes",
        "**Title:** Audit\n**Search / CPQ collections:** limit=1\n**Variables:** {{limit}}=1",
        enabled=True,
    )
    assert notes is not None
    assert notes.index("Audit") < notes.index("Later notes")
    assert "Variables" not in notes
    assert notes.strip().startswith("## Refined prompt")


def test_compose_notes_disabled_keeps_only_user_notes() -> None:
    notes = compose_export_notes("Only notes", "secret footer", enabled=False)
    assert notes == "Only notes"


def test_prepend_sheet_when_enabled() -> None:
    sheets = [{"name": "Data", "rows": [{"a": 1}]}]
    out = prepend_refined_prompt_sheet(
        sheets, "**Title:** T\n**Variables:** z=1", enabled=True, max_sheets=20
    )
    assert out[0]["name"] == "Refined prompt"
    assert "Variables" not in out[0]["rows"][0]["refined_prompt"]
    assert out[1]["name"] == "Data"


def test_prepend_sheet_skipped_at_cap() -> None:
    sheets = [{"name": f"S{i}", "rows": []} for i in range(20)]
    out = prepend_refined_prompt_sheet(
        sheets, "Title: x", enabled=True, max_sheets=20
    )
    assert out == sheets
