"""Composable MCP server instruction text (no profile I/O)."""

from __future__ import annotations

BASE_SERVER_INSTRUCTIONS = (
    "Oracle CPQ MCP server for Users, Groups, Data Tables, BML, Commerce metadata, "
    "Commerce transactions, Parts, Performance Logs, Metrics, Collaborative Quote "
    "Queues, Site Admin (certificates/SSO), Tasks, and Configuration "
    "(productFamilies). "
    "All calls use the active customer profile from CPQ_CUSTOMER_PROFILE "
    "and environment from CPQ_ENVIRONMENT or the profile default. "
    "Every tool envelope includes profile, environment, and customer_id — always "
    "cite which profile/env answered when comparing dual MCP servers. "
    "Use discover_tools to find tools by domain "
    "(users/groups/datatables/bml/commerce/performance/parts/tasks/configuration/"
    "metrics/collab/admin) or "
    "operation (read/write). Read-only tools are safe for exploration; write tools "
    "(update_user, create_group, deploy_datatables, create_datatable, export_datatables, "
    "export_bml_library_functions, generate_proposal, copy_transaction, "
    "copy_transaction_lines, export_attachment, export_performance_logs, "
    "clear_collab_operation_queue) default to "
    "dry_run=true preflight "
    "mode and require a server-issued confirmation_token before mutating CPQ data. "
    "Never execute writes without user approval and a valid confirmation_token. "
    "When profile READ_ONLY=true (default), all create/update/deploy operations are blocked. "
    "On failure, tools return structured errors: {status: 'error', code, message, hint, details}."
)

CAPABILITY_CARD = (
    " ## Capability card (do not invent out-of-scope CPQ behavior)\n"
    "Covered: users, groups, datatables, BML (incl. local search), commerce metadata/"
    "transactions/saved searches, metrics, collab queues, admin certificates/SSO "
    "(PEM redacted), performance logs, parts, tasks, configuration productFamilies, "
    "local data/ cache, refined prompts, post-response export.\n"
    "Out of scope without dedicated tools: pricing engines, approval workflows, "
    "Document Designer deep editing, arbitrary integrations/webhooks, inventing "
    "quote totals or discount logic.\n"
    "Long jobs: prefer start_bml_site_export → poll get_local_job; for CPQ task "
    "exports use export_* → get_task → download_task_file. Prefer data/ cache and "
    "cpq://local resources over dumping huge payloads into chat.\n"
    "Live honesty: tasks, configuration, some BML/datatable writes, and v19-only "
    "admin/saved-search APIs may be untested or 404 on REST v18 — see "
    "docs/LIVE_SMOKE_MATRIX.md. Prefer LOCAL_DATA_POLICY and list_local_data first.\n"
    "Elicitation: when the host supports MCP elicitation, prefer it for "
    "offer_use_local_data / offer_export_response / offer_save_refined_prompt / "
    "write confirmation; otherwise use the chat fallback (needs_user_input + choices) "
    "and retry the tool with the user's explicit choice.\n"
)

ASYNC_AGENT_LOOP = (
    " Async / long-running: never leave the user waiting on one multi-minute tool "
    "call when avoidable. BML site zip: start_bml_site_export then repeatedly "
    "get_local_job(job_id) until succeeded|failed, then search_local_bml or "
    "cpq://local. Oracle async exports: export_datatables or "
    "export_bml_library_functions (after confirmation) → get_task → "
    "download_task_file. Raise HTTP_TIMEOUT / host CPQ_HTTP_TIMEOUT if short GETs "
    "still time out."
)

