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
    "copy_transaction_lines, create_transaction, new_transaction, add_from_favorites, "
    "display_transaction_history, save_transaction, save_transaction_version, "
    "submit_transaction, reconfigure_transaction, create_transaction_version, "
    "add_transaction_lines, update_transaction_lines, remove_transaction_lines, "
    "delete_transaction_line, interact_transaction_line, reconfigure_transaction_line, "
    "reconfigure_transaction_line_inbound, export_attachment, export_performance_logs, "
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
    "local data/ cache, refined prompts, post-response export, ensure_prompt_studio.\n"
    "Out of scope without dedicated tools: pricing engines, "
    "Document Designer deep editing, arbitrary integrations/webhooks, inventing "
    "quote totals or discount logic. Approval submit is available via submit_transaction "
    "when the site action exists — do not invent approval outcomes.\n"
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

REFINED_PROMPT_GATE = (
    " Refined prompt gate: emit the footer only for real site/cache data work — not "
    "for every chat in this repo. YES when at least one is true this turn: (1) an "
    "Oracle CPQ MCP tool was invoked that reads/writes CPQ or loads/syncs local CPQ "
    "cache (users/groups/commerce/configuration/datatables/bml/transactions/metrics/"
    "parts/tasks/admin/collab/performance, including list_*/get_*/sync_*_local/"
    "load_local_data); (2) the user asked for customer/site CPQ data and the answer "
    "came from data/{profile}/{env}/. NO (skip footer and do not call "
    "offer_save_refined_prompt or save_refined_prompt): editing/reviewing this repo "
    "(tools, tests, docs, YAML, plans, server compliance); generic coding, git, PRs, "
    "or codebase how-to; meta MCP helpers only (discover_tools, saved-prompt "
    "picker/save/offer, export-response policy, ensure_prompt_studio) without a CPQ "
    "data task in the same turn; user says skip refined prompt. Self-check: if Tools "
    "(for the agent) would "
    "be only 'none (local file read only)' and no CPQ site/cache data was returned "
    "to the user, do not emit the refined-prompt section. "
)

PROMPT_STUDIO_ENSURE = (
    " Prompt Studio (YES-gate only): after the refined-prompt footer/save step and "
    "post-response export step on a YES-gate turn, call ensure_prompt_studio "
    "(probes http://127.0.0.1:8765/api/health and auto-starts python -m apps.prompt_studio "
    "if needed). End the user-visible reply with a short Prompt Studio line: the returned "
    "url when running=true; if still down, paste activation_commands from the tool result "
    "(do not invent other scripts). Skip on NO-gate turns. Calling ensure_prompt_studio "
    "alone does not make a turn YES-gate."
)

DOCUMENT_TEMPLATES = (
    " ## Document templates (all IDEs)\n"
    "When creating .docx / .xlsx / .pptx under this repo, ALWAYS clone the branded package "
    "from .config/template/ when that file exists and is a valid Office ZIP (non-empty, "
    "starts with PK). Exact filenames only — do not invent alternate names or paths: "
    "'Word Template.docx', 'Excel Template.xlsx', 'PowerPoint Template.pptx'. "
    "Clone via copy-then-open (or branded_documents helpers): clear body/slide content only; "
    "preserve section headers/footers, logos, themes, and style definitions. "
    "Word content must use template styles by name when present: Title (else Heading 1) for "
    "the document title; Heading 1 / Heading 2 / Heading 3 for sections; Normal for notes/body. "
    "Prefer a template table style when one exists (Table Grid is an acceptable fallback). "
    "Missing, zero-byte, or unreadable templates → blank document and note that the template "
    "was not applied — do not invent logos, fonts, or branding. "
    "Treat .config/template/ as read-only: never create, overwrite, delete, or 'fix' files "
    "there — the user alone maintains branding templates. "
    "Write new Office files under data/{profile}/{env}/exports/ (or another non-template path). "
    "MCP export_response_excel / export_response_word must use "
    "oracle_cpq_mcp.exporters.branded_documents (open_word_document / open_excel_workbook / "
    "open_pptx_presentation). See .config/template/README.md and AGENTS.md. "
    "Word-only diagrams: export_response_word accepts diagrams "
    "[{title, mermaid?, image_path?, caption?}] (max 8) after notes and before tables. "
    "Diagram images and captions are center-aligned in the Word body. "
    "For analytical or structured Word exports (audits, pass/fail summaries, flows, "
    "comparisons, relationship reviews), include 1–3 Mermaid diagrams — expected, not "
    "merely optional; do not wait for the user to ask. Skip diagrams for trivial short "
    "lists or pure errors. "
    "Prefer flowchart/graph over dense ER diagrams unless relationships are the point. "
    "Pass Mermaid source for local mmdc rendering, or a PNG path under tmp/{profile}/{env}/ "
    "(never .config/template/). Do not send diagram source to public Kroki/mermaid.ink. "
    "If mmdc is missing, still pass mermaid source (export succeeds; note diagrams_skipped "
    "and suggest: npm i -g @mermaid-js/mermaid-cli); never paste Mermaid source as the only "
    "visual when mmdc works. "
    "Structure Word notes with newlines and ## / ### headings plus - / * bullets — never "
    "one dense unformatted paragraph. "
    "These MCP instructions are authoritative across Antigravity, Cursor, and VS Code — "
    "do not rely on .cursor/rules alone.\n"
)

