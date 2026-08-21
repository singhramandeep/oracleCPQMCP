# Oracle CPQ MCP Server

MCP server for **Oracle CPQ** — exposes **Users**, **Groups**, **Data Tables**, **BML**, and **Commerce metadata** REST APIs to AI agents.

**Recommended IDE:** [Google Antigravity](https://antigravity.google/) (MCP setup partially tested). Cursor and VS Code configs are included but still need testing.

## Get started

**New here?** Follow the full walkthrough:

**[docs/QUICKSTART.md](docs/QUICKSTART.md)** — download repo, create credential profile, smoke test, and connect **Antigravity** (recommended) step by step.

**What's new?** See **[docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md)** for changelog history (auto-updated from git; refresh with `python scripts/update_release_notes.py`).

**Questions?** See **[docs/FAQ.md](docs/FAQ.md)** — setup, dual environments, security, cache, Prompt Studio, and troubleshooting.

Quick smoke test after install — run in the **IDE integrated terminal** (`` Ctrl+` ``, project root):

```bash
pip install -e ".[dev]"
```

| Shell | Copy credential template |
|-------|--------------------------|
| Windows PowerShell / CMD | `copy .config\.env.example .config\mycompany.env` |
| macOS / Linux / Git Bash | `cp .config/.env.example .config/mycompany.env` |

Edit `.config/mycompany.env`, then:

```bash
oracle-cpq-smoke --profile mycompany --env dev
python -m oracle_cpq_mcp
```

## Add MCP in Google Antigravity (recommended)

Antigravity is the **recommended** client for this server. Instructions are **partially tested**. Full detail: [QUICKSTART — Antigravity](docs/QUICKSTART.md#google-antigravity-ide-recommended).

1. Complete install, profile, and smoke test (above).
2. Open the `oracleCPQMCP` folder in Antigravity.
3. Copy the example MCP config:

| Shell | Command |
|-------|---------|
| Windows PowerShell | `mkdir .agents -Force; copy .agents\mcp_config.example.json .agents\mcp_config.json` |
| Windows CMD | `mkdir .agents && copy .agents\mcp_config.example.json .agents\mcp_config.json` |
| macOS / Linux / Git Bash | `mkdir -p .agents && cp .agents/mcp_config.example.json .agents/mcp_config.json` |

4. Edit `.agents/mcp_config.json` — Antigravity requires **absolute paths** (not `${workspaceFolder}`):

```json
{
  "mcpServers": {
    "oracle-cpq": {
      "command": "C:\\Users\\YourName\\workspaces\\oracleCPQMCP\\scripts\\mcp-server.cmd",
      "args": [],
      "cwd": "C:\\Users\\YourName\\workspaces\\oracleCPQMCP",
      "env": {
        "MCP_MODE": "stdio",
        "DISABLE_CONSOLE_OUTPUT": "true",
        "CPQ_CUSTOMER_PROFILE": "mycompany",
        "CPQ_CONFIG_DIR": "C:\\Users\\YourName\\workspaces\\oracleCPQMCP\\.config",
        "CPQ_SCHEMA_INTEGRITY": "1"
      }
    }
  }
}
```

Replace the path with your real project folder. Set `CPQ_CUSTOMER_PROFILE` to your `.config/<name>.env` profile id. On macOS/Linux use `scripts/mcp-server.sh` and `chmod +x scripts/mcp-server.sh`.

5. In Antigravity: Agent panel → **…** → **MCP Servers** → **Manage MCP Servers** (or edit `.agents/mcp_config.json` directly).
6. Restart Antigravity or reload MCP servers.
7. In Agent chat: *"Discover CPQ tools and list 5 users."*

**Required Antigravity env vars:** `MCP_MODE=stdio`, `DISABLE_CONSOLE_OUTPUT=true`, plus `CPQ_CUSTOMER_PROFILE` and `CPQ_CONFIG_DIR`. **Never put CPQ passwords in MCP JSON.**

Example file: [`.agents/mcp_config.example.json`](.agents/mcp_config.example.json). Official docs: [Antigravity MCP](https://antigravity.google/docs/mcp/).

### Other IDEs (need testing)

| IDE | Config file | Example |
|-----|-------------|---------|
| Cursor | `.cursor/mcp.json` (local, gitignored) | [`.cursor/mcp.json.example`](.cursor/mcp.json.example) / [`.cursor/mcp.json.unix.example`](.cursor/mcp.json.unix.example) |
| VS Code | `.vscode/mcp.json` (local, gitignored) | [`.vscode/mcp.json.example`](.vscode/mcp.json.example) / [`.vscode/mcp.json.unix.example`](.vscode/mcp.json.unix.example) |

These paths still need end-to-end testing on this project. Prefer Antigravity. See [docs/QUICKSTART.md](docs/QUICKSTART.md#other-ides-need-testing).

All clients use launchers: [`scripts/mcp-server.cmd`](scripts/mcp-server.cmd) (Windows) / [`scripts/mcp-server.sh`](scripts/mcp-server.sh) (macOS/Linux).
## Documentation

| Document | Contents |
|----------|----------|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | **Start here** — clone, credentials, **Antigravity MCP** (recommended), sample prompts, Prompt Studio |
| [docs/FAQ.md](docs/FAQ.md) | **FAQ** — install, dual env (dev+test), security, local cache, BML, Prompt Studio, troubleshooting |
| [docs/FEATURES.md](docs/FEATURES.md) | **Detailed features** + **security guardrails / human-in-the-loop** + Prompt Studio enable/run |
| [docs/TOOL_CATALOG.md](docs/TOOL_CATALOG.md) | Formal per-tool Parameters / Filters tables (87 tools; regenerate with `python scripts/generate_tool_catalog.py`) |
| [docs/PRE_COMMIT_REVIEW.md](docs/PRE_COMMIT_REVIEW.md) | Pre-commit secrets / catalog / test checklist |
| [docs/STANDARDS.md](docs/STANDARDS.md) | Tool authoring standards — checklist, lint, contract/eval gates |
| [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md) | Release notes — auto-updated from git via `python scripts/update_release_notes.py` |
| [docs/SETUP.md](docs/SETUP.md) | Short setup summary |
| [docs/others/AUDIT_REPORT.md](docs/others/AUDIT_REPORT.md) | Historical technical audit (archived) |
| [SECURITY.md](SECURITY.md) | Guardrails, confirmation tokens, audit |
| [SECURITY_TESTING.md](SECURITY_TESTING.md) | Security test suite and CI |
| [THREAT_MODEL.md](THREAT_MODEL.md) | STRIDE / MCP threat analysis |
| [.config/.env.example](.config/.env.example) | CPQ profile field reference |

## Features

Full product write-up (including **security guardrails and human-in-the-loop**): **[`docs/FEATURES.md`](docs/FEATURES.md)**.

- **87 MCP tools** — users, groups, data tables, BML, commerce metadata/transactions, performance logs, parts, tasks, configuration (productFamilies), tool discovery, saved refined prompts, Local `data/` sync. Formal per-tool tables: [`docs/TOOL_CATALOG.md`](docs/TOOL_CATALOG.md) (regenerate with `python scripts/generate_tool_catalog.py`).
- **Read-only by default** — profile `READ_ONLY=true` blocks all mutations
- **Safe writes** — preflight + HMAC `confirmation_token` (when writes enabled)
- **Structured errors** — `{status, code, message, hint, details}` (no stack traces)
- **Consistent output envelopes** — read/write tools return MCP object payloads (`status`, `tool`, `data`; errors use `status: error`)
- **Refined prompt footer** — after any CPQ-related task (live tools and/or local `data/` cache), agents append a copy-paste reusable prompt with title, tags, **output format** (`chat_text` / `json` / `excel_download`, default chat text), **cached data** yes/no/mixed, `{{placeholders}}`, Variables, and tool steps (`### Refined prompt (Better token usage)`). On by default; set profile `REFINED_PROMPT=false` to disable. Save via `offer_save_refined_prompt` / `save_refined_prompt` (stores `output_format`); set `AUTO_SAVE_REFINED_PROMPT=true` (or choose “save and always”) to auto-save. Pick with **`/OracleCPQ_SavedPrompts`** or **use a saved prompt** → `start_prompt_picker`. Disable entries with `set_saved_prompt_enabled`. Reload MCP after upgrades so these tools appear.
- **Local `data/` snapshots** — full users/groups/BML/commerce metadata/datatable syncs write under `data/{profile}/{env}/` (JSON + Excel, or `.bml`+JSON for BML). Policy `LOCAL_DATA_POLICY=ask|prefer|never` (default ask); tools `list_local_data`, `offer_use_local_data`, `sync_*_local`. Override root with `CPQ_LOCAL_DATA_DIR`.
- **Server-side security** — validation, rate limits, replay protection, output redaction, post-execution output schema validation

### Testing status (live CPQ)

Offline unit/contract tests cover the full catalog. Against a live CPQ site, the **scope C** additions below are **untested** for now (no Focalpoint smoke yet):

| Area | Tools | Live status |
|------|--------|-------------|
| Data tables (new) | `create_datatable`, `export_datatables` | **Untested** |
| BML (new) | `search_bml_scripts`, `list_bml_common_functions`, `get_bml_common_function`, `list_bml_library_folders`, `get_bml_dependent_attributes`, `export_bml_library_functions` | **Untested** |
| Tasks | `get_task`, `download_task_file` | **Untested** |
| Configuration | All `productFamilies` / layoutcache tools (`list_product_families` … `get_layout_cache_attributes`) | **Untested** |

Previously shipped domains (users, groups, existing datatable list/get/deploy, core BML export, commerce, performance, parts, `discover_tools`) are unchanged by this note.

## MCP tools (summary)

**87 tools** across users, groups, datatables, BML, commerce, performance, parts, tasks, configuration, and meta (including saved refined prompts and Local `data/` sync). Full input/output/tag tables: [`docs/TOOL_CATALOG.md`](docs/TOOL_CATALOG.md). Use `discover_tools(domain="users", operation="read")`, `discover_tools(domain="configuration")`, or `discover_tools(domain="tasks")` in Agent mode to filter the catalog.

Write tools default to **dry-run preflight** (`dry_run=true`). Mutations require user confirmation, `dry_run=false`, and a `confirmation_token` from preflight. Blocked when `READ_ONLY=true` (default).

BML zip export returns `[object envelope, File attachment]`. Commerce tools default `process_var_name` from `COMMERCE_PROCESS_VAR_NAME` in your profile. Async exports return a `taskId` — use `get_task` then `download_task_file` (both **untested** live).

### Users

| Tool | Type | Description |
|------|------|-------------|
| `list_users` | Read | List users across all companies on the CPQ site. Defaults to **active users only**. Returns one page (`limit`, `offset`); use `pagination.nextOffset` when `hasMore` is true. Optional `q_expr` filter and `status_filter` (`active`, `inactive`, `all`). **API:** `GET /users` |
| `get_user` | Read | Fetch a single user record by **party number** (CPQ `partyNumber`, not login name). Returns profile fields such as login, name, email, and status. **API:** `GET /users/{partyNumber}` |
| `get_user_groups` | Read | List all groups assigned to a user. Paginated — call again with increased `offset` when `hasMore` is true. **API:** `GET /users/{partyNumber}/groups` |
| `export_users_excel` | Read | Export users to a downloadable **Excel (.xlsx)** file. Auto-paginates up to 10,000 rows. Defaults to active users. Returns `[summary envelope, File attachment]`. **API:** `GET /users` (paginated internally) |
| `update_user` | Write | **Patch-update** an existing user — include only fields you intend to change in `patch_body`. Preflight validates the user exists and previews the mutation; apply with confirmation token. **API:** `PATCH /users/{partyNumber}` |

### Groups

| Tool | Type | Description |
|------|------|-------------|
| `list_groups` | Read | List groups for the configured company (`COMPANY_LOGIN_NAME` in profile, default `_host`). Paginated. **API:** `GET /companies/{company}/groups` |
| `get_group` | Read | Get metadata for one group by its **variable name** (`groupVarName`). **API:** `GET /companies/{company}/groups/{groupVarName}` |
| `list_group_users` | Read | List users who belong to a group. Paginated. **API:** `GET /companies/{company}/groups/{groupVarName}/users` |
| `create_group` | Write | Create a new group for the configured company. Requires admin permissions. Preflight previews the create; apply with confirmation token. **API:** `POST /companies/{company}/groups` |

### Data tables

| Tool | Type | Description |
|------|------|-------------|
| `list_datatables` | Read | List data tables defined on the CPQ site. Paginated. **API:** `GET /datatables` |
| `get_datatable` | Read | Get **schema/metadata** for a data table (columns, types, labels). Defaults to `CUSTOM_DATA_TABLE_NAME` from profile when `table_name` is omitted. **API:** `GET /datatables/{tableName}` |
| `get_datatable_rows` | Read | Read **deployed row data** from a custom data table. Paginated. Defaults to profile `CUSTOM_DATA_TABLE_NAME`. **API:** `GET /adminCustom{tableName}` |
| `list_datatable_fields` | Read | List field definitions for a data table. Paginated. **API:** `GET /datatables/{tableName}/fields` |
| `get_datatable_field` | Read | Get one field definition by name. **API:** `GET /datatables/{tableName}/fields/{fieldName}` |
| `deploy_datatables` | Write | **Deploy** one or more data tables to the live CPQ site — admin-only, changes production configuration. Destructive/privileged. Preflight previews; apply with confirmation token. **API:** `POST /datatables/actions/deploy` |
| `create_datatable` | Write | **Untested (live).** Create a data table. Dry-run + confirmation. **API:** `POST /datatables` |
| `export_datatables` | Write | **Untested (live).** Start a data table export task (returns `taskId`). Pair with `get_task` / `download_task_file`. Dry-run + confirmation. **API:** `POST /datatables/actions/export` |

### BML

| Tool | Type | Description |
|------|------|-------------|
| `get_all_bml_code` | Read | Download or retrieve **BML source code**. `delivery='zip'` (default) exports all Commerce BML and BMLT files via `GET /adminMeta` — equivalent to **cpq-toolkit pull** — and returns a zip `File` attachment. `delivery='json'` returns util library functions with inline `scriptText` (paginated `/bml/library/functions` fetch). Requires admin permissions. |
| `get_bml_function` | Read | Get one util library BML function by id (includes `scriptText` when available). **API:** `GET /bml/library/functions/{id}` |
| `search_bml_scripts` | Read | **Untested (live).** Search BML scripts. **API:** `GET /bml/scripts` |
| `list_bml_common_functions` | Read | **Untested (live).** List built-in BML common functions. **API:** `GET /bml/common/functions` |
| `get_bml_common_function` | Read | **Untested (live).** Get one common function by name. **API:** `GET /bml/common/functions/{name}` |
| `list_bml_library_folders` | Read | **Untested (live).** List util library folders. **API:** `GET /bml/library/folders` |
| `get_bml_dependent_attributes` | Read | **Untested (live).** Attributes referenced by util library functions (read-like POST; allowed under `READ_ONLY`). **API:** `POST /bml/library/functions/actions/dependentAttributes` |
| `export_bml_library_functions` | Write | **Untested (live).** Export util library functions (returns `taskId`). Dry-run + confirmation. **API:** `POST /bml/library/functions/actions/export` |

### Commerce metadata

Read-only metadata for Commerce process documents. All tools default `process_var_name` from profile (`COMMERCE_PROCESS_VAR_NAME`) and accept optional `doc_var_name` and `expand_all` (include translations via `expand=all*`).

| Tool | Type | Description |
|------|------|-------------|
| `get_commerce_attributes` | Read | List **attribute definitions** on a Commerce **main document** (default `doc_var_name='transaction'`). Names, types, constraints, display metadata. **API:** `GET /commerceProcesses/{process}/documents/{doc}/attributes` |
| `get_commerce_actions` | Read | List **action definitions** on a Commerce **main document** (default `transaction`). **API:** `GET /commerceProcesses/{process}/documents/{doc}/actionDefs` |
| `get_commerce_attribute` | Read | Get one attribute definition by `attribute_var_name`. **API:** `GET .../attributes/{attributeVarName}` |
| `get_commerce_action` | Read | Get one action definition by `action_var_name`. **API:** `GET .../actionDefs/{actionVarName}` |
| `list_commerce_processes` | Read | List Commerce process setups (admin). Paginated. **API:** `GET /commerceProcessSetups` |
| `get_line_attributes` | Read | List **attribute definitions** on a Commerce **line document** (default `doc_var_name='transactionLine'`). **API:** `GET /commerceProcesses/{process}/documents/{doc}/attributes` |
| `get_line_actions` | Read | List **action definitions** on a Commerce **line document** (default `transactionLine`). **API:** `GET /commerceProcesses/{process}/documents/{doc}/actionDefs` |

### Commerce transactions

Live Commerce **document** APIs (path built as `/commerceDocuments{Process}{Doc}` from `COMMERCE_PROCESS_VAR_NAME`). Writes use dry-run preflight + confirmation.

| Tool | Type | Description |
|------|------|-------------|
| `list_transactions` | Read | List transactions (paginated; `q_expr`, `fields`, `orderby`, `expand`, …). **API:** `GET /commerceDocuments{Process}{Doc}` |
| `get_transaction` | Read | Get one transaction by numeric `transaction_id`. **API:** `GET .../{id}` |
| `list_transaction_lines` | Read | List lines for a transaction (paginated). **API:** `GET .../{id}/transactionLine` |
| `get_transaction_line` | Read | Get one line by `transaction_id` + `document_number`. **API:** `GET .../{id}/transactionLine/{documentNumber}` |
| `get_document_layout` | Read | Desktop layout definition for a process document. **API:** `GET /commerceProcesses/{process}/layouts/{doc}` |
| `generate_proposal` | Write | Generate proposal for a transaction. **API:** `POST .../actions/generateProposal` |
| `export_attachment` | Write | Export/view a CPQ-generated transaction attachment. Requires `attribute_var_name` (sent as `selections`); optional `action_var_name` (default `exportAttachment`). JSON response, not file bytes. **API:** `POST .../actions/{actionVarName}` |
| `download_attachment` | Read | Download attachment file bytes from a transaction attribute's `fileLocation`. Returns `[envelope, File]`. **API:** `GET` relative path from `fileLocation` |
| `copy_transaction` | Write | Copy a transaction. **API:** `POST .../actions/_copy_transaction` |
| `copy_transaction_lines` | Write | Copy lines onto a transaction (default action `copyLineItems_t`). **API:** `POST .../actions/{actionName}` |

### Performance logs

Access to CPQ **performance log events** (user activity timing / metrics). Collection filters mirror the REST API: `limit`, `offset`, `total_results`, `q_expr` (MongoDB `q`), `fields`, `orderby`.

| Tool | Type | Description |
|------|------|-------------|
| `list_performance_logs` | Read | List performance log events (one page). Use `pagination.nextOffset` when `hasMore` is true. **API:** `GET /performanceLogs` |
| `get_performance_log` | Read | Get one event by numeric `log_id`. **API:** `GET /performanceLogs/{id}` |
| `export_performance_logs` | Write | Export performance logs (optional `log_id`). Dry-run + confirmation. **API:** `POST /performanceLogs[/id]/actions/export` |

### Parts

| Tool | Type | Description |
|------|------|-------------|
| `list_parts` | Read | List parts (paginated). **API:** `GET /parts` |
| `get_part` | Read | Get one part by id. **API:** `GET /parts/{id}` |
| `search_parts` | Read | Search parts with a JSON body. Allowed under `READ_ONLY`. **API:** `POST /parts/actions/search` |

### Tasks

Async task APIs used after export actions. **Entire domain untested against live CPQ.**

| Tool | Type | Description |
|------|------|-------------|
| `get_task` | Read | **Untested (live).** Get async task status (e.g. after export). **API:** `GET /tasks/{taskId}` |
| `download_task_file` | Read | **Untested (live).** Download a task output file. Returns `[envelope, File]`. **API:** `GET /tasks/{taskId}/files/{fileName}` |

### Configuration

Product family hierarchy and layout cache. Scoped tools use `scope: family \| line \| model` plus the required var-name path args. **Entire domain untested against live CPQ.**

| Tool | Type | Description |
|------|------|-------------|
| `list_product_families` / `get_product_family` | Read | **Untested (live).** Product family metadata. **API:** `GET /productFamilies[/{prodFamVarName}]` |
| `list_product_lines` / `get_product_line` | Read | **Untested (live).** Lines under a family. **API:** `GET .../productLines` |
| `list_models` / `get_model` | Read | **Untested (live).** Models under a line. **API:** `GET .../models` |
| `list_config_attributes` / `get_config_attribute` | Read | **Untested (live).** Attributes at family/line/model scope. |
| `list_array_sets` / `get_array_set` | Read | **Untested (live).** Array sets at scope. |
| `list_array_set_attributes` / `get_array_set_attribute` | Read | **Untested (live).** Attributes of an array set. |
| `list_config_menu_items` / `get_config_menu_item` | Read | **Untested (live).** Menu items (`parent_kind`: attribute or array_set_attribute). |
| `get_config_layout` | Read | **Untested (live).** Layout by `layout_var_name` at scope. |
| `get_layout_cache_attributes` | Read | **Untested (live).** **API:** `GET /layoutcache/{fam}/{line}/{model}/attributes` |

### Meta

| Tool | Type | Description |
|------|------|-------------|
| `discover_tools` | Read | Search and filter this server's tool catalog by **domain** (`users` / `groups` / `datatables` / `bml` / `commerce` / `performance` / `parts` / `tasks` / `configuration`), **operation** (`read` / `write`), or free-text query. Use before calling tools to find read-only vs write capabilities, HTTP methods, and API paths. Does not call CPQ. |
| `list_saved_prompts` / `search_saved_prompts` / `get_saved_prompt` | Read | Local saved refined-prompt library (`.config/saved_prompts.json`). |
| `offer_save_refined_prompt` / `save_refined_prompt` / `record_prompt_use` | Read* | Offer/save/update local refined prompts (*local file only, not CPQ). |
| `set_auto_save_refined_prompt` | Read* | Write `AUTO_SAVE_REFINED_PROMPT` on the active profile `.env` (*local only). |
| `set_saved_prompt_enabled` | Read* | Enable/disable a saved prompt (disabled ones are hidden from pickers). |
| `start_prompt_picker` | Read | Interactive pick: all / search / by tag / by tool (`/OracleCPQ_SavedPrompts`). |
| `list_local_data` / `get_local_data_status` / `load_local_data` | Read* | Inspect local `data/{profile}/{env}` snapshots (*disk only, not CPQ). |
| `offer_use_local_data` / `set_local_data_policy` | Read* | Ask cache vs fresh; write `LOCAL_DATA_POLICY` on the profile `.env`. |

Also exposes MCP resource `cpq://saved-prompts` and prompt `run_saved_prompt`. Domain sync tools (`sync_users_local`, `sync_groups_local`, `sync_bml_local`, `sync_commerce_metadata_local`, `sync_datatable_local` / `sync_datatables_local`) write full collections under `data/`.

<details>
<summary><strong>Configuration reference</strong></summary>

### Profile env (`.config/<customer>.env`)

| Variable | Description |
|----------|-------------|
| `CPQ_CUSTOMER_PROFILE` | Profile file name without `.env` (set in MCP config) |
| `CPQ_ENVIRONMENT` | Override default: `dev`, `test`, `prod` |
| `READ_ONLY` | Default `true` — blocks create/update/delete |
| `REFINED_PROMPT` | Default `true` — append refined-prompt footer after CPQ-related tasks (live and/or local cache) |
| `AUTO_SAVE_REFINED_PROMPT` | Default `false` — when true, auto-save refined prompts; when false, agent asks |
| `LOCAL_DATA_POLICY` | Default `ask` — `ask` / `prefer` / `never` for using `data/` snapshots before live CPQ |
| `CPQ_LOCAL_DATA_DIR` | Optional override for local snapshot root (default `<repo>/data`) |
| `CPQ_SAVED_PROMPTS_PATH` | Optional override for saved refined-prompt library JSON |
| `DEV_URL`, `DEV_USERNAME`, `DEV_PASSWORD` | Dev CPQ credentials |
| `REST_API_VERSION` | e.g. `v18` |
| `CUSTOM_DATA_TABLE_NAME` | Default table for smoke test / datatable tools |
| `COMMERCE_PROCESS_VAR_NAME` | Commerce process variable for metadata tools (e.g. `oraclecpqo`) |

See [.config/.env.example](.config/.env.example) for all fields.

### Host env (MCP JSON — not in profile file)

| Variable | Default | Purpose |
|----------|---------|---------|
| `CPQ_CONFIRMATION_SECRET` | — | Required when writes enabled |
| `CPQ_SCHEMA_INTEGRITY` | `1` | Verify tool manifest at startup |
| `CPQ_ALLOW_PROD` | unset | Must be `1` for prod |
| `CPQ_MAX_TOOL_CALLS` | `20` | Session tool call cap |
| `CPQ_VERBOSE` | off | Redacted request/curl logging |

</details>

<details>
<summary><strong>Tool output envelopes</strong></summary>

All dict-returning tools emit a **single MCP object** (required by the MCP/FastMCP output schema):

| Shape | Fields |
|-------|--------|
| Success | `{ "status": "ok", "tool": "<name>", "data": { ... }, "pagination": { ... }? }` |
| Error | `{ "status": "error", "code": "...", "message": "...", "hint": "...", "details": { ... }? }` |
| Write preflight | `{ "status": "preflight_ok" \| "confirmation_required" \| ..., "tool": "<name>", "data": { ... } }` |

Export/BML tools return a **list**: `[object envelope, File attachment]`. The object envelope uses `data.message` (and optional `data.filename`).

Implementation: `core/responses.py` (`wrap_tool_success`) + `schemas/tool_outputs.py` (MCP JSON Schema registration).

</details>

<details>
<summary><strong>Safe execution (write tools)</strong></summary>

1. **Preflight** (`dry_run=true`, default) — validates inputs, returns `confirmation_token`
2. **User approval** — agent asks you to confirm
3. **Apply** — `dry_run=false` + `confirmation_token` from preflight

Blocked entirely when `READ_ONLY=true` (default).

</details>

<details>
<summary><strong>Pagination</strong></summary>

List tools return one page per call (`limit`, `offset`, `hasMore`, `totalResults`). Use `pagination.nextOffset` in the response for the next page. For full user export use `export_users_excel` (auto-paginates, cap 10,000 rows).

[Oracle CPQ pagination docs](https://docs.oracle.com/en/cloud/saas/configure-price-quote/cxcpq/Paginate.html)

</details>

<details>
<summary><strong>IDE configuration files (reference)</strong></summary>

| IDE | Status | Config file | Example in repo |
|-----|--------|-------------|-----------------|
| **Antigravity** | **Recommended** (partially tested) | `.agents/mcp_config.json` | [`.agents/mcp_config.example.json`](.agents/mcp_config.example.json) |
| Cursor | Needs testing | `.cursor/mcp.json` | [`.cursor/mcp.json.example`](.cursor/mcp.json.example) |
| VS Code | Needs testing | `.vscode/mcp.json` | [`.vscode/mcp.json.example`](.vscode/mcp.json.example) |

See [Add MCP in Google Antigravity](#add-mcp-in-google-antigravity-recommended) above and [docs/QUICKSTART.md](docs/QUICKSTART.md).

</details>

## Development

**IDE terminal** (repo root, venv activated):

```bash
pip install -e ".[dev]"
pytest
```

### Prompt Studio (local)

Browse/search/favorites/suites and fill `{{placeholders}}` against `.config/saved_prompts.json`:

```powershell
.\.venv\Scripts\python.exe -m pip install '.[prompt-studio]'
.\.venv\Scripts\python.exe -m apps.prompt_studio
```

Then open [http://127.0.0.1:8765](http://127.0.0.1:8765). Details: [`apps/prompt_studio/README.md`](apps/prompt_studio/README.md) and [`docs/FEATURES.md`](docs/FEATURES.md#prompt-studio-enable-and-run).

## Project structure

```
mcp/oracle_cpq_mcp/   # MCP server package
  core/               # Config, CPQClient, errors, preflight
  security/           # Policy, validation, confirmation, audit
  tools/              # MCP tool handlers
  registry/           # Tool catalog
apps/prompt_studio/   # Local Prompt Studio (FastAPI + static UI)
.config/              # Customer profiles (*.env gitignored)
scripts/              # mcp-server.cmd / mcp-server.sh launchers
.agents/              # Antigravity MCP example (local mcp_config.json not committed)
.cursor/              # Cursor MCP examples only (local mcp.json gitignored)
docs/                 # QUICKSTART, SETUP, security review
tests/                # Unit + security tests
```

## Security & git

- **Never commit** `.agents/mcp_config.json`, `.cursor/mcp.json`, `.config/*.env`, `saved_prompts.json`, `prompt_studio.json`, or `data/` — see [.gitignore](.gitignore)
- **Never put passwords** in MCP config JSON
- Guardrails + HITL writes: [`docs/FEATURES.md`](docs/FEATURES.md#security-guardrails-and-human-in-the-loop) and [`SECURITY.md`](SECURITY.md)
- Pre-commit checklist: [`docs/PRE_COMMIT_REVIEW.md`](docs/PRE_COMMIT_REVIEW.md)

## Remote MCP (future)

Local stdio works with desktop IDEs today. Cloud clients (ChatGPT, Gemini) need HTTPS + Streamable HTTP — see Phase 2 notes in [docs/SETUP.md](docs/SETUP.md).

## License

Internal / project-specific — see repository settings.