REFINED_PROMPT_CORE = (
    " After finishing any CPQ-related task (live MCP tools, local data/ cache reads, "
    "or both), always append a markdown section titled exactly "
    "'### Refined prompt (Better token usage)' with these parts: "
    "(0) '**Title:**' one short human-readable line summarizing the task. "
    "(0b) '**Tags:**' comma-separated tags from domains used "
    "(users/groups/datatables/bml/commerce/performance/parts/tasks/configuration/"
    "metrics/collab/admin/meta) "
    "plus intent tags when relevant (audit, export, write, discovery, read). No icons. "
    "(0c) '**Output format:**' how this answer was shared — one of: chat text, json, "
    "excel download (default chat text). Also include {{output_format}} in Variables "
    "with this-run value chat_text|json|excel_download. "
    "(0d) '**Cached data:**' yes|no|mixed — if yes/mixed, briefly note the local path "
    "(e.g. data/focalpoint/dev/users); if no, say live CPQ. "
    "(1) Then 1–3 short prose paragraphs in plain English: the goal, constraints, "
    "and what to return. Make the prompt generic and copy-paste reusable by replacing "
    "run-specific values (status filters, party numbers, group names, domains, limits, "
    "profile nicknames, etc.) with {{snake_case}} placeholders. Keep it descriptive "
    "enough for an LLM to map to tools without API-call syntax. No credentials. "
    "(2) Then a '**Variables**' bullet list of every {{placeholder}} used (must include "
    "{{output_format}}), each with the value from this run as a hint "
    "(e.g. '{{status_filter}} — this run: active'). "
    "The user may leave placeholders unset when reusing; an LLM should ask for each. "
    "(3) Then a '**Tools (for the agent)**' numbered list naming the exact MCP tools "
    "used; parameter values must use the same {{placeholders}}; page until hasMore=false. "
    "If no MCP tools were used (local file only), write: "
    "'none (local file read only)'. Do not invent tools that were not used. "
    "Do not call extra tools only to produce the refined prompt. "
)

REFINED_PROMPT_SAVE_ASK = (
    "(4) After the footer, call offer_save_refined_prompt (omit save) so the user can "
    "choose: save this prompt once, save and enable AUTO_SAVE_REFINED_PROMPT for future "
    "runs, or skip. Pass output_format=chat_text|json|excel_download (default chat_text). "
    "Pass original_user_prompt as the verbatim user message that started this task "
    "(not the refined footer, not a paraphrase). "
    "Do not invent ad-hoc scripts — use the MCP tools only. "
)

REFINED_PROMPT_SAVE_AUTO = (
    "(4) After the footer, call save_refined_prompt with the same title/tags/variables/"
    "tools/output_format (AUTO_SAVE_REFINED_PROMPT is enabled — do not ask). "
    "Pass original_user_prompt as the verbatim user message that started this task "
    "(not the refined footer, not a paraphrase). "
    "Dedupes by content hash. "
)

PICKER_INSTRUCTIONS = (
    " If the user says 'use a saved prompt', 'pick a saved prompt', 'run saved prompt', "
    "or invokes /OracleCPQ_SavedPrompts, call start_prompt_picker immediately and wait "
    "for their choice before inventing a new free-form CPQ task. Menu modes: all, search, "
    "by_tag, by_tool (disabled prompts are hidden). Hosts may also use the MCP prompt "
    "run_saved_prompt."
)

LOCAL_DATA_CORE = (
    " Before calling live CPQ list/export tools for users, groups, BML, commerce "
    "attributes/actions, or datatables, call list_local_data or get_local_data_status. "
    "Full snapshots live under data/{profile}/{env}/… (JSON + Excel, or .bml+.json for BML). "
    "Honor user phrases: 'use cached/saved data' → load_local_data; "
    "'fresh data' / 'do not use cache' → sync_*_local or live tools. "
    "After a full fetch, sync_*_local / export_users_excel / get_all_bml_code persist "
    "into data/ automatically."
)

LOCAL_DATA_ASK = (
    " LOCAL_DATA_POLICY=ask: when a snapshot exists, call offer_use_local_data "
    "(omit choice) and wait for use_cache / fetch_fresh / prefer / never before "
    "hitting CPQ. prefer/never also update the profile .env via set_local_data_policy."
)

LOCAL_DATA_PREFER = (
    " LOCAL_DATA_POLICY=prefer: use load_local_data when a snapshot exists unless the "
    "user asks for fresh data. On miss, call sync_*_local (or the matching live export)."
)

LOCAL_DATA_NEVER = (
    " LOCAL_DATA_POLICY=never: always fetch from CPQ (sync_*_local or live tools); "
    "still persist full results into data/ for later runs."
)