PROFILE_CREDENTIALS = (
    " ## Profile credentials (never edit)\n"
    "Never create, edit, delete, reformat, quote, or rewrite username / password fields "
    "(or DEV_USERNAME / DEV_PASSWORD / TEST_* / PROD_* credential keys) in "
    ".config/*.yaml or .config/*.env. The user alone owns credential changes. "
    "On 401 or profile-load failures: report the error; do not 'fix' credentials. "
    "Never paste passwords into chat. Allowed profile YAML edits are non-secret catalog "
    "fields only (e.g. product_families, commerce_processes, data_tables, aliases) when "
    "the user explicitly asks. "
    "Live CPQ access must go only through Oracle CPQ MCP tools. Never use profile "
    "username/password to call CPQ REST directly (curl, httpx, requests, browser Basic "
    "auth, or local scripts that load_profile + CPQClient / Basic auth for user tasks). "
    "Report auth failures (401, locked account) without inventing alternate auth paths.\n"
)

AGENT_SCRATCH_FILES = (
    " ## Scratch files (reuse under tmp/)\n"
    "Never write scratch or temporary analysis files at the repo root. "
    "Write reusable intermediate artifacts (JSON, MD, small xlsx dumps that are not MCP "
    "export_response_*) under tmp/{profile}/{env}/ with clear descriptive names "
    "(prefer stems like layout_transaction.json over a leading tmp_). "
    "Create the directory if missing. "
    "When any such file is created or updated during a turn, include a short user-visible "
    "'Scratch files' section (or bullet list) with the path(s) so the user knows they are "
    "available for reuse. Never put credentials or passwords in scratch files. "
    "Formal branded Office exports still go through MCP to data/{profile}/{env}/exports/.\n"
)

REFINED_PROMPT_CORE = (
    REFINED_PROMPT_GATE
    + " When the gate is YES, append a markdown section titled exactly "
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
    "If no MCP tools were used but site/cache data came from local files, write: "
    "'none (local file read only)'. Do not invent tools that were not used. "
    "Do not call extra tools only to produce the refined prompt. "
    "(3b) Then '**Turn metrics:**' with two bullets: "
    "'**Elapsed:**' best-effort wall-clock for this agent turn "
    "(e.g. 45s or 2m 10s) or 'not available' if it cannot be estimated; "
    "'**Tokens:**' input/output/total only if the platform surfaces usage for this turn; "
    "otherwise 'not available'. Do not invent precise token counts. "
)

REFINED_PROMPT_SAVE_ASK = (
    "(4) Only when the refined-prompt gate is YES: after the footer, call "
    "offer_save_refined_prompt (omit save) so the user can "
    "choose: save this prompt once, save and enable AUTO_SAVE_REFINED_PROMPT for future "
    "runs, or skip. Pass output_format=chat_text|json|excel_download (default chat_text). "
    "Pass original_user_prompt as the verbatim user message that started this task "
    "(not the refined footer, not a paraphrase). "
    "Do not invent ad-hoc scripts — use the MCP tools only. "
    "When the gate is NO, do not call offer_save_refined_prompt. "
)

REFINED_PROMPT_SAVE_AUTO = (
    "(4) Only when the refined-prompt gate is YES: after the footer, call "
    "save_refined_prompt with the same title/tags/variables/"
    "tools/output_format (AUTO_SAVE_REFINED_PROMPT is enabled — do not ask). "
    "Pass original_user_prompt as the verbatim user message that started this task "
    "(not the refined footer, not a paraphrase). "
    "Dedupes by content hash. "
    "When the gate is NO, do not call save_refined_prompt. "
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
    " After a YES-gate site/cache data answer that includes tabular data, honor "
    "POST_RESPONSE_EXPORT. Use the same refined-prompt YES/NO gate — skip export for "
    "repo/code-review tables. "
    "Pass structured sheets [{name, columns?, rows}] to export tools — never scrape chat "
    "markdown as the source of truth. Files land under data/{profile}/{env}/exports/."
)

