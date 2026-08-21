"""MCP tools for saving and picking refined prompts."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.config import update_profile_env_key
from oracle_cpq_mcp.prompts.saved_library import (
    choice_label,
    get_entry,
    last_used,
    list_entries,
    record_use,
    search_entries,
    set_enabled,
    upsert_prompt,
)
from oracle_cpq_mcp.prompts.tags import normalize_tags, tags_for_tools
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.security.context import get_security_context
from oracle_cpq_mcp.tools._register import register_tool


def _active_customer_id() -> str:
    ctx = get_security_context()
    if ctx is None or not ctx.customer_id:
        raise RuntimeError("Security context not configured (no active customer profile).")
    return ctx.customer_id


def _enable_auto_save(enabled: bool) -> dict[str, Any]:
    customer_id = _active_customer_id()
    path = update_profile_env_key(
        customer_id,
        "AUTO_SAVE_REFINED_PROMPT",
        "true" if enabled else "false",
    )
    return {
        "enabled": enabled,
        "path": str(path),
        "key": "AUTO_SAVE_REFINED_PROMPT",
        "note": (
            "Treat this result as source of truth for the rest of this session. "
            "Reload the Oracle CPQ MCP server if you need SERVER_INSTRUCTIONS rebuilt "
            "from the updated profile flag."
        ),
    }


def register_saved_prompt_tools(mcp: Any) -> None:
    """Register saved refined-prompt library tools."""

    def list_saved_prompts(limit: int = 50) -> dict[str, Any]:
        entries = list_entries()
        entries.sort(key=lambda e: e.last_run_at or e.created_at or "", reverse=True)
        clipped = entries[: max(1, min(limit, 200))]
        return {
            "count": len(clipped),
            "total": len(entries),
            "items": [
                {
                    "id": e.id,
                    "title": e.title,
                    "tags": e.tags,
                    "tools": e.tools,
                    "last_run_at": e.last_run_at,
                    "run_count": e.run_count,
                    "label": choice_label(e),
                }
                for e in clipped
            ],
        }

    list_saved_prompts.__doc__ = TOOL_CATALOG["list_saved_prompts"].description
    register_tool(mcp, list_saved_prompts, "list_saved_prompts")

    def search_saved_prompts(
        query: str | None = None,
        tag: str | None = None,
        tool_domain: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        entries = search_entries(query=query, tag=tag, tool_domain=tool_domain)
        clipped = entries[: max(1, min(limit, 100))]
        return {
            "count": len(clipped),
            "items": [
                {
                    "id": e.id,
                    "title": e.title,
                    "tags": e.tags,
                    "tools": e.tools,
                    "label": choice_label(e),
                    "last_run_at": e.last_run_at,
                }
                for e in clipped
            ],
        }

    search_saved_prompts.__doc__ = TOOL_CATALOG["search_saved_prompts"].description
    register_tool(mcp, search_saved_prompts, "search_saved_prompts")

    def get_saved_prompt(prompt_id: str) -> dict[str, Any]:
        entry = get_entry(prompt_id)
        if entry is None:
            return {
                "status": "error",
                "code": "NOT_FOUND",
                "message": f"No saved prompt with id {prompt_id!r}.",
                "hint": "Call list_saved_prompts or search_saved_prompts first.",
            }
        return entry.to_dict()

    get_saved_prompt.__doc__ = TOOL_CATALOG["get_saved_prompt"].description
    register_tool(mcp, get_saved_prompt, "get_saved_prompt")

    def record_prompt_use(prompt_id: str) -> dict[str, Any]:
        entry = record_use(prompt_id)
        if entry is None:
            return {
                "status": "error",
                "code": "NOT_FOUND",
                "message": f"No saved prompt with id {prompt_id!r}.",
                "hint": "Call list_saved_prompts first.",
            }
        return {
            "id": entry.id,
            "title": entry.title,
            "run_count": entry.run_count,
            "last_run_at": entry.last_run_at,
        }

    record_prompt_use.__doc__ = TOOL_CATALOG["record_prompt_use"].description
    register_tool(mcp, record_prompt_use, "record_prompt_use")

    def save_refined_prompt(
        title: str,
        original_user_prompt: str,
        refined_prompt: str,
        variables: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        tools: list[str] | None = None,
        output_format: str = "chat_text",
    ) -> dict[str, Any]:
        tool_names = list(tools or [])
        merged_tags = tags_for_tools(tool_names, extra=tags)
        if tags:
            merged_tags = sorted(set(merged_tags) | set(normalize_tags(tags)))
        entry, created = upsert_prompt(
            title=title,
            original_user_prompt=original_user_prompt,
            refined_prompt=refined_prompt,
            variables=variables,
            tags=merged_tags,
            tools=tool_names,
            output_format=output_format,
        )
        return {
            "created": created,
            "prompt": entry.to_dict(),
            "message": (
                "Saved new refined prompt."
                if created
                else "Updated existing refined prompt (same content hash)."
            ),
        }

    save_refined_prompt.__doc__ = TOOL_CATALOG["save_refined_prompt"].description
    register_tool(mcp, save_refined_prompt, "save_refined_prompt")

    def set_auto_save_refined_prompt(enabled: bool) -> dict[str, Any]:
        return _enable_auto_save(enabled)

    set_auto_save_refined_prompt.__doc__ = TOOL_CATALOG[
        "set_auto_save_refined_prompt"
    ].description
    register_tool(mcp, set_auto_save_refined_prompt, "set_auto_save_refined_prompt")

    def offer_save_refined_prompt(
        title: str,
        original_user_prompt: str,
        refined_prompt: str,
        variables: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        tools: list[str] | None = None,
        output_format: str = "chat_text",
        save: bool | None = None,
        always: bool | None = None,
    ) -> dict[str, Any]:
        """Ask whether to save; if save is None, return chat/elicitation fallback."""
        if save is None:
            return {
                "needs_user_input": True,
                "question": (
                    f"Save refined prompt {title!r}? "
                    "You can also enable auto-save for all future refined prompts "
                    "(writes AUTO_SAVE_REFINED_PROMPT=true to the active profile .env)."
                ),
                "choices": [
                    "save_once — save this prompt only",
                    "save_and_always — save this prompt and auto-save future ones",
                    "skip — do not save",
                ],
                "hint": (
                    "Ask the user, then call offer_save_refined_prompt again with "
                    "save=true|false and optionally always=true (same other args)."
                ),
                "pending": {
                    "title": title,
                    "original_user_prompt": original_user_prompt,
                    "refined_prompt": refined_prompt,
                    "variables": variables or {},
                    "tags": tags or [],
                    "tools": tools or [],
                    "output_format": output_format or "chat_text",
                },
            }
        if save is False:
            return {
                "saved": False,
                "auto_save_enabled": None,
                "message": "User declined to save the refined prompt.",
            }

        result = save_refined_prompt(
            title=title,
            original_user_prompt=original_user_prompt,
            refined_prompt=refined_prompt,
            variables=variables,
            tags=tags,
            tools=tools,
            output_format=output_format,
        )
        if always is True:
            flag = _enable_auto_save(True)
            result = {
                **result,
                "auto_save": flag,
                "message": (
                    f"{result.get('message', 'Saved.')} "
                    "AUTO_SAVE_REFINED_PROMPT=true written to profile .env."
                ),
            }
        return result

    offer_save_refined_prompt.__doc__ = TOOL_CATALOG["offer_save_refined_prompt"].description
    register_tool(mcp, offer_save_refined_prompt, "offer_save_refined_prompt")

    def set_saved_prompt_enabled(prompt_id: str, enabled: bool) -> dict[str, Any]:
        entry = set_enabled(prompt_id, enabled)
        if entry is None:
            return {
                "status": "error",
                "code": "NOT_FOUND",
                "message": f"No saved prompt with id {prompt_id!r}.",
                "hint": "Call list_saved_prompts first.",
            }
        return {
            "id": entry.id,
            "title": entry.title,
            "enabled": entry.enabled,
            "message": (
                f"Saved prompt {entry.title!r} is now "
                f"{'enabled' if entry.enabled else 'disabled'}."
            ),
        }

    set_saved_prompt_enabled.__doc__ = TOOL_CATALOG["set_saved_prompt_enabled"].description
    register_tool(mcp, set_saved_prompt_enabled, "set_saved_prompt_enabled")

    def start_prompt_picker(
        mode: str | None = None,
        query: str | None = None,
        tag: str | None = None,
        tool_domain: str | None = None,
        tool: str | None = None,
        prompt_id: str | None = None,
    ) -> dict[str, Any]:
        """Interactive picker: choose mode / filters, or fetch by prompt_id."""
        if prompt_id:
            entry = get_entry(prompt_id)
            if entry is None:
                return {
                    "status": "error",
                    "code": "NOT_FOUND",
                    "message": f"No saved prompt with id {prompt_id!r}.",
                }
            if not entry.enabled:
                return {
                    "status": "error",
                    "code": "DISABLED",
                    "message": (
                        f"Saved prompt {prompt_id!r} is disabled. "
                        "Enable it with set_saved_prompt_enabled(enabled=true)."
                    ),
                }
            record_use(prompt_id)
            return {
                "selected": entry.to_dict(),
                "message": (
                    "Use selected.refined_prompt (and variables) for the next run. "
                    "Ask for any unset {{placeholders}}, then execute with CPQ MCP tools."
                ),
            }

        if not mode:
            return {
                "needs_user_input": True,
                "question": "How do you want to pick a saved prompt?",
                "choices": [
                    "all — show all enabled prompts by title",
                    "search — search enabled prompt titles",
                    "by_tag — filter by tag",
                    "by_tool — filter by MCP tool name",
                ],
                "hint": (
                    "Ask the user, then call start_prompt_picker again with "
                    "mode=all|search|by_tag|by_tool "
                    "(and query/tag/tool as needed). Extra modes: last5, by_domain."
                ),
            }

        normalized = mode.strip().lower()
        if normalized == "all":
            entries = list_entries()
            entries.sort(key=lambda e: e.title.lower())
        elif normalized == "last5":
            entries = last_used(5)
        elif normalized == "by_tag":
            if not tag:
                existing_tags = sorted({t for e in list_entries() for t in e.tags})
                return {
                    "needs_user_input": True,
                    "question": "Which tag?",
                    "choices": existing_tags
                    or ["users", "groups", "audit", "export"],
                    "hint": "Call start_prompt_picker with mode=by_tag and tag=<choice>.",
                }
            entries = search_entries(tag=tag)
        elif normalized == "by_tool":
            if not tool:
                existing_tools = sorted({t for e in list_entries() for t in e.tools})
                return {
                    "needs_user_input": True,
                    "question": "Which MCP tool?",
                    "choices": existing_tools
                    or ["list_users", "list_groups", "list_datatables"],
                    "hint": "Call start_prompt_picker with mode=by_tool and tool=<name>.",
                }
            entries = search_entries(tool=tool)
        elif normalized == "by_domain":
            if not tool_domain:
                return {
                    "needs_user_input": True,
                    "question": "Which tool domain?",
                    "choices": [
                        "users",
                        "groups",
                        "datatables",
                        "bml",
                        "commerce",
                        "performance",
                        "parts",
                        "tasks",
                        "configuration",
                        "meta",
                    ],
                    "hint": (
                        "Call start_prompt_picker with mode=by_domain "
                        "and tool_domain=<choice>."
                    ),
                }
            entries = search_entries(tool_domain=tool_domain)
        elif normalized == "search":
            if not query:
                return {
                    "needs_user_input": True,
                    "question": "Enter a title search string for saved prompts.",
                    "choices": [],
                    "hint": "Call start_prompt_picker with mode=search and query=<text>.",
                }
            entries = search_entries(query=query)
        else:
            return {
                "status": "error",
                "code": "VALIDATION_ERROR",
                "message": f"Unknown mode {mode!r}.",
                "hint": "Use all, search, by_tag, by_tool, last5, or by_domain.",
            }

        if not entries:
            return {"count": 0, "items": [], "message": "No enabled saved prompts matched."}

        clipped = entries[:50]
        labels = [f"{choice_label(e)} | id={e.id}" for e in clipped]
        return {
            "needs_user_input": True,
            "question": "Pick a saved prompt (reply with the id):",
            "choices": labels,
            "items": [
                {
                    "id": e.id,
                    "title": e.title,
                    "tags": e.tags,
                    "tools": e.tools,
                    "label": choice_label(e),
                }
                for e in clipped
            ],
            "hint": "Call start_prompt_picker with prompt_id=<id> to load and mark as used.",
        }

    start_prompt_picker.__doc__ = TOOL_CATALOG["start_prompt_picker"].description
    register_tool(mcp, start_prompt_picker, "start_prompt_picker")
