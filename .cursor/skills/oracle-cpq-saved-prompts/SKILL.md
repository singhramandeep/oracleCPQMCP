---
name: oracle-cpq-saved-prompts
description: >-
  Pick and run an enabled Oracle CPQ saved refined prompt (same as /OracleCPQ_SavedPrompts).
  Use when the user wants to browse saved prompts by title, search, tag, or tool and execute one.
disable-model-invocation: true
---

# Oracle CPQ — pick & run a saved refined prompt

You are helping the user pick an **enabled** saved refined prompt from the local library and **execute** it with Oracle CPQ MCP tools.

## Required flow

1. Call `start_prompt_picker` with no arguments (omit `mode`).
2. Present the returned choices clearly:
   - **all** — show all enabled prompts by title
   - **search** — search enabled prompt titles
   - **by_tag** — filter by tag
   - **by_tool** — filter by MCP tool name
3. After the user answers, call `start_prompt_picker` again with:
   - `mode=all`, or
   - `mode=search` and `query=<text>`, or
   - `mode=by_tag` and `tag=<tag>`, or
   - `mode=by_tool` and `tool=<tool_name>`
4. When the tool returns a list of prompts, show titles (and ids). Ask the user to pick one id.
5. Call `start_prompt_picker` with `prompt_id=<id>`.
6. Execute `selected.refined_prompt` using the listed tools. Ask for any unset `{{placeholders}}` before calling tools. Page list tools until `hasMore=false`.

## Rules

- Use MCP tools only — never invent ad-hoc Python scripts to read `.config/saved_prompts.json`.
- Never show or run **disabled** prompts. To re-enable one, use `set_saved_prompt_enabled(prompt_id=..., enabled=true)`.
- Do not invent a free-form CPQ task until a saved prompt is selected (or the user cancels).
