"""MCP resources and prompts for the saved refined-prompt library."""

from __future__ import annotations

import json
from typing import Any

from oracle_cpq_mcp.prompts.saved_library import get_entry, list_entries, record_use


def register_saved_prompt_resources_and_prompts(mcp: Any) -> None:
    """Register cpq://saved-prompts resources and run_saved_prompt MCP prompt."""

    @mcp.resource("cpq://saved-prompts")
    def saved_prompts_index() -> str:
        """JSON index of enabled locally saved refined prompts."""
        items = [
            {
                "id": e.id,
                "title": e.title,
                "tags": e.tags,
                "tools": e.tools,
                "output_format": e.output_format,
                "last_run_at": e.last_run_at,
                "run_count": e.run_count,
                "enabled": e.enabled,
            }
            for e in list_entries()
        ]
        return json.dumps({"count": len(items), "prompts": items}, indent=2)

    @mcp.resource("cpq://saved-prompts/{prompt_id}")
    def saved_prompt_resource(prompt_id: str) -> str:
        """JSON body for one saved refined prompt (enabled only for public view)."""
        entry = get_entry(prompt_id)
        if entry is None:
            return json.dumps({"error": "not_found", "prompt_id": prompt_id})
        if not entry.enabled:
            return json.dumps(
                {
                    "error": "disabled",
                    "prompt_id": prompt_id,
                    "hint": "Enable with set_saved_prompt_enabled(enabled=true).",
                }
            )
        return json.dumps(entry.to_dict(), indent=2)

    @mcp.prompt(
        name="run_saved_prompt",
        description=(
            "Inject an enabled saved refined prompt into the conversation by id or exact title."
        ),
    )
    def run_saved_prompt(prompt_id: str = "", title: str = "") -> str:
        """Return the refined prompt text for the agent to execute."""
        entry = None
        if prompt_id.strip():
            entry = get_entry(prompt_id.strip())
            if entry is not None and not entry.enabled:
                return (
                    f"Saved prompt {prompt_id!r} is disabled. "
                    "Enable it with set_saved_prompt_enabled, then retry."
                )
        elif title.strip():
            needle = title.strip().lower()
            for candidate in list_entries():
                if candidate.title.lower() == needle:
                    entry = candidate
                    break
        if entry is None:
            return (
                "No matching enabled saved prompt. Use list_saved_prompts or "
                "start_prompt_picker / /OracleCPQ_SavedPrompts, then retry with a valid "
                "prompt_id or title."
            )
        record_use(entry.id)
        variables = "\n".join(
            f"- {k}: {v}" for k, v in (entry.variables or {}).items()
        ) or "(none)"
        fmt = entry.output_format or "chat_text"
        fmt_label = {
            "chat_text": "chat text",
            "json": "json",
            "excel_download": "excel download",
        }.get(fmt, fmt)
        return (
            f"# Saved prompt: {entry.title}\n\n"
            f"Tags: {', '.join(entry.tags) or 'none'}\n\n"
            f"Output format: {fmt_label} (`{fmt}`)\n\n"
            f"## Original user prompt\n{entry.original_user_prompt}\n\n"
            f"## Refined prompt\n{entry.refined_prompt}\n\n"
            f"## Variables (this run hints)\n{variables}\n\n"
            "Execute the refined prompt using Oracle CPQ MCP tools (and local data/ "
            "cache tools when appropriate). "
            f"Deliver the answer in output format `{fmt}` "
            f"({fmt_label}). "
            "Ask the user to fill any unset {{placeholders}}."
        )
