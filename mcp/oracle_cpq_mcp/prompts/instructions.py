"""Composable MCP server instruction text (no profile I/O)."""

from __future__ import annotations

# Compressed for context budget. Safety rules must stay; prose is shortened.

BASE_SERVER_INSTRUCTIONS = (
    "Oracle CPQ MCP — domains: users, groups, datatables, BML, commerce metadata/"
    "transactions, parts, performance, metrics, collab, admin (certs/SSO), tasks, "
    "configuration (productFamilies), CX (sales/prm when enabled), local data, "
    "meta (discover/export/prompts). "
    "Active profile = CPQ_CUSTOMER_PROFILE; env = CPQ_ENVIRONMENT or profile default. "
    "Cite profile+environment from tool envelopes. Use discover_tools by domain/"
    "cx_module/operation. Writes: dry_run=true then confirmation_token; never apply "
    "without user approval. READ_ONLY=true (default) blocks create/update/deploy. "
    "Errors: {status, code, message, hint, details}."
)

CAPABILITY_CARD = (
    " ## Capability card\n"
    "Out of scope without tools: pricing engines, Document Designer deep edit, "
    "invented quote totals/discounts/approval outcomes. "
    "Long jobs: start_bml_site_export→get_local_job; export_*→get_task→download_task_file. "
    "Prefer data/ cache over huge chat dumps. Untested/live gaps: docs/LIVE_SMOKE_MATRIX.md. "
    "Elicitation preferred for offer_* / write confirm; else chat choices + retry.\n"
)

ASYNC_AGENT_LOOP = (
    " Async: BML zip start_bml_site_export then poll get_local_job; Oracle exports "
    "export_*→get_task→download_task_file. Raise HTTP_TIMEOUT if GETs time out."
)

PROFILE_CREDENTIALS = (
    " ## Profile credentials (never edit)\n"
    "Never create/edit/delete/reformat username, password, oauth_client_id, "
    "oauth_client_secret (or *_USERNAME/*_PASSWORD / oauth_* secrets) in "
    ".config/*.yaml|.env. On 401: report only — do not 'fix' credentials. "
    "Never paste secrets in chat. Live CPQ only via Oracle CPQ MCP tools — never "
    "curl/httpx/load_profile+CPQClient with profile secrets. Non-secret catalog YAML "
    "edits only when user asks.\n"
)

AGENT_SCRATCH_FILES = (
    " ## Scratch files\n"
    "Write intermediates under tmp/{profile}/{env}/ (never repo root). List paths "
    "under 'Scratch files' when created. No credentials in scratch. Branded Office "
    "exports → MCP → data/{profile}/{env}/exports/.\n"
)

CUSTOMER_KNOWLEDGE_MEMORY = (
    " ## Customer knowledge (cross-session memory)\n"
    "After substantive site/cache discoveries, call append_customer_knowledge with a "
    "concise bullet summary (not raw dumps — point to data/ paths). "
    "Before repeating discovery, call get_customer_knowledge. "
    "ensure_customer_knowledge wires knowledge/{customer_id}.md + profile field. "
    "Never store passwords, tokens, or OAuth secrets in knowledge.\n"
)

DOCUMENT_TEMPLATES = (
    " ## Document templates\n"
    "Clone .config/template/ when valid (PK ZIP): 'Word Template.docx', "
    "'Excel Template.xlsx', 'PowerPoint Template.pptx'. Clear body only; keep "
    "header/footer/logo. Styles: Title (or H1), H1–H3, Normal. Template dir "
    "read-only. Exports via branded_documents. Analytical Word: 1–3 Mermaid "
    "diagrams via diagrams[] (local mmdc; no Kroki/mermaid.ink); content-first; "
    "notes with ## / bullets. Skip diagrams for trivial lists/errors. "
    "MCP instructions beat .cursor/rules.\n"
)

REFINED_PROMPT_GATE = (
    " Refined prompt gate: YES only for real site/cache CPQ data "
    "(list_*/get_*/sync_*/load_local_data or data/{profile}/{env}/ answers). "
    "NO for repo/coding/meta-only (discover_tools, offer_*, ensure_prompt_studio alone). "
    "Skip if Tools would be only 'none (local file read only)' with no site data. "
)

REFINED_PROMPT_CORE = (
    REFINED_PROMPT_GATE
    + " YES → append '### Refined prompt (Better token usage)': "
    "**Title**; **Tags** (domains+intent); **Output format** (chat text|json|excel download) "
    "+ {{output_format}}=chat_text|json|excel_download; **Cached data** yes|no|mixed; "
    "1–3 prose paras with {{snake_case}}; **Variables** (incl. {{output_format}}); "
    "**Tools** exact MCP names (or 'none (local file read only)'); "
    "**Turn metrics:** **Elapsed** only — Do not include token counts. "
    "Saved-prompt runs: record_prompt_use(prompt_id, duration_ms, source=cache|api|mixed). "
)

REFINED_PROMPT_SAVE_ASK = (
    " YES only: after footer call offer_save_refined_prompt (omit save); "
    "pass original_user_prompt verbatim + output_format. NO → do not call. "
)