POST_RESPONSE_EXPORT_ASK = (
    " POST_RESPONSE_EXPORT=ask (default): after the refined-prompt footer/save step "
    "(when the gate is YES), "
    "call offer_export_response (omit choice) with title and the same sheets used in chat. "
    "Choices: excel / word / both / skip / always_excel / never. On excel/word/both/"
    "always_excel, call export_response_excel and/or export_response_word with those sheets. "
    "When calling export_response_word (word or both), include 1–3 Mermaid diagrams via "
    "diagrams [{title, mermaid?, image_path?, caption?}] for analytical/structured answers "
    "(audits, pass/fail, flows, comparisons) without waiting for the user to ask; skip "
    "diagrams for trivial lists or pure errors. Prefer flowchart/graph; render locally via "
    "mmdc (never Kroki/mermaid.ink); if mmdc is missing still pass mermaid and tell the "
    "user about diagrams_skipped. Structure notes with ## / bullets, not one dense paragraph. "
    "Skip for NO-gate turns, non-tabular answers, or pure errors."
)

POST_RESPONSE_EXPORT_NEVER = (
    " POST_RESPONSE_EXPORT=never: do not offer or auto-export tabular chat answers."
)

POST_RESPONSE_EXPORT_ALWAYS_EXCEL = (
    " POST_RESPONSE_EXPORT=always_excel: after YES-gate tabular answers (and after the "
    "refined-prompt step), call export_response_excel with the structured sheets — "
    "do not ask first. Skip when the refined-prompt gate is NO."
)

ALIAS_INSTRUCTIONS_HEADER = (
    " Property aliases: when the user refers to a friendly alias phrase below, "
    "use the mapped CPQ variable name in tool arguments (case-insensitive match). "
)


def _format_alias_section(
    *,
    commerce_process_aliases: dict[str, str] | None,
    custom_data_table_aliases: dict[str, str] | None,
    product_family_aliases: dict[str, str] | None = None,
    product_line_aliases: dict[str, str] | None = None,
    product_model_aliases: dict[str, str] | None = None,
) -> str:
    commerce = commerce_process_aliases or {}
    tables = custom_data_table_aliases or {}
    families = product_family_aliases or {}
    lines_map = product_line_aliases or {}
    models = product_model_aliases or {}
    if not commerce and not tables and not families and not lines_map and not models:
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
    if families:
        lines.append("Product families:")
        for alias, var_name in sorted(families.items(), key=lambda item: item[0]):
            lines.append(f'- "{alias}" → prod_fam_var_name={var_name}')
    if lines_map:
        lines.append("Product lines:")
        for alias, var_name in sorted(lines_map.items(), key=lambda item: item[0]):
            lines.append(f'- "{alias}" → product_line_var_name={var_name}')
    if models:
        lines.append("Product models:")
        for alias, var_name in sorted(models.items(), key=lambda item: item[0]):
            lines.append(f'- "{alias}" → model_var_name={var_name}')
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
    product_family_aliases: dict[str, str] | None = None,
    product_line_aliases: dict[str, str] | None = None,
    product_model_aliases: dict[str, str] | None = None,
) -> str:
    """Compose MCP instructions; include refined-prompt, local-data, knowledge, aliases."""
    text = (
        BASE_SERVER_INSTRUCTIONS
        + CAPABILITY_CARD
        + PROFILE_CREDENTIALS
        + AGENT_SCRATCH_FILES
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
    text += DOCUMENT_TEMPLATES
    text += PROMPT_STUDIO_ENSURE
    if refined_prompt:
        text += REFINED_PROMPT_CORE
        if auto_save_refined_prompt:
            text += REFINED_PROMPT_SAVE_AUTO
        else:
            text += REFINED_PROMPT_SAVE_ASK
    text += _format_alias_section(
        commerce_process_aliases=commerce_process_aliases,
        custom_data_table_aliases=custom_data_table_aliases,
        product_family_aliases=product_family_aliases,
        product_line_aliases=product_line_aliases,
        product_model_aliases=product_model_aliases,
    )
    text += _format_knowledge_section("Shared knowledge", shared_knowledge)
    text += _format_knowledge_section("Customer knowledge", customer_knowledge)
    return text
