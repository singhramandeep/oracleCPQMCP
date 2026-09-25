# Oracle CPQ MCP - Tool Catalog

> **Auto-generated.** Do not edit by hand.
> Regenerate with:
>
> ```bash
> python scripts/generate_tool_catalog.py
> ```

**Total tools:** 122

This document is the formal per-tool reference for the GitHub repository. Each row is one MCP tool function with **Parameters** and **Filters** (from Pydantic validation models), output contract, tags, and API metadata from `TOOL_CATALOG`.

## Domains

- [users](#users)
- [groups](#groups)
- [datatables](#datatables)
- [bml](#bml)
- [commerce](#commerce)
- [performance](#performance)
- [parts](#parts)
- [tasks](#tasks)
- [configuration](#configuration)
- [meta](#meta)
- [admin](#admin)
- [collab](#collab)
- [metrics](#metrics)

## users

_6 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `export_users_excel` | `1.2.0` | `read` | `PRIVILEGED` | `excel`, `export`, `local_data`, `read`, `users` | GET /users | `columns` (list[str] \| None, default None) | `status_filter` (Literal['active', 'inactive', 'all'], default 'active'); `q_expr` (str \| None, default None) | attachment/list (no root object schema) |
| `get_user` | `1.0.0` | `read` | `READ_ONLY` | `read`, `users` | GET /users/{partyNumber} | `party_number` (str, required) | - | read envelope `{status, tool, data}` |
| `get_user_groups` | `1.0.0` | `read` | `READ_ONLY` | `groups`, `paginated`, `read`, `users` | GET /users/{partyNumber}/groups | `party_number` (str, required); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `list_users` | `1.0.0` | `read` | `READ_ONLY` | `paginated`, `read`, `users` | GET /users | `limit` (int, default 100); `offset` (int, default 0) | `status_filter` (Literal['active', 'inactive', 'all'], default 'active'); `q_expr` (str \| None, default None) | read envelope `{status, tool, data}` |
| `sync_users_local` | `1.1.0` | `read` | `PRIVILEGED` | `excel`, `export`, `local_data`, `read`, `users` | GET /users | `columns` (list[str] \| None, default None) | `status_filter` (Literal['active', 'inactive', 'all'], default 'active'); `q_expr` (str \| None, default None) | read envelope `{status, tool, data}` |
| `update_user` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `confirmation`, `dry_run`, `users`, `write` | PATCH /users/{partyNumber} | `party_number` (str, required); `patch_body` (dict[str, Any], required); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |

### Descriptions

- **`export_users_excel`** — Export CPQ users to an Excel (.xlsx) file. Defaults to active users only. Also writes users.json + users.xlsx under data/{profile}/{env}/users/.
- **`get_user`** — Get a single user by party number.
- **`get_user_groups`** — List all groups assigned to a user. Returns one page of results. If hasMore is true, call again with offset = offset + limit.
- **`list_users`** — List users across all companies on the CPQ site. Defaults to active users only. Returns one page of results. If hasMore is true, call again with offset = offset + limit. Use export_users_excel for a full Excel export.
- **`sync_users_local`** — Fetch all CPQ users (paginated) and write data/{profile}/{env}/users/ (users.json + users.xlsx + manifest.json). Prefer this for a complete local cache. Defaults to active users only.
- **`update_user`** — Patch-update an existing user. Only include fields you intend to change. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview stating this w…

## groups

_5 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `create_group` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `confirmation`, `dry_run`, `groups`, `write` | POST /companies/{company}/groups | `group_body` (dict[str, Any], required); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `get_group` | `1.0.0` | `read` | `READ_ONLY` | `groups`, `read` | GET /companies/{company}/groups/{groupVarName} | `group_var_name` (str, required) | - | read envelope `{status, tool, data}` |
| `list_group_users` | `1.0.0` | `read` | `READ_ONLY` | `groups`, `paginated`, `read`, `users` | GET /companies/{company}/groups/{groupVarName}/users | `group_var_name` (str, required); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `list_groups` | `1.0.0` | `read` | `READ_ONLY` | `groups`, `paginated`, `read` | GET /companies/{company}/groups | `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `sync_groups_local` | `1.1.0` | `read` | `PRIVILEGED` | `excel`, `export`, `groups`, `local_data`, `read` | GET /companies/{company}/groups | - | - | read envelope `{status, tool, data}` |

### Descriptions

- **`create_group`** — Create a new group for the configured company. Requires admin permissions. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview stating this…
- **`get_group`** — Get details for a single group by its variable name.
- **`list_group_users`** — List users that belong to a group. Returns one page of results. If hasMore is true, call again with offset = offset + limit.
- **`list_groups`** — List groups for the configured company (defaults to host company `_host`). Returns one page of results. If hasMore is true, call again with offset = offset + limit.
- **`sync_groups_local`** — Fetch all company groups (paginated) and write data/{profile}/{env}/groups/ (groups.json + groups.xlsx + manifest.json).

## datatables

_10 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `create_datatable` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `admin`, `confirmation`, `datatables`, `dry_run`, `write` | POST /datatables | `body` (dict[str, Any], required); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `deploy_datatables` | `1.0.0` | `write` | `DESTRUCTIVE` | `admin`, `confirmation`, `datatables`, `dry_run`, `write` | POST /datatables/actions/deploy | `table_names` (list[str], required); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `export_datatables` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `admin`, `confirmation`, `datatables`, `dry_run`, `export`, `write` | POST /datatables/actions/export | `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `get_datatable` | `1.0.0` | `read` | `READ_ONLY` | `datatables`, `read` | GET /datatables/{tableName} | `table_name` (str \| None, default None) | - | read envelope `{status, tool, data}` |
| `get_datatable_field` | `1.0.0` | `read` | `READ_ONLY` | `datatables`, `read` | GET /datatables/{tableName}/fields/{fieldName} | `field_name` (str, required); `table_name` (str \| None, default None) | - | read envelope `{status, tool, data}` |
| `get_datatable_rows` | `1.0.0` | `read` | `READ_ONLY` | `datatables`, `paginated`, `read` | GET /adminCustom{tableName} | `table_name` (str \| None, default None); `limit` (int, default 50); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `list_datatable_fields` | `1.0.0` | `read` | `READ_ONLY` | `datatables`, `paginated`, `read` | GET /datatables/{tableName}/fields | `table_name` (str \| None, default None); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `list_datatables` | `1.0.0` | `read` | `READ_ONLY` | `datatables`, `paginated`, `read` | GET /datatables | `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `sync_datatable_local` | `1.1.0` | `read` | `PRIVILEGED` | `datatables`, `excel`, `export`, `local_data`, `read` | GET /datatables/{name} | `table_name` (str \| None, default None) | - | read envelope `{status, tool, data}` |
| `sync_datatables_local` | `1.0.0` | `read` | `PRIVILEGED` | `datatables`, `excel`, `export`, `local_data`, `read` | GET /datatables/{name} | `table_names` (list[str] \| None, default None) | - | read envelope `{status, tool, data}` |

### Descriptions

- **`create_datatable`** — Create a new data table via POST /datatables. Requires name; optional description, folder, fields, isLive. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs…
- **`deploy_datatables`** — Deploy one or more data tables. Admin-only — changes live CPQ configuration. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview stating th…
- **`export_datatables`** — Start a data table export task via POST /datatables/actions/export. Returns taskId; poll with get_task and download with download_task_file. Safe execution: defaults to dry_run=true (preflight only — validates inputs, c…
- **`get_datatable`** — Get metadata/properties for a data table. Defaults to the first CUSTOM_DATA_TABLE_NAME from profile (supports CUSTOM_DATA_TABLE_NAME_1, _2, etc.).
- **`get_datatable_field`** — Get one data table field definition by field name. Defaults table_name from profile.
- **`get_datatable_rows`** — Get rows from a deployed data table. Defaults to the first CUSTOM_DATA_TABLE_NAME from profile (supports _1, _2 suffixes). Returns one page of results. If hasMore is true, call again with offset = offset + limit.
- **`list_datatable_fields`** — List field definitions for a data table. Defaults table_name from profile. Returns one page of results. If hasMore is true, call again with offset = offset + limit.
- **`list_datatables`** — List data tables defined on the CPQ site. Returns one page of results. If hasMore is true, call again with offset = offset + limit.
- **`sync_datatable_local`** — Fetch one data table meta + all rows and write data/{profile}/{env}/datatables/{name}/ (meta.json, rows.json, rows.xlsx).
- **`sync_datatables_local`** — Sync one or more data tables locally. Defaults to all CUSTOM_DATA_TABLE_NAME* values from the profile.

## bml

_11 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `export_bml_library_functions` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `bml`, `confirmation`, `dry_run`, `export`, `write` | POST /bml/library/functions/actions/export | `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `get_all_bml_code` | `1.4.0` | `read` | `PRIVILEGED` | `admin`, `bml`, `export`, `local_data`, `read` | GET /adminMeta | `delivery` (Literal['zip', 'json'], default 'zip') | - | attachment/list (no root object schema) |
| `get_bml_common_function` | `1.0.0` | `read` | `READ_ONLY` | `bml`, `read` | GET /bml/common/functions/{name} | `name` (str, required) | - | read envelope `{status, tool, data}` |
| `get_bml_dependent_attributes` | `1.0.0` | `read` | `READ_ONLY` | `bml`, `read` | POST /bml/library/functions/actions/dependentAttributes | `body` (dict[str, Any] \| None, default None) | - | read envelope `{status, tool, data}` |
| `get_bml_function` | `1.0.0` | `read` | `READ_ONLY` | `bml`, `read` | GET /bml/library/functions/{namespace.variableName} | `function_id` (str, required) | - | read envelope `{status, tool, data}` |
| `list_bml_common_functions` | `1.0.0` | `read` | `READ_ONLY` | `bml`, `read` | GET /bml/common/functions | `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `list_bml_library_folders` | `1.0.0` | `read` | `READ_ONLY` | `bml`, `read` | GET /bml/library/folders | `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `search_bml_scripts` | `1.0.0` | `read` | `READ_ONLY` | `bml`, `paginated`, `read`, `search` | GET /bml/scripts | `limit` (int, default 100); `offset` (int, default 0); `orderby` (str \| None, default None); `fields` (list[str] \| None, default None) | `q_expr` (str \| None, default None) | read envelope `{status, tool, data}` |
| `search_local_bml` | `1.0.0` | `read` | `READ_ONLY` | `bml`, `local_data`, `read`, `search` | — | `max_matches` (int, default 50); `case_insensitive` (bool, default True); `include_functions` (bool, default True) | `query` (str, required) | read envelope `{status, tool, data}` |
| `start_bml_site_export` | `1.0.0` | `read` | `READ_ONLY` | `async`, `bml`, `export`, `local_data`, `read` | GET /adminMeta | - | - | read envelope `{status, tool, data}` |
| `sync_bml_local` | `1.1.0` | `read` | `PRIVILEGED` | `bml`, `export`, `local_data`, `read` | GET /bml/library/functions | - | - | read envelope `{status, tool, data}` |

### Descriptions

- **`export_bml_library_functions`** — Export util library functions via POST .../actions/export. Returns taskId; use get_task and download_task_file. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only…
- **`get_all_bml_code`** — Download or retrieve BML source code from the CPQ site (synchronous — blocks the MCP tool call until done). delivery='zip' (default) exports all Commerce BML and BMLT files via GET /adminMeta — equivalent to cpq-toolkit…
- **`get_bml_common_function`** — Get one BML common function by name via GET /bml/common/functions/{name}.
- **`get_bml_dependent_attributes`** — Return attributes referenced by util library functions via POST /bml/library/functions/actions/dependentAttributes. Read-like; allowed under READ_ONLY.
- **`get_bml_function`** — Get one util library BML function by function_id (namespace.variableName). Does not export full site zip.
- **`list_bml_common_functions`** — List built-in BML common functions (atoi, len, etc.) via GET /bml/common/functions.
- **`list_bml_library_folders`** — List util library folders via GET /bml/library/folders.
- **`search_bml_scripts`** — Search BML scripts containing a string via GET /bml/scripts. Supports q_expr, limit, offset, orderby, fields.
- **`search_local_bml`** — Search text across extracted local BML files under data/{profile}/{env}/bml/site/ (and util library .bml under bml/functions/). Does not call Oracle CPQ. Use after get_all_bml_code or start_bml_site_export has populated…
- **`start_bml_site_export`** — Start a background MCP-local job that downloads the full Commerce BML/BMLT site zip (GET /adminMeta), persists under data/{profile}/{env}/bml/, and extracts to bml/site/. Returns immediately with job_id. Poll with get_l…
- **`sync_bml_local`** — Fetch all util library BML functions with scriptText and write data/{profile}/{env}/bml/ (library.json + functions/**/*.bml + **/*.json).

## commerce

_38 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `add_from_favorites` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName} | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None); `action_var_name` (str, default '_s_addFromFavorites_t') | - | write envelope `{status, tool, data}` |
| `add_transaction_lines` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `lines`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName} | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None); `action_var_name` (str, default 'addLineItem_t') | - | write envelope `{status, tool, data}` |
| `copy_transaction` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/_copy_transaction | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `copy_transaction_lines` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `lines`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/{actionName} | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `action_name` (str, default 'copyLineItems_t'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `create_transaction` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc} | `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `create_transaction_version` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName} | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None); `action_var_name` (str, default 'versionTransaction_t') | - | write envelope `{status, tool, data}` |
| `delete_transaction_line` | `1.0.0` | `write` | `DESTRUCTIVE` | `commerce`, `confirmation`, `dry_run`, `lines`, `transactions`, `write` | DELETE /commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber} | `transaction_id` (str, required); `document_number` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `display_transaction_history` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName} | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None); `action_var_name` (str, required) | - | write envelope `{status, tool, data}` |
| `download_attachment` | `1.0.0` | `read` | `READ_ONLY` | `attachments`, `commerce`, `read`, `transactions` | GET attachment fileLocation | `transaction_id` (str, required); `attribute_var_name` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `document_number` (str, default '1') | - | attachment/list (no root object schema) |
| `export_attachment` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName} | `transaction_id` (str, required); `attribute_var_name` (str, required); `action_var_name` (str, default 'exportAttachment'); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `generate_proposal` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/generateProposal | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `get_commerce_action` | `1.0.0` | `read` | `READ_ONLY` | `actions`, `commerce`, `metadata`, `read` | GET /commerceProcesses/{processVarName}/documents/{docVarName}/actionDefs/{actionVarName} | `action_var_name` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `expand_all` (bool, default False) | - | read envelope `{status, tool, data}` |
| `get_commerce_actions` | `1.0.0` | `read` | `READ_ONLY` | `actions`, `commerce`, `metadata`, `paginated`, `read` | GET /commerceProcesses/{processVarName}/documents/{docVarName}/actionDefs | `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `expand_all` (bool, default False); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `get_commerce_attribute` | `1.0.0` | `read` | `READ_ONLY` | `attributes`, `commerce`, `metadata`, `read` | GET /commerceProcesses/{processVarName}/documents/{docVarName}/attributes/{attributeVarName} | `attribute_var_name` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `expand_all` (bool, default False) | - | read envelope `{status, tool, data}` |
| `get_commerce_attributes` | `1.0.0` | `read` | `READ_ONLY` | `attributes`, `commerce`, `metadata`, `paginated`, `read` | GET /commerceProcesses/{processVarName}/documents/{docVarName}/attributes | `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `expand_all` (bool, default False); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `get_commerce_ui_settings` | `1.0.0` | `read` | `READ_ONLY` | `commerce`, `read`, `settings`, `ui` | GET /commerceUISettings | - | - | read envelope `{status, tool, data}` |
| `get_document_layout` | `1.0.0` | `read` | `READ_ONLY` | `commerce`, `layout`, `metadata`, `read` | GET /commerceProcesses/{processVarName}/layouts/{mainDocVarName} | `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction') | - | read envelope `{status, tool, data}` |
| `get_line_actions` | `1.0.0` | `read` | `READ_ONLY` | `actions`, `commerce`, `line`, `metadata`, `paginated`, `read` | GET /commerceProcesses/{processVarName}/documents/{docVarName}/actionDefs | `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transactionLine'); `expand_all` (bool, default False); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `get_line_attributes` | `1.0.0` | `read` | `READ_ONLY` | `attributes`, `commerce`, `line`, `metadata`, `paginated`, `read` | GET /commerceProcesses/{processVarName}/documents/{docVarName}/attributes | `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transactionLine'); `expand_all` (bool, default False); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `get_saved_search` | `1.0.0` | `read` | `READ_ONLY` | `commerce`, `read`, `saved_search` | GET /searchResources/{resourceVarName}/{searchId} | `search_id` (int, required); `resource_var_name` (str \| None, default None); `process_var_name` (str \| None, default None) | - | read envelope `{status, tool, data}` |
| `get_transaction` | `1.0.0` | `read` | `READ_ONLY` | `commerce`, `read`, `transactions` | GET /commerceDocuments{Process}{Doc}/{id} | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `expand` (str \| None, default None); `exclude_field_types` (str \| None, default None) | - | read envelope `{status, tool, data}` |
| `get_transaction_line` | `1.0.0` | `read` | `READ_ONLY` | `commerce`, `lines`, `read`, `transactions` | GET /commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber} | `transaction_id` (str, required); `document_number` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `expand` (str \| None, default None); `exclude_field_types` (str \| None, default None) | - | read envelope `{status, tool, data}` |
| `interact_transaction_line` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `lines`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}/actions/_interact | `transaction_id` (str, required); `document_number` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `list_commerce_processes` | `1.0.0` | `read` | `READ_ONLY` | `commerce`, `metadata`, `paginated`, `read` | GET /commerceProcessSetups | `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `list_commerce_processes_table` | `1.0.0` | `read` | `READ_ONLY` | `commerce`, `metadata`, `read`, `table` | GET /commerceProcessSetups | `page_size` (int, default 100) | - | read envelope `{status, tool, data}` |
| `list_saved_searches` | `1.0.0` | `read` | `READ_ONLY` | `commerce`, `paginated`, `read`, `saved_search` | GET /searchResources/{resourceVarName} | `resource_var_name` (str \| None, default None); `process_var_name` (str \| None, default None); `show_all` (Literal['ALL', 'HIDDEN', 'VISIBLE', 'INACTIVE'], default 'VISIBLE'); `limit` (int, default 100); `offset` (int, default 0); `total_results` (bool, default True) | - | read envelope `{status, tool, data}` |
| `list_transaction_lines` | `1.0.0` | `read` | `READ_ONLY` | `commerce`, `lines`, `paginated`, `read`, `transactions` | GET /commerceDocuments{Process}{Doc}/{id}/transactionLine | `limit` (int, default 100); `offset` (int, default 0); `total_results` (bool, default True); `fields` (list[str] \| None, default None); `orderby` (list[str] \| None, default None); `expand` (str \| None, default None); `exclude_field_types` (str \| None, default None); `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction') | `q_expr` (str \| None, default None) | read envelope `{status, tool, data}` |
| `list_transactions` | `1.0.0` | `read` | `READ_ONLY` | `commerce`, `paginated`, `read`, `transactions` | GET /commerceDocuments{Process}{Doc} | `limit` (int, default 100); `offset` (int, default 0); `total_results` (bool, default True); `fields` (list[str] \| None, default None); `orderby` (list[str] \| None, default None); `expand` (str \| None, default None); `exclude_field_types` (str \| None, default None); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction') | `q_expr` (str \| None, default None) | read envelope `{status, tool, data}` |
| `new_transaction` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/actions/_new_transaction | `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `reconfigure_transaction` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/_reconfigure_action | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `reconfigure_transaction_line` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `lines`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}/actions/_reconfigure_action | `transaction_id` (str, required); `document_number` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `reconfigure_transaction_line_inbound` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `lines`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}/actions/_reconfigure_inbound_action | `transaction_id` (str, required); `document_number` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `remove_transaction_lines` | `1.0.0` | `write` | `DESTRUCTIVE` | `commerce`, `confirmation`, `dry_run`, `lines`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/_remove_transactionLine | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `save_transaction` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName} | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None); `action_var_name` (str, default 'cleanSave_t') | - | write envelope `{status, tool, data}` |
| `save_transaction_version` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName} | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None); `action_var_name` (str, default 'versionSave_t') | - | write envelope `{status, tool, data}` |
| `submit_transaction` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName} | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None); `action_var_name` (str, default 'submit_t') | - | write envelope `{status, tool, data}` |
| `sync_commerce_metadata_local` | `1.1.0` | `read` | `PRIVILEGED` | `commerce`, `excel`, `export`, `local_data`, `read` | GET /commerceProcesses/{process}/documents/{doc}/{resource} | `process_var_name` (str \| None, default None); `expand_all` (bool, default True) | - | read envelope `{status, tool, data}` |
| `update_transaction_lines` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `commerce`, `confirmation`, `dry_run`, `lines`, `transactions`, `write` | POST /commerceDocuments{Process}{Doc}/{id}/actions/_update_line_items | `transaction_id` (str, required); `process_var_name` (str \| None, default None); `doc_var_name` (str, default 'transaction'); `body` (dict[str, Any] \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |

### Descriptions

- **`add_from_favorites`** — Add favorites onto a Commerce transaction (POST .../actions/{action_var_name}; default _s_addFromFavorites_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only…
- **`add_transaction_lines`** — Add line items to a Commerce transaction (POST .../actions/{action_var_name}; default addLineItem_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, ret…
- **`copy_transaction`** — Copy a Commerce transaction (POST .../actions/_copy_transaction). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview stating this will UPD…
- **`copy_transaction_lines`** — Copy transaction lines onto a Commerce transaction (POST .../actions/{action_name}; default action_name=copyLineItems_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via…
- **`create_transaction`** — Create a Commerce transaction/quote (POST /commerceDocuments{Process}{Doc}). Pass documents/attributes in body as required by the site. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks…
- **`create_transaction_version`** — Create a Commerce transaction version (POST .../actions/{action_var_name}; default versionTransaction_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs,…
- **`delete_transaction_line`** — Delete one transaction line (DELETE .../transactionLine/{documentNumber}). Destructive — permanently removes that line document. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existe…
- **`display_transaction_history`** — Display transaction history via a site-specific action (POST .../actions/{action_var_name}; action_var_name required). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via re…
- **`download_attachment`** — Download file bytes for an existing transaction attachment attribute (e.g. proposalAttachment_t). Returns MCP File attachment. Does not generate a proposal (use generate_proposal) and does not call exportAttachment (use…
- **`export_attachment`** — Export/view a CPQ-generated transaction attachment via REST (POST .../actions/{action_var_name}). Requires attribute_var_name (attachment attribute; sent as body selections). Returns JSON (documents/warnings); does not…
- **`generate_proposal`** — Generate a proposal document for a Commerce transaction (POST .../actions/generateProposal). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a pr…
- **`get_commerce_action`** — Get one Commerce document action definition by action_var_name. Defaults process from profile. Does not list all actions.
- **`get_commerce_actions`** — Get metadata for actions on a Commerce MAIN document (default doc_var_name='transaction' — not the line document). Returns one page of results (limit/offset). If hasMore is true, call again with offset = offset + limit.…
- **`get_commerce_attribute`** — Get one Commerce document attribute definition by attribute_var_name. Defaults process from profile, doc_var_name=transaction. Does not list all attributes (use get_commerce_attributes).
- **`get_commerce_attributes`** — Get metadata for attributes on a Commerce MAIN document (default doc_var_name='transaction' — not the line document). Returns one page of results (limit/offset). If hasMore is true, call again with offset = offset + lim…
- **`get_commerce_ui_settings`** — Get Commerce UI and general site settings (GET /commerceUISettings). Returns commerceSettings and generalSiteSettings as provided by CPQ. Requires a REST version that exposes this resource (docs target v19; set REST_API…
- **`get_document_layout`** — Get Commerce desktop layout definition for a process document (panels, tabs, actions, attributes). Defaults process from profile and doc_var_name='transaction'. Does not return live quote data.
- **`get_line_actions`** — Get metadata for actions on a Commerce LINE document (default doc_var_name='transactionLine' — not the main/header document). Returns one page of results (limit/offset). If hasMore is true, call again with offset = offs…
- **`get_line_attributes`** — Get metadata for attributes on a Commerce LINE document (default doc_var_name='transactionLine' — not the main/header document). Returns one page of results (limit/offset). If hasMore is true, call again with offset = o…
- **`get_saved_search`** — Get one saved search by numeric search_id (GET /searchResources/{resource_var_name}/{search_id}). resource_var_name optional — same default derivation as list_saved_searches. Docs target REST v19. Does not modify CPQ da…
- **`get_transaction`** — Get one Commerce transaction by numeric transaction_id. Optional expand / exclude_field_types. Defaults process from profile.
- **`get_transaction_line`** — Get a single transaction line by transaction_id and document_number (line document number).
- **`interact_transaction_line`** — Interact with a configured transaction line (POST .../transactionLine/{documentNumber}/actions/_interact). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs…
- **`list_commerce_processes`** — List Commerce process setups (admin metadata). Paginated. Does not list live transactions.
- **`list_commerce_processes_table`** — List all Commerce process setups as a flat table with variable_name, name, description, id, and label. Pages until complete. Does not list live transactions.
- **`list_saved_searches`** — List saved searches for a commerce document resource (GET /searchResources/{resource_var_name}). Paginated with limit/offset. Optional show_all maps to query showAll (ALL\|HIDDEN\|VISIBLE\|INACTIVE; default VISIBLE). When…
- **`list_transaction_lines`** — List line items for a Commerce transaction. Paginated collection with the same filter params as list_transactions. Empty items means no lines for that id.
- **`list_transactions`** — List Commerce transactions for the configured process (GET /commerceDocuments{Process}{Doc}). Returns one page; if hasMore is true, call again with offset = offset + limit. Supports q_expr, fields, orderby, expand, excl…
- **`new_transaction`** — Create a Commerce transaction via the _new_transaction action (POST .../actions/_new_transaction). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, return…
- **`reconfigure_transaction`** — Reconfigure a Commerce transaction (POST .../actions/_reconfigure_action). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview stating this…
- **`reconfigure_transaction_line`** — Reconfigure a transaction line (POST .../transactionLine/{documentNumber}/actions/_reconfigure_action). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, r…
- **`reconfigure_transaction_line_inbound`** — Inbound reconfigure of a transaction line (POST .../transactionLine/{documentNumber}/actions/_reconfigure_inbound_action). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence vi…
- **`remove_transaction_lines`** — Remove transaction lines via action (POST .../actions/_remove_transactionLine). Destructive — removes selected lines from the quote. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks ex…
- **`save_transaction`** — Save a Commerce transaction (POST .../actions/{action_var_name}; default cleanSave_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview…
- **`save_transaction_version`** — Save a Commerce transaction version (POST .../actions/{action_var_name}; default versionSave_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns…
- **`submit_transaction`** — Submit a Commerce transaction for approval (POST .../actions/{action_var_name}; default submit_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, return…
- **`sync_commerce_metadata_local`** — Fetch all header/line attributes and actions for a commerce process (paginated) and write JSON + Excel under data/{profile}/{env}/commerce/{process}/.
- **`update_transaction_lines`** — Update transaction lines (POST .../actions/_update_line_items). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview stating this will UPDAT…

## performance

_3 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `export_performance_logs` | `1.0.0` | `write` | `HIGH_RISK_WRITE` | `confirmation`, `dry_run`, `export`, `logs`, `performance`, `write` | POST /performanceLogs/actions/export | `log_id` (str \| None, default None); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | `body` (dict[str, Any] \| None, default None) | attachment/list (no root object schema) |
| `get_performance_log` | `1.0.0` | `read` | `READ_ONLY` | `logs`, `performance`, `read` | GET /performanceLogs/{id} | `log_id` (str, required) | - | read envelope `{status, tool, data}` |
| `list_performance_logs` | `1.0.0` | `read` | `READ_ONLY` | `logs`, `paginated`, `performance`, `read` | GET /performanceLogs | `limit` (int, default 100); `offset` (int, default 0); `total_results` (bool, default True); `fields` (list[str] \| None, default None); `orderby` (list[str] \| None, default None) | `q_expr` (str \| None, default None) | read envelope `{status, tool, data}` |

### Descriptions

- **`export_performance_logs`** — Export performance log events via REST. Optional log_id for single event. Does not list logs (use list_performance_logs). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via…
- **`get_performance_log`** — Get a single performance log event by numeric id. Does not export CSV and does not create Performance Debugger logs.
- **`list_performance_logs`** — List Oracle CPQ performance log events (user activity timing / metrics). Returns one page of results. If hasMore is true, call again with offset = offset + limit. Supports collection filters: q_expr (MongoDB q), fields…

## parts

_3 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `get_part` | `1.0.0` | `read` | `READ_ONLY` | `parts`, `read` | GET /parts/{id} | `part_id` (str, required) | - | read envelope `{status, tool, data}` |
| `list_parts` | `1.0.0` | `read` | `READ_ONLY` | `paginated`, `parts`, `read` | GET /parts | `limit` (int, default 100); `offset` (int, default 0); `fields` (list[str] \| None, default None) | `q_expr` (str \| None, default None) | read envelope `{status, tool, data}` |
| `search_parts` | `1.0.0` | `read` | `READ_ONLY` | `parts`, `read`, `search` | POST /parts/actions/search | `body` (dict[str, Any], required) | - | read envelope `{status, tool, data}` |

### Descriptions

- **`get_part`** — Get a single part by id.
- **`list_parts`** — List parts from the CPQ site. Returns one page of results. If hasMore is true, call again with offset = offset + limit.
- **`search_parts`** — Search parts via POST /parts/actions/search with a search body. Not a mutating write; allowed under READ_ONLY via client allowlist.

## tasks

_2 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `download_task_file` | `1.0.0` | `read` | `READ_ONLY` | `export`, `read`, `tasks` | GET /tasks/{taskId}/files/{fileName} | `task_id` (str, required); `file_name` (str, required) | - | attachment/list (no root object schema) |
| `get_task` | `1.0.0` | `read` | `READ_ONLY` | `read`, `tasks` | GET /tasks/{taskId} | `task_id` (str, required) | - | read envelope `{status, tool, data}` |

### Descriptions

- **`download_task_file`** — Download a file associated with a task (export zip/log). GET /tasks/{taskId}/files/{fileName}. Returns [envelope, File].
- **`get_task`** — Get task status/details by task_id (e.g. after export_datatables). GET /tasks/{taskId}.

## configuration

_17 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `get_array_set` | `1.0.0` | `read` | `READ_ONLY` | `arraySets`, `configuration`, `read` | GET /productFamilies/.../arraySets/{arraySetVarName} | `scope` (Literal['family', 'line', 'model'], required); `prod_fam_var_name` (str, required); `prod_line_var_name` (str \| None, default None); `model_var_name` (str \| None, default None); `array_set_var_name` (str, required) | - | read envelope `{status, tool, data}` |
| `get_array_set_attribute` | `1.0.0` | `read` | `READ_ONLY` | `arraySets`, `attributes`, `configuration`, `read` | GET /productFamilies/.../arraySets/{arraySetVarName}/attributes/{attributeVarName} | `scope` (Literal['family', 'line', 'model'], required); `prod_fam_var_name` (str, required); `prod_line_var_name` (str \| None, default None); `model_var_name` (str \| None, default None); `array_set_var_name` (str, required); `attribute_var_name` (str, required) | - | read envelope `{status, tool, data}` |
| `get_config_attribute` | `1.0.0` | `read` | `READ_ONLY` | `attributes`, `configuration`, `read` | GET /productFamilies/.../attributes/{attributeVarName} | `scope` (Literal['family', 'line', 'model'], required); `prod_fam_var_name` (str, required); `prod_line_var_name` (str \| None, default None); `model_var_name` (str \| None, default None); `attribute_var_name` (str, required) | - | read envelope `{status, tool, data}` |
| `get_config_layout` | `1.0.0` | `read` | `READ_ONLY` | `configuration`, `layouts`, `read` | GET /productFamilies/.../layouts/{layoutVarName} | `scope` (Literal['family', 'line', 'model'], required); `prod_fam_var_name` (str, required); `prod_line_var_name` (str \| None, default None); `model_var_name` (str \| None, default None); `layout_var_name` (str, required) | - | read envelope `{status, tool, data}` |
| `get_config_menu_item` | `1.0.0` | `read` | `READ_ONLY` | `configuration`, `menuItems`, `read` | GET /productFamilies/.../menuItems/{menuItemId} | `scope` (Literal['family', 'line', 'model'], required); `prod_fam_var_name` (str, required); `prod_line_var_name` (str \| None, default None); `model_var_name` (str \| None, default None); `parent_kind` (Literal['attribute', 'array_set_attribute'], required); `attribute_var_name` (str, required); `menu_item_id` (str, required); `array_set_var_name` (str \| None, default None) | - | read envelope `{status, tool, data}` |
| `get_layout_cache_attributes` | `1.0.0` | `read` | `READ_ONLY` | `configuration`, `layouts`, `read` | GET /layoutcache/{prodFamVarName}/{prodLineVarName}/{modelVarName}/attributes | `prod_fam_var_name` (str, required); `prod_line_var_name` (str, required); `model_var_name` (str, required) | - | read envelope `{status, tool, data}` |
| `get_model` | `1.0.0` | `read` | `READ_ONLY` | `configuration`, `metadata`, `read` | GET /productFamilies/{prodFamVarName}/productLines/{prodLineVarName}/models/{modelVarName} | `prod_fam_var_name` (str, required); `prod_line_var_name` (str, required); `model_var_name` (str, required) | - | read envelope `{status, tool, data}` |
| `get_product_family` | `1.0.0` | `read` | `READ_ONLY` | `configuration`, `metadata`, `read` | GET /productFamilies/{prodFamVarName} | `prod_fam_var_name` (str, required) | - | read envelope `{status, tool, data}` |
| `get_product_line` | `1.0.0` | `read` | `READ_ONLY` | `configuration`, `metadata`, `read` | GET /productFamilies/{prodFamVarName}/productLines/{prodLineVarName} | `prod_fam_var_name` (str, required); `prod_line_var_name` (str, required) | - | read envelope `{status, tool, data}` |
| `list_array_set_attributes` | `1.0.0` | `read` | `READ_ONLY` | `arraySets`, `attributes`, `configuration`, `read` | GET /productFamilies/.../arraySets/{arraySetVarName}/attributes | `scope` (Literal['family', 'line', 'model'], required); `prod_fam_var_name` (str, required); `prod_line_var_name` (str \| None, default None); `model_var_name` (str \| None, default None); `array_set_var_name` (str, required); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `list_array_sets` | `1.0.0` | `read` | `READ_ONLY` | `arraySets`, `configuration`, `read` | GET /productFamilies/.../arraySets | `scope` (Literal['family', 'line', 'model'], required); `prod_fam_var_name` (str, required); `prod_line_var_name` (str \| None, default None); `model_var_name` (str \| None, default None); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `list_config_attributes` | `1.0.0` | `read` | `READ_ONLY` | `attributes`, `configuration`, `read` | GET /productFamilies/.../attributes | `scope` (Literal['family', 'line', 'model'], required); `prod_fam_var_name` (str, required); `prod_line_var_name` (str \| None, default None); `model_var_name` (str \| None, default None); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `list_config_menu_items` | `1.0.0` | `read` | `READ_ONLY` | `configuration`, `menuItems`, `read` | GET /productFamilies/.../menuItems | `scope` (Literal['family', 'line', 'model'], required); `prod_fam_var_name` (str, required); `prod_line_var_name` (str \| None, default None); `model_var_name` (str \| None, default None); `parent_kind` (Literal['attribute', 'array_set_attribute'], required); `attribute_var_name` (str, required); `array_set_var_name` (str \| None, default None); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `list_models` | `1.0.0` | `read` | `READ_ONLY` | `configuration`, `metadata`, `read` | GET /productFamilies/{prodFamVarName}/productLines/{prodLineVarName}/models | `prod_fam_var_name` (str, required); `prod_line_var_name` (str, required); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `list_product_families` | `1.0.0` | `read` | `READ_ONLY` | `configuration`, `metadata`, `read` | GET /productFamilies | `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |
| `list_product_hierarchy_table` | `1.0.0` | `read` | `READ_ONLY` | `configuration`, `metadata`, `read`, `table` | GET /productFamilies/.../productLines/.../models | `page_size` (int, default 100) | - | read envelope `{status, tool, data}` |
| `list_product_lines` | `1.0.0` | `read` | `READ_ONLY` | `configuration`, `metadata`, `read` | GET /productFamilies/{prodFamVarName}/productLines | `prod_fam_var_name` (str, required); `limit` (int, default 100); `offset` (int, default 0) | - | read envelope `{status, tool, data}` |

### Descriptions

- **`get_array_set`** — Get one array set at scope family\|line\|model.
- **`get_array_set_attribute`** — Get one array-set attribute at scope family\|line\|model.
- **`get_config_attribute`** — Get one configuration attribute at scope family\|line\|model by attribute_var_name.
- **`get_config_layout`** — Get a configuration layout by layout_var_name at scope family\|line\|model.
- **`get_config_menu_item`** — Get one menu item by menu_item_id for an attribute or array-set attribute at scope family\|line\|model.
- **`get_layout_cache_attributes`** — Get layout-cache attributes for a model via GET /layoutcache/{fam}/{line}/{model}/attributes.
- **`get_model`** — Get one model by family, line, and model variable names.
- **`get_product_family`** — Get one product family by prod_fam_var_name.
- **`get_product_line`** — Get one product line by family + line variable names.
- **`list_array_set_attributes`** — List attributes of an array set at scope family\|line\|model.
- **`list_array_sets`** — List array sets at scope family\|line\|model.
- **`list_config_attributes`** — List configuration attributes at scope family\|line\|model (composite path under /productFamilies/.../attributes).
- **`list_config_menu_items`** — List menu items for an attribute or array-set attribute (parent_kind=attribute\|array_set_attribute) at scope family\|line\|model.
- **`list_models`** — List models under a product family/line.
- **`list_product_families`** — List product family metadata via GET /productFamilies.
- **`list_product_hierarchy_table`** — Walk all product families → lines → models and return a flat table of variable names and display names (one row per model; empty model columns when a family/line has no models). Pages CPQ collections. Does not write pro…
- **`list_product_lines`** — List product lines under a product family.

## meta

_21 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `discover_tools` | `1.0.0` | `read` | `READ_ONLY` | `discovery`, `meta`, `read` | — | `limit` (int, default 20) | `query` (str \| None, default None); `domain` (Literal['users', 'groups', 'datatables', 'bml', 'commerce', 'performance', …], default 'all'); `operation` (Literal['read', 'write', 'all'], default 'all') | read envelope `{status, tool, data}` |
| `ensure_prompt_studio` | `1.0.0` | `read` | `READ_ONLY` | `meta`, `prompt_studio`, `read`, `saved_prompts` | — | - | - | read envelope `{status, tool, data}` |
| `export_response_excel` | `1.0.0` | `read` | `READ_ONLY` | `excel`, `export`, `meta`, `read` | — | `title` (str, required); `sheets` (list[ExportResponseSheetInput], required); `notes` (str \| None, default None) | - | attachment/list (no root object schema) |
| `export_response_word` | `1.1.0` | `read` | `READ_ONLY` | `export`, `meta`, `read` | — | `title` (str, required); `sheets` (list[ExportResponseSheetInput], required); `notes` (str \| None, default None); `diagrams` (list[ExportResponseDiagramInput] \| None, default None) | - | attachment/list (no root object schema) |
| `get_local_data_status` | `1.0.0` | `read` | `READ_ONLY` | `local_data`, `meta`, `read` | — | `process_var_name` (str \| None, default None); `table_name` (str \| None, default None) | `domain` (Literal['users', 'groups', 'bml', 'commerce', 'datatables'], required) | read envelope `{status, tool, data}` |
| `get_local_job` | `1.0.0` | `read` | `READ_ONLY` | `async`, `local_data`, `meta`, `read` | — | `job_id` (str, required) | - | read envelope `{status, tool, data}` |
| `get_saved_prompt` | `1.0.0` | `read` | `READ_ONLY` | `meta`, `read`, `saved_prompts` | — | `prompt_id` (str, required) | - | read envelope `{status, tool, data}` |
| `list_local_data` | `1.1.0` | `read` | `READ_ONLY` | `discovery`, `local_data`, `meta`, `read` | — | - | - | read envelope `{status, tool, data}` |
| `list_saved_prompts` | `1.1.0` | `read` | `READ_ONLY` | `meta`, `read`, `saved_prompts` | — | `limit` (int, default 50) | - | read envelope `{status, tool, data}` |
| `load_local_data` | `1.1.0` | `read` | `READ_ONLY` | `local_data`, `meta`, `read` | — | `process_var_name` (str \| None, default None); `table_name` (str \| None, default None); `include_payload` (bool, default False); `payload_keys` (list[str] \| None, default None) | `domain` (Literal['users', 'groups', 'bml', 'commerce', 'datatables'], required) | read envelope `{status, tool, data}` |
| `offer_export_response` | `1.0.0` | `read` | `READ_ONLY` | `excel`, `export`, `local_data`, `meta`, `read` | — | `title` (str, required); `sheets` (list[ExportResponseSheetInput] \| None, default None); `notes` (str \| None, default None); `choice` (Literal['excel', 'word', 'both', 'skip', 'always_excel', 'never'] \| None, default None) | - | read envelope `{status, tool, data}` |
| `offer_save_refined_prompt` | `1.2.0` | `read` | `READ_ONLY` | `meta`, `read`, `saved_prompts` | — | `title` (str, required); `original_user_prompt` (str, required); `refined_prompt` (str, required); `variables` (dict[str, Any] \| None, default None); `tags` (list[str] \| None, default None); `tools` (list[str] \| None, default None); `output_format` (Literal['chat_text', 'json', 'excel_download'], default 'chat_text'); `save` (bool \| None, default None); `always` (bool \| None, default None) | - | read envelope `{status, tool, data}` |
| `offer_use_local_data` | `1.1.0` | `read` | `READ_ONLY` | `local_data`, `meta`, `read` | — | `process_var_name` (str \| None, default None); `table_name` (str \| None, default None); `choice` (Literal['use_cache', 'fetch_fresh', 'prefer', 'never'] \| None, default None) | `domain` (Literal['users', 'groups', 'bml', 'commerce', 'datatables'], required) | read envelope `{status, tool, data}` |
| `record_prompt_use` | `1.0.0` | `read` | `READ_ONLY` | `meta`, `read`, `saved_prompts` | — | `prompt_id` (str, required) | - | read envelope `{status, tool, data}` |
| `save_refined_prompt` | `1.2.0` | `read` | `READ_ONLY` | `meta`, `read`, `saved_prompts` | — | `title` (str, required); `original_user_prompt` (str, required); `refined_prompt` (str, required); `variables` (dict[str, Any] \| None, default None); `tags` (list[str] \| None, default None); `tools` (list[str] \| None, default None); `output_format` (Literal['chat_text', 'json', 'excel_download'], default 'chat_text') | - | read envelope `{status, tool, data}` |
| `search_saved_prompts` | `1.0.0` | `read` | `READ_ONLY` | `meta`, `read`, `saved_prompts`, `search` | — | `limit` (int, default 20) | `query` (str \| None, default None); `tag` (str \| None, default None); `tool_domain` (str \| None, default None) | read envelope `{status, tool, data}` |
| `set_auto_save_refined_prompt` | `1.0.0` | `read` | `READ_ONLY` | `meta`, `read`, `saved_prompts` | — | `enabled` (bool, required) | - | read envelope `{status, tool, data}` |
| `set_local_data_policy` | `1.0.0` | `read` | `READ_ONLY` | `local_data`, `meta`, `read` | — | `policy` (Literal['ask', 'prefer', 'never'], required) | - | read envelope `{status, tool, data}` |
| `set_post_response_export` | `1.0.0` | `read` | `READ_ONLY` | `export`, `local_data`, `meta`, `read` | — | `policy` (Literal['ask', 'never', 'always_excel'], required) | - | read envelope `{status, tool, data}` |
| `set_saved_prompt_enabled` | `1.0.0` | `read` | `READ_ONLY` | `meta`, `read`, `saved_prompts` | — | `prompt_id` (str, required); `enabled` (bool, required) | - | read envelope `{status, tool, data}` |
| `start_prompt_picker` | `1.1.0` | `read` | `READ_ONLY` | `discovery`, `meta`, `read`, `saved_prompts` | — | `mode` (str \| None, default None); `prompt_id` (str \| None, default None) | `query` (str \| None, default None); `tag` (str \| None, default None); `tool_domain` (str \| None, default None); `tool` (str \| None, default None) | read envelope `{status, tool, data}` |

### Descriptions

- **`discover_tools`** — Search and filter the Oracle CPQ MCP tool catalog by domain (users/groups/datatables/bml/commerce/performance/parts/tasks/configuration/metrics/collab/admin), operation, or free-text query. Use this to find read-only vs…
- **`ensure_prompt_studio`** — Probe local Prompt Studio (GET http://127.0.0.1:8765/api/health by default) and auto-start it in the background if it is not running (python -m apps.prompt_studio). Returns running/started, url, host, port, optional pid…
- **`export_response_excel`** — Build a multi-sheet Excel (.xlsx) from structured sheets [{name, columns?, rows}] and write under data/{profile}/{env}/exports/. Returns an attachment lead envelope plus File bytes. Caps: 20 sheets, 10k rows total. Does…
- **`export_response_word`** — Build a Word (.docx) from structured sheets (optional notes) and optional diagrams [{title, mermaid?, image_path?, caption?}] and write under data/{profile}/{env}/exports/. Mermaid is rasterized locally via mmdc (@merma…
- **`get_local_data_status`** — Check whether a local snapshot exists for a domain (users/groups/bml/commerce/datatables). For commerce pass process_var_name; for datatables pass table_name. Does not call Oracle CPQ.
- **`get_local_job`** — Poll an MCP-local background job started by start_bml_site_export (or future local job starters). Returns status queued\|running\|succeeded\|failed plus result paths or error. Does not call Oracle CPQ. For Oracle CPQ async…
- **`get_saved_prompt`** — Load one saved refined prompt by id, including refined_prompt text and variables. Does not call Oracle CPQ.
- **`list_local_data`** — List local data/{profile}/{env} snapshots (manifests) for the active profile. Does not call Oracle CPQ. Use before live list/export tools when LOCAL_DATA_POLICY is ask or prefer.
- **`list_saved_prompts`** — List locally saved refined prompts (title, tags, tools, last_run). Does not call Oracle CPQ. Library file defaults to .prompts/saved_prompts.json.
- **`load_local_data`** — Load a local snapshot summary and file paths under data/. Default omits large payloads (include_payload=false) to save tokens. Does not call Oracle CPQ.
- **`offer_export_response`** — After a tabular chat answer, offer to export structured sheets to Excel and/or Word. Omit choice for needs_user_input (excel / word / both / skip / always_excel / never). always_excel/never also write POST_RESPONSE_EXPO…
- **`offer_save_refined_prompt`** — Offer to save a refined prompt after a CPQ-related task. If save is omitted, returns needs_user_input with choices: save once, save and always auto-save, or skip (chat fallback when elicitation is unavailable). With sav…
- **`offer_use_local_data`** — Ask whether to use a local data/ snapshot or fetch fresh CPQ data. Omit choice for needs_user_input (use_cache / fetch_fresh / prefer / never). prefer/never also write LOCAL_DATA_POLICY on the profile .env. Does not cal…
- **`record_prompt_use`** — Update last_run_at and run_count for a saved prompt after the user runs it. Writes only the local saved-prompts library (not Oracle CPQ).
- **`save_refined_prompt`** — Save a refined prompt (title, original user prompt, refined text, variables, tags, tools, output_format) into the local library. output_format is chat_text (default), json, or excel_download. Dedupes by content hash (in…
- **`search_saved_prompts`** — Search saved refined prompts by title text, tag, and/or tool domain. Does not call Oracle CPQ.
- **`set_auto_save_refined_prompt`** — Set AUTO_SAVE_REFINED_PROMPT=true\|false on the active customer profile .env (allowlisted key rewrite only). Does not call Oracle CPQ. Treat the tool result as source of truth for the rest of this session; reload MCP if…
- **`set_local_data_policy`** — Set LOCAL_DATA_POLICY=ask\|prefer\|never on the active customer profile .env (allowlisted key rewrite only). Does not call Oracle CPQ. Reload MCP if you need server instructions rebuilt from the new flag.
- **`set_post_response_export`** — Set POST_RESPONSE_EXPORT=ask\|never\|always_excel on the active customer profile .env (allowlisted key rewrite only). Does not call Oracle CPQ. Reload MCP if you need server instructions rebuilt from the new flag.
- **`set_saved_prompt_enabled`** — Enable or disable a saved refined prompt by id. Disabled prompts are hidden from list/search/picker. Local library file only; does not call Oracle CPQ.
- **`start_prompt_picker`** — Interactively pick an enabled saved refined prompt: all (by title), search, by_tag, by_tool (also last5 / by_domain). Omit mode for the top-level menu; pass prompt_id to load and record use. Disabled prompts are hidden.…

## admin

_3 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `get_certificate` | `1.0.0` | `read` | `READ_ONLY` | `admin`, `certificates`, `read` | GET /certificates/{name} | `name` (str, required) | - | read envelope `{status, tool, data}` |
| `get_sso_configuration` | `1.0.0` | `read` | `READ_ONLY` | `admin`, `read`, `sso` | GET /ssoConfiguration | - | - | read envelope `{status, tool, data}` |
| `list_certificates` | `1.0.0` | `read` | `READ_ONLY` | `admin`, `certificates`, `read` | GET /certificates | - | - | read envelope `{status, tool, data}` |

### Descriptions

- **`get_certificate`** — Get one site certificate by name (GET /certificates/{name}). PEM/certificate material is redacted ([REDACTED]) in MCP responses. Docs target REST v19. Read-only.
- **`get_sso_configuration`** — Get site SSO configuration (GET /ssoConfiguration). IdP certificate and SAML keystore fields are redacted ([REDACTED]) in MCP responses. Docs target REST v19. Read-only; does not change SSO settings.
- **`list_certificates`** — List site certificates (GET /certificates). PEM/certificate material in responses is redacted ([REDACTED]) before reaching the LLM. Docs target REST v19 (set REST_API_VERSION=v19 if v18 returns 404). Read-only; does not…

## collab

_2 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `clear_collab_operation_queue` | `1.0.0` | `write` | `DESTRUCTIVE` | `collab`, `confirmation`, `dry_run`, `queue`, `write` | POST /collabOperationQueues/{bs_id}/actions/clearCurrentQueue | `bs_id` (int, required); `dry_run` (bool, default True); `confirmation_token` (str \| None, default None) | - | write envelope `{status, tool, data}` |
| `get_collab_operation_queue` | `1.0.0` | `read` | `READ_ONLY` | `collab`, `queue`, `read` | GET /collabOperationQueues/{bs_id} | `bs_id` (int, required) | - | read envelope `{status, tool, data}` |

### Descriptions

- **`clear_collab_operation_queue`** — Clear the collaborative quote operation queue for a commerce document (POST /collabOperationQueues/{bs_id}/actions/clearCurrentQueue). Destructive — removes queued/current collab operations for that bs_id. Safe executio…
- **`get_collab_operation_queue`** — Get the collaborative quote operation queue for a commerce document (GET /collabOperationQueues/{bs_id}). Returns queuedOperations, currentlyExecutingOperation, operationCount, and node. Requires a REST version that exp…

## metrics

_1 tool(s)_

| Tool | Version | Op | Risk | Tags | HTTP / API | Parameters | Filters | Output |
|------|---------|----|------|------|------------|------------|---------|--------|
| `list_metrics` | `1.0.0` | `read` | `READ_ONLY` | `metrics`, `paginated`, `read` | GET /metrics | `limit` (int, default 100); `offset` (int, default 0); `total_results` (bool, default True) | `name` (str \| None, default None); `start_time` (str \| None, default None); `end_time` (str \| None, default None); `date_modified_from` (str \| None, default None); `date_modified_to` (str \| None, default None); `date_added_from` (str \| None, default None); `date_added_to` (str \| None, default None) | read envelope `{status, tool, data}` |

### Descriptions

- **`list_metrics`** — List Oracle CPQ site metrics (GET /metrics). Returns one page of items (name, value, startTime, endTime, dateModified, dateAdded). Optional filters: name (exact), start_time/end_time, date_modified_from/to, date_added_f…

---

## Regeneration

After adding or changing tools in `mcp/oracle_cpq_mcp/registry/tool_registry.py` (and matching input models), run:

```bash
python scripts/generate_tool_catalog.py
```