REFINED_PROMPT_SAVE_AUTO = (
    " YES only: after footer call save_refined_prompt (AUTO_SAVE — do not ask) "
    "with original_user_prompt verbatim. NO → do not call. "
)

PROMPT_STUDIO_ENSURE = (
    " YES-gate only: after refined+export steps call ensure_prompt_studio; "
    "end with Prompt Studio url or activation_commands. Skip on NO-gate."
)

PICKER_INSTRUCTIONS = (
    " 'use a saved prompt' / /OracleCPQ_SavedPrompts → start_prompt_picker "
    "(all|search|by_tag|by_tool); wait before new free-form tasks."
)

LOCAL_DATA_CORE = (
    " Before large list/export (users/groups/BML/commerce/datatables): "
    "list_local_data or get_local_data_status. "
    "'use cached data'→load_local_data; 'fresh data'→sync_*_local/live."
)

LOCAL_DATA_ASK = (
    " LOCAL_DATA_POLICY=ask: if snapshot exists, offer_use_local_data then wait."
)

LOCAL_DATA_PREFER = (
    " LOCAL_DATA_POLICY=prefer: load_local_data when present; else sync/live."
)

LOCAL_DATA_NEVER = (
    " LOCAL_DATA_POLICY=never: always live/sync; still persist to data/."
)

POST_RESPONSE_EXPORT_CORE = (
    " YES-gate tabular answers: honor POST_RESPONSE_EXPORT with structured "
    "sheets [{name,columns?,rows}] — never scrape markdown. Files under "
    "data/{profile}/{env}/exports/."
)

POST_RESPONSE_EXPORT_ASK = (
    " POST_RESPONSE_EXPORT=ask: after refined step call offer_export_response; "
    "on word/both include 1–3 Mermaid diagrams for analytical answers (local mmdc)."
)

POST_RESPONSE_EXPORT_NEVER = (
    " POST_RESPONSE_EXPORT=never: do not offer or auto-export."
)

POST_RESPONSE_EXPORT_ALWAYS_EXCEL = (
    " POST_RESPONSE_EXPORT=always_excel: after YES-gate tabular + refined step, "
    "export_response_excel (do not ask)."
)

FRUGAL_MODE = (
    " ## Frugal mode (on)\n"
    "Minimize tokens. Concise answers. Default list limit≤25 unless user asks more. "
    "Prefer local cache (load_local_data). "
    "Do NOT emit refined-prompt footer; do NOT call offer_save_refined_prompt / "
    "save_refined_prompt / offer_export_response / export_response_* / "
    "ensure_prompt_studio. Prefer chat over Office; if user insists on Office, "
    "clone .config/template/ briefly. Keep credential/READ_ONLY/dry-run safety.\n"
)

ALIAS_INSTRUCTIONS_HEADER = (
    " Property aliases: map friendly phrases below to tool args (case-insensitive)."
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
            lines.append(f'- "{alias}" → process_var_name={var_name}')
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


def _format_fusion_modules_section(fusion_modules: list[str] | None) -> str:
    modules = [m.strip() for m in (fusion_modules or []) if m and str(m).strip()]
    if not modules:
        return ""
    listed = ", ".join(modules)
    extra = ""
    if "PRM" in modules:
        extra = (
            " When presenting partner custom lookup fields, call list_partner_lov to map "
            "LookupCode to Meaning/DisplayLabel — do not leave raw codes in user-facing "
            "status answers. Field PartnerProfilePEO_<suffix> → lov_name "
            "PartnerProfilePEO_LOVVA_For_<suffix>. Do not invent lov_name; if unknown, "
            "get_partner(only_data=false) and use links with rel=lov."
        )
    return (
        f" Fusion CX modules enabled on profile: {listed}. "
        "Use registered CX tools for those products (discover_tools "
        "cx_module=sales|prm|service|field_service|subscription|incentive_compensation). "
        "Do not invent REST paths for modules with no registered tools."
        f"{extra}\n"
    )


def build_server_instructions(
    *,
    refined_prompt: bool,
    auto_save_refined_prompt: bool = False,
    local_data_policy: str = "ask",
    post_response_export: str = "ask",
    frugal_mode: bool = False,
    fusion_modules: list[str] | None = None,
    shared_knowledge: str = "",
    customer_knowledge: str = "",
    commerce_process_aliases: dict[str, str] | None = None,
    custom_data_table_aliases: dict[str, str] | None = None,
    product_family_aliases: dict[str, str] | None = None,
    product_line_aliases: dict[str, str] | None = None,
    product_model_aliases: dict[str, str] | None = None,
) -> str:
    """Compose MCP instructions; frugal_mode omits token-heavy policy blocks."""
    text = (
        BASE_SERVER_INSTRUCTIONS
        + CAPABILITY_CARD
        + PROFILE_CREDENTIALS
        + AGENT_SCRATCH_FILES
        + CUSTOMER_KNOWLEDGE_MEMORY
        + _format_fusion_modules_section(fusion_modules)
    )

    if frugal_mode:
        text += FRUGAL_MODE
        text += LOCAL_DATA_CORE + LOCAL_DATA_PREFER
        text += PICKER_INSTRUCTIONS
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

    text += ASYNC_AGENT_LOOP + PICKER_INSTRUCTIONS + LOCAL_DATA_CORE
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