POST_RESPONSE_EXPORT_CORE = (
    " After a CPQ-related answer that includes tabular data, honor POST_RESPONSE_EXPORT. "
    "Pass structured sheets [{name, columns?, rows}] to export tools — never scrape chat "
    "markdown as the source of truth. Files land under data/{profile}/{env}/exports/."
)

POST_RESPONSE_EXPORT_ASK = (
    " POST_RESPONSE_EXPORT=ask (default): after the refined-prompt footer/save step, "
    "call offer_export_response (omit choice) with title and the same sheets used in chat. "
    "Choices: excel / word / both / skip / always_excel / never. On excel/word/both/"
    "always_excel, call export_response_excel and/or export_response_word with those sheets. "
    "Skip for non-tabular answers or pure errors."
)

POST_RESPONSE_EXPORT_NEVER = (
    " POST_RESPONSE_EXPORT=never: do not offer or auto-export tabular chat answers."
)

POST_RESPONSE_EXPORT_ALWAYS_EXCEL = (
    " POST_RESPONSE_EXPORT=always_excel: after tabular answers (and after the refined-prompt "
    "step), call export_response_excel with the structured sheets — do not ask first."
)

ALIAS_INSTRUCTIONS_HEADER = (
    " Property aliases: when the user refers to a friendly alias phrase below, "
    "use the mapped CPQ variable name in tool arguments (case-insensitive match). "
)


def _format_alias_section(
    *,
    commerce_process_aliases: dict[str, str] | None,
    custom_data_table_aliases: dict[str, str] | None,
) -> str:
    commerce = commerce_process_aliases or {}
    tables = custom_data_table_aliases or {}
    if not commerce and not tables:
        return ""
    lines = [ALIAS_INSTRUCTIONS_HEADER, "## Property aliases"]
    if commerce:
        lines.append("Commerce processes:")
        for alias, var_name in sorted(commerce.items(), key=lambda item: item[0]):
            lines.append(
                f'- "{alias}" → process_var_name={var_name}'
            )
    if tables:
        lines.append("Data tables:")
        for alias, var_name in sorted(tables.items(), key=lambda item: item[0]):
            lines.append(f'- "{alias}" → table_name={var_name}')
    return "\n".join(lines) + "\n"


def _format_knowledge_section(title: str, body: str) -> str:
    text = (body or "").strip()
    if not text:
        return ""
    return f"\n## {title}\n{text}\n"


def build_server_instructions(
    *,
    refined_prompt: bool,
    auto_save_refined_prompt: bool = False,
    local_data_policy: str = "ask",
    post_response_export: str = "ask",
    shared_knowledge: str = "",
    customer_knowledge: str = "",
    commerce_process_aliases: dict[str, str] | None = None,
    custom_data_table_aliases: dict[str, str] | None = None,
) -> str:
    """Compose MCP instructions; include refined-prompt, local-data, knowledge, aliases."""
    text = (
        BASE_SERVER_INSTRUCTIONS
        + CAPABILITY_CARD
        + ASYNC_AGENT_LOOP
        + PICKER_INSTRUCTIONS
        + LOCAL_DATA_CORE
    )
    policy = (local_data_policy or "ask").strip().lower()
    if policy == "prefer":
        text += LOCAL_DATA_PREFER
    elif policy == "never":
        text += LOCAL_DATA_NEVER
    else:
        text += LOCAL_DATA_ASK
    text += POST_RESPONSE_EXPORT_CORE
    export_policy = (post_response_export or "ask").strip().lower()
    if export_policy == "never":
        text += POST_RESPONSE_EXPORT_NEVER
    elif export_policy == "always_excel":
        text += POST_RESPONSE_EXPORT_ALWAYS_EXCEL
    else:
        text += POST_RESPONSE_EXPORT_ASK
    if refined_prompt:
        text += REFINED_PROMPT_CORE
        if auto_save_refined_prompt:
            text += REFINED_PROMPT_SAVE_AUTO
        else:
            text += REFINED_PROMPT_SAVE_ASK
    text += _format_alias_section(
        commerce_process_aliases=commerce_process_aliases,
        custom_data_table_aliases=custom_data_table_aliases,
    )
    text += _format_knowledge_section("Shared knowledge", shared_knowledge)
    text += _format_knowledge_section("Customer knowledge", customer_knowledge)
    return text
