# Oracle CPQ MCP - Tool Catalog

> **Auto-generated.** Do not edit by hand.
> Regenerate with:
>
> ```bash
> oracle-cpq generate-tool-catalog
> # or: python scripts/generate_tool_catalog.py
> ```

**Total tools:** 157

This document is the formal per-tool reference for the GitHub repository. Each domain lists **Read tools** then **Write tools**. Every tool has one property table (Version, CX module, Op/Risk, Method, CPQ REST URL, Fusion REST URL, Tags, Parameters, Filters, Output, Description) so API path and inputs stay together.

**CPQ REST URL** and **Fusion REST URL** are paths relative to the site base URL. Standalone (`cpq.hosted: standalone` or omitted): **CPQ REST URL** (`/rest/{rest_api_version}` + API path). Fusion-hosted CPQ (`cpq.hosted: fusion`): **Fusion REST URL** (`/cpq/rest/{rest_api_version}` + API path). `{rest_api_version}` comes from the profile (e.g. `v18` / `v19`). `CPQClient` applies the prefix from nested `cpq.hosted` / `cpq.auth` (legacy `cpq_mode` / `fusion_enabled` still migrate). Sales/PRM tools put the **CRM REST** path (`/crmRestApi/resources/11.13.18.05/…`) in the Fusion REST URL column (base `cx.url`); the CPQ column is `— (CX … REST; not CPQ)`. Local/meta tools show `— (local / no CPQ REST)` in both columns.

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
- [metrics](#metrics)
- [collab](#collab)
- [admin](#admin)
- [sales](#sales)
- [prm](#prm)
- [meta](#meta)

## users

_6 tool(s)_

- **Read:** [`export_users_excel`](#export-users-excel), [`get_user`](#get-user), [`get_user_groups`](#get-user-groups), [`list_users`](#list-users), [`sync_users_local`](#sync-users-local)
- **Write:** [`update_user`](#update-user)

### Read tools

#### `export_users_excel`

| | |
|---|---|
| **Version** | `1.2.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `PRIVILEGED` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/users` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/users` |
| **Tags** | `cpq`, `excel`, `export`, `local_data`, `read`, `users` |
| **Parameters** | `columns` (list[str] \| None, default None) |
| **Filters** | `status_filter` (Literal['active', 'inactive', 'all'], default 'active')<br>`q_expr` (str \| None, default None) |
| **Output** | attachment/list (no root object schema) |
| **Description** | Export CPQ users to an Excel (.xlsx) file. Defaults to active users only. Also writes users.json + users.xlsx under data/{profile}/{env}/users/. |

#### `get_user`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/users/{partyNumber}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/users/{partyNumber}` |
| **Tags** | `cpq`, `read`, `users` |
| **Parameters** | `party_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get a single user by party number. |

#### `get_user_groups`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/users/{partyNumber}/groups` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/users/{partyNumber}/groups` |
| **Tags** | `cpq`, `groups`, `paginated`, `read`, `users` |
| **Parameters** | `party_number` (str, required)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List all groups assigned to a user. Returns one page of results. If hasMore is true, call again with offset = offset + limit. |

#### `list_users`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/users` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/users` |
| **Tags** | `cpq`, `paginated`, `read`, `users` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | `status_filter` (Literal['active', 'inactive', 'all'], default 'active')<br>`q_expr` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List users across all companies on the CPQ site. Defaults to active users only. Returns one page of results. If hasMore is true, call again with offset = offset + limit. Use export_users_excel for a full Excel export. |

#### `sync_users_local`

| | |
|---|---|
| **Version** | `1.1.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `PRIVILEGED` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/users` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/users` |
| **Tags** | `cpq`, `excel`, `export`, `local_data`, `read`, `users` |
| **Parameters** | `columns` (list[str] \| None, default None) |
| **Filters** | `status_filter` (Literal['active', 'inactive', 'all'], default 'active')<br>`q_expr` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Fetch all CPQ users (paginated) and write data/{profile}/{env}/users/ (users.json + users.xlsx + manifest.json). Prefer this for a complete local cache. Defaults to active users only. |

### Write tools

#### `update_user`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `PATCH` |
| **CPQ REST URL** | `/rest/{rest_api_version}/users/{partyNumber}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/users/{partyNumber}` |
| **Tags** | `confirmation`, `cpq`, `dry_run`, `users`, `write` |
| **Parameters** | `party_number` (str, required)<br>`patch_body` (dict[str, Any], required)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Patch-update an existing user. Only include fields you intend to change. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview stating this w… |

## groups

_5 tool(s)_

- **Read:** [`get_group`](#get-group), [`list_group_users`](#list-group-users), [`list_groups`](#list-groups), [`sync_groups_local`](#sync-groups-local)
- **Write:** [`create_group`](#create-group)

### Read tools

#### `get_group`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/companies/{company}/groups/{groupVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/companies/{company}/groups/{groupVarName}` |
| **Tags** | `cpq`, `groups`, `read` |
| **Parameters** | `group_var_name` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get details for a single group by its variable name. |

#### `list_group_users`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/companies/{company}/groups/{groupVarName}/users` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/companies/{company}/groups/{groupVarName}/users` |
| **Tags** | `cpq`, `groups`, `paginated`, `read`, `users` |
| **Parameters** | `group_var_name` (str, required)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List users that belong to a group. Returns one page of results. If hasMore is true, call again with offset = offset + limit. |

#### `list_groups`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/companies/{company}/groups` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/companies/{company}/groups` |
| **Tags** | `cpq`, `groups`, `paginated`, `read` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List groups for the configured company (defaults to host company `_host`). Returns one page of results. If hasMore is true, call again with offset = offset + limit. |

#### `sync_groups_local`

| | |
|---|---|
| **Version** | `1.1.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `PRIVILEGED` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/companies/{company}/groups` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/companies/{company}/groups` |
| **Tags** | `cpq`, `excel`, `export`, `groups`, `local_data`, `read` |
| **Parameters** | — |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Fetch all company groups (paginated) and write data/{profile}/{env}/groups/ (groups.json + groups.xlsx + manifest.json). |

### Write tools

#### `create_group`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/companies/{company}/groups` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/companies/{company}/groups` |
| **Tags** | `confirmation`, `cpq`, `dry_run`, `groups`, `write` |
| **Parameters** | `group_body` (dict[str, Any], required)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Create a new group for the configured company. Requires admin permissions. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview stating this… |

## datatables

_10 tool(s)_

- **Read:** [`get_datatable`](#get-datatable), [`get_datatable_field`](#get-datatable-field), [`get_datatable_rows`](#get-datatable-rows), [`list_datatable_fields`](#list-datatable-fields), [`list_datatables`](#list-datatables), [`sync_datatable_local`](#sync-datatable-local), [`sync_datatables_local`](#sync-datatables-local)
- **Write:** [`create_datatable`](#create-datatable), [`deploy_datatables`](#deploy-datatables), [`export_datatables`](#export-datatables)

### Read tools

#### `get_datatable`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/datatables/{tableName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/datatables/{tableName}` |
| **Tags** | `cpq`, `datatables`, `read` |
| **Parameters** | `table_name` (str \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get metadata/properties for a data table. Defaults to the first CUSTOM_DATA_TABLE_NAME from profile (supports CUSTOM_DATA_TABLE_NAME_1, _2, etc.). |

#### `get_datatable_field`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/datatables/{tableName}/fields/{fieldName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/datatables/{tableName}/fields/{fieldName}` |
| **Tags** | `cpq`, `datatables`, `read` |
| **Parameters** | `field_name` (str, required)<br>`table_name` (str \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one data table field definition by field name. Defaults table_name from profile. |

#### `get_datatable_rows`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/adminCustom{tableName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/adminCustom{tableName}` |
| **Tags** | `cpq`, `datatables`, `paginated`, `read` |
| **Parameters** | `table_name` (str \| None, default None)<br>`limit` (int, default 50)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get rows from a deployed data table. Defaults to the first CUSTOM_DATA_TABLE_NAME from profile (supports _1, _2 suffixes). Returns one page of results. If hasMore is true, call again with offset = offset + limit. |

#### `list_datatable_fields`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/datatables/{tableName}/fields` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/datatables/{tableName}/fields` |
| **Tags** | `cpq`, `datatables`, `paginated`, `read` |
| **Parameters** | `table_name` (str \| None, default None)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List field definitions for a data table. Defaults table_name from profile. Returns one page of results. If hasMore is true, call again with offset = offset + limit. |

#### `list_datatables`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/datatables` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/datatables` |
| **Tags** | `cpq`, `datatables`, `paginated`, `read` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List data tables defined on the CPQ site. Returns one page of results. If hasMore is true, call again with offset = offset + limit. |

#### `sync_datatable_local`

| | |
|---|---|
| **Version** | `1.1.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `PRIVILEGED` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/datatables/{name}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/datatables/{name}` |
| **Tags** | `cpq`, `datatables`, `excel`, `export`, `local_data`, `read` |
| **Parameters** | `table_name` (str \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Fetch one data table meta + all rows and write data/{profile}/{env}/datatables/{name}/ (meta.json, rows.json, rows.xlsx). |

#### `sync_datatables_local`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `PRIVILEGED` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/datatables/{name}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/datatables/{name}` |
| **Tags** | `cpq`, `datatables`, `excel`, `export`, `local_data`, `read` |
| **Parameters** | `table_names` (list[str] \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Sync one or more data tables locally. Defaults to all CUSTOM_DATA_TABLE_NAME* values from the profile. |

### Write tools

#### `create_datatable`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/datatables` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/datatables` |
| **Tags** | `admin`, `confirmation`, `cpq`, `datatables`, `dry_run`, `write` |
| **Parameters** | `body` (dict[str, Any], required)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Create a new data table via POST /datatables. Requires name; optional description, folder, fields, isLive. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs… |

#### `deploy_datatables`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `DESTRUCTIVE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/datatables/actions/deploy` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/datatables/actions/deploy` |
| **Tags** | `admin`, `confirmation`, `cpq`, `datatables`, `dry_run`, `write` |
| **Parameters** | `table_names` (list[str], required)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Deploy one or more data tables. Admin-only — changes live CPQ configuration. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview stating th… |

#### `export_datatables`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/datatables/actions/export` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/datatables/actions/export` |
| **Tags** | `admin`, `confirmation`, `cpq`, `datatables`, `dry_run`, `export`, `write` |
| **Parameters** | `body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Start a data table export task via POST /datatables/actions/export. Returns taskId; poll with get_task and download with download_task_file. Safe execution: defaults to dry_run=true (preflight only — validates inputs, c… |

## bml

_11 tool(s)_

- **Read:** [`get_all_bml_code`](#get-all-bml-code), [`get_bml_common_function`](#get-bml-common-function), [`get_bml_dependent_attributes`](#get-bml-dependent-attributes), [`get_bml_function`](#get-bml-function), [`list_bml_common_functions`](#list-bml-common-functions), [`list_bml_library_folders`](#list-bml-library-folders), [`search_bml_scripts`](#search-bml-scripts), [`search_local_bml`](#search-local-bml), [`start_bml_site_export`](#start-bml-site-export), [`sync_bml_local`](#sync-bml-local)
- **Write:** [`export_bml_library_functions`](#export-bml-library-functions)

### Read tools

#### `get_all_bml_code`

| | |
|---|---|
| **Version** | `1.4.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `PRIVILEGED` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/adminMeta` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/adminMeta` |
| **Tags** | `admin`, `bml`, `cpq`, `export`, `local_data`, `read` |
| **Parameters** | `delivery` (Literal['zip', 'json'], default 'zip') |
| **Filters** | — |
| **Output** | attachment/list (no root object schema) |
| **Description** | Download or retrieve BML source code from the CPQ site (synchronous — blocks the MCP tool call until done). delivery='zip' (default) exports all Commerce BML and BMLT files via GET /adminMeta — equivalent to cpq-toolkit… |

#### `get_bml_common_function`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/bml/common/functions/{name}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/bml/common/functions/{name}` |
| **Tags** | `bml`, `cpq`, `read` |
| **Parameters** | `name` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one BML common function by name via GET /bml/common/functions/{name}. |

#### `get_bml_dependent_attributes`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/bml/library/functions/actions/dependentAttributes` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/bml/library/functions/actions/dependentAttributes` |
| **Tags** | `bml`, `cpq`, `read` |
| **Parameters** | `body` (dict[str, Any] \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Return attributes referenced by util library functions via POST /bml/library/functions/actions/dependentAttributes. Read-like; allowed under READ_ONLY. |

#### `get_bml_function`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/bml/library/functions/{namespace.variableName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/bml/library/functions/{namespace.variableName}` |
| **Tags** | `bml`, `cpq`, `read` |
| **Parameters** | `function_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one util library BML function by function_id (namespace.variableName). Does not export full site zip. |

#### `list_bml_common_functions`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/bml/common/functions` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/bml/common/functions` |
| **Tags** | `bml`, `cpq`, `read` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List built-in BML common functions (atoi, len, etc.) via GET /bml/common/functions. |

#### `list_bml_library_folders`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/bml/library/folders` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/bml/library/folders` |
| **Tags** | `bml`, `cpq`, `read` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List util library folders via GET /bml/library/folders. |

#### `search_bml_scripts`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/bml/scripts` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/bml/scripts` |
| **Tags** | `bml`, `cpq`, `paginated`, `read`, `search` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0)<br>`orderby` (str \| None, default None)<br>`fields` (list[str] \| None, default None) |
| **Filters** | `q_expr` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Search BML scripts containing a string via GET /bml/scripts. Supports q_expr, limit, offset, orderby, fields. |

#### `search_local_bml`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `bml`, `cpq`, `local_data`, `read`, `search` |
| **Parameters** | `max_matches` (int, default 50)<br>`case_insensitive` (bool, default True)<br>`include_functions` (bool, default True) |
| **Filters** | `query` (str, required) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Search text across extracted local BML files under data/{profile}/{env}/bml/site/ (and util library .bml under bml/functions/). Does not call Oracle CPQ. Use after get_all_bml_code or start_bml_site_export has populated… |

#### `start_bml_site_export`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/adminMeta` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/adminMeta` |
| **Tags** | `async`, `bml`, `cpq`, `export`, `local_data`, `read` |
| **Parameters** | — |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Start a background MCP-local job that downloads the full Commerce BML/BMLT site zip (GET /adminMeta), persists under data/{profile}/{env}/bml/, and extracts to bml/site/. Returns immediately with job_id. Poll with get_l… |

#### `sync_bml_local`

| | |
|---|---|
| **Version** | `1.1.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `PRIVILEGED` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/bml/library/functions` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/bml/library/functions` |
| **Tags** | `bml`, `cpq`, `export`, `local_data`, `read` |
| **Parameters** | — |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Fetch all util library BML functions with scriptText and write data/{profile}/{env}/bml/ (library.json + functions/**/*.bml + **/*.json). |

### Write tools

#### `export_bml_library_functions`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/bml/library/functions/actions/export` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/bml/library/functions/actions/export` |
| **Tags** | `bml`, `confirmation`, `cpq`, `dry_run`, `export`, `write` |
| **Parameters** | `body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Export util library functions via POST .../actions/export. Returns taskId; use get_task and download_task_file. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only… |

## commerce

_38 tool(s)_

- **Read:** [`download_attachment`](#download-attachment), [`get_commerce_action`](#get-commerce-action), [`get_commerce_actions`](#get-commerce-actions), [`get_commerce_attribute`](#get-commerce-attribute), [`get_commerce_attributes`](#get-commerce-attributes), [`get_commerce_ui_settings`](#get-commerce-ui-settings), [`get_document_layout`](#get-document-layout), [`get_line_actions`](#get-line-actions), [`get_line_attributes`](#get-line-attributes), [`get_saved_search`](#get-saved-search), [`get_transaction`](#get-transaction), [`get_transaction_line`](#get-transaction-line), [`list_commerce_processes`](#list-commerce-processes), [`list_commerce_processes_table`](#list-commerce-processes-table), [`list_saved_searches`](#list-saved-searches), [`list_transaction_lines`](#list-transaction-lines), [`list_transactions`](#list-transactions), [`sync_commerce_metadata_local`](#sync-commerce-metadata-local)
- **Write:** [`add_from_favorites`](#add-from-favorites), [`add_transaction_lines`](#add-transaction-lines), [`copy_transaction`](#copy-transaction), [`copy_transaction_lines`](#copy-transaction-lines), [`create_transaction`](#create-transaction), [`create_transaction_version`](#create-transaction-version), [`delete_transaction_line`](#delete-transaction-line), [`display_transaction_history`](#display-transaction-history), [`export_attachment`](#export-attachment), [`generate_proposal`](#generate-proposal), [`interact_transaction_line`](#interact-transaction-line), [`new_transaction`](#new-transaction), [`reconfigure_transaction`](#reconfigure-transaction), [`reconfigure_transaction_line`](#reconfigure-transaction-line), [`reconfigure_transaction_line_inbound`](#reconfigure-transaction-line-inbound), [`remove_transaction_lines`](#remove-transaction-lines), [`save_transaction`](#save-transaction), [`save_transaction_version`](#save-transaction-version), [`submit_transaction`](#submit-transaction), [`update_transaction_lines`](#update-transaction-lines)

### Read tools

#### `download_attachment`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/attachment fileLocation` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/attachment fileLocation` |
| **Tags** | `attachments`, `commerce`, `cpq`, `read`, `transactions` |
| **Parameters** | `transaction_id` (str, required)<br>`attribute_var_name` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`document_number` (str, default '1') |
| **Filters** | — |
| **Output** | attachment/list (no root object schema) |
| **Description** | Download file bytes for an existing transaction attachment attribute (e.g. proposalAttachment_t). Returns MCP File attachment. Does not generate a proposal (use generate_proposal) and does not call exportAttachment (use… |

#### `get_commerce_action`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceProcesses/{processVarName}/documents/{docVarName}/actionDefs/{actionVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceProcesses/{processVarName}/documents/{docVarName}/actionDefs/{actionVarName}` |
| **Tags** | `actions`, `commerce`, `cpq`, `metadata`, `read` |
| **Parameters** | `action_var_name` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`expand_all` (bool, default False) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one Commerce document action definition by action_var_name. Defaults process from profile. Does not list all actions. |

#### `get_commerce_actions`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceProcesses/{processVarName}/documents/{docVarName}/actionDefs` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceProcesses/{processVarName}/documents/{docVarName}/actionDefs` |
| **Tags** | `actions`, `commerce`, `cpq`, `metadata`, `paginated`, `read` |
| **Parameters** | `process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`expand_all` (bool, default False)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get metadata for actions on a Commerce MAIN document (default doc_var_name='transaction' — not the line document). Returns one page of results (limit/offset). If hasMore is true, call again with offset = offset + limit.… |

#### `get_commerce_attribute`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceProcesses/{processVarName}/documents/{docVarName}/attributes/{attributeVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceProcesses/{processVarName}/documents/{docVarName}/attributes/{attributeVarName}` |
| **Tags** | `attributes`, `commerce`, `cpq`, `metadata`, `read` |
| **Parameters** | `attribute_var_name` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`expand_all` (bool, default False) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one Commerce document attribute definition by attribute_var_name. Defaults process from profile, doc_var_name=transaction. Does not list all attributes (use get_commerce_attributes). |

#### `get_commerce_attributes`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceProcesses/{processVarName}/documents/{docVarName}/attributes` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceProcesses/{processVarName}/documents/{docVarName}/attributes` |
| **Tags** | `attributes`, `commerce`, `cpq`, `metadata`, `paginated`, `read` |
| **Parameters** | `process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`expand_all` (bool, default False)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get metadata for attributes on a Commerce MAIN document (default doc_var_name='transaction' — not the line document). Returns one page of results (limit/offset). If hasMore is true, call again with offset = offset + lim… |

#### `get_commerce_ui_settings`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceUISettings` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceUISettings` |
| **Tags** | `commerce`, `cpq`, `read`, `settings`, `ui` |
| **Parameters** | — |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get Commerce UI and general site settings (GET /commerceUISettings). Returns commerceSettings and generalSiteSettings as provided by CPQ. Requires a REST version that exposes this resource (docs target v19; set REST_API… |

#### `get_document_layout`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceProcesses/{processVarName}/layouts/{mainDocVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceProcesses/{processVarName}/layouts/{mainDocVarName}` |
| **Tags** | `commerce`, `cpq`, `layout`, `metadata`, `read` |
| **Parameters** | `process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction') |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get Commerce desktop layout definition for a process document (panels, tabs, actions, attributes). Defaults process from profile and doc_var_name='transaction'. Does not return live quote data. |

#### `get_line_actions`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceProcesses/{processVarName}/documents/{docVarName}/actionDefs` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceProcesses/{processVarName}/documents/{docVarName}/actionDefs` |
| **Tags** | `actions`, `commerce`, `cpq`, `line`, `metadata`, `paginated`, `read` |
| **Parameters** | `process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transactionLine')<br>`expand_all` (bool, default False)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get metadata for actions on a Commerce LINE document (default doc_var_name='transactionLine' — not the main/header document). Returns one page of results (limit/offset). If hasMore is true, call again with offset = offs… |

#### `get_line_attributes`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceProcesses/{processVarName}/documents/{docVarName}/attributes` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceProcesses/{processVarName}/documents/{docVarName}/attributes` |
| **Tags** | `attributes`, `commerce`, `cpq`, `line`, `metadata`, `paginated`, `read` |
| **Parameters** | `process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transactionLine')<br>`expand_all` (bool, default False)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get metadata for attributes on a Commerce LINE document (default doc_var_name='transactionLine' — not the main/header document). Returns one page of results (limit/offset). If hasMore is true, call again with offset = o… |

#### `get_saved_search`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/searchResources/{resourceVarName}/{searchId}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/searchResources/{resourceVarName}/{searchId}` |
| **Tags** | `commerce`, `cpq`, `read`, `saved_search` |
| **Parameters** | `search_id` (int, required)<br>`resource_var_name` (str \| None, default None)<br>`process_var_name` (str \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one saved search by numeric search_id (GET /searchResources/{resource_var_name}/{search_id}). resource_var_name optional — same default derivation as list_saved_searches. Docs target REST v19. Does not modify CPQ da… |

#### `get_transaction`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}` |
| **Tags** | `commerce`, `cpq`, `read`, `transactions` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`expand` (str \| None, default None)<br>`exclude_field_types` (str \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one Commerce transaction by numeric transaction_id. Optional expand / exclude_field_types. Defaults process from profile. |

#### `get_transaction_line`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}` |
| **Tags** | `commerce`, `cpq`, `lines`, `read`, `transactions` |
| **Parameters** | `transaction_id` (str, required)<br>`document_number` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`expand` (str \| None, default None)<br>`exclude_field_types` (str \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get a single transaction line by transaction_id and document_number (line document number). |

#### `list_commerce_processes`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceProcessSetups` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceProcessSetups` |
| **Tags** | `commerce`, `cpq`, `metadata`, `paginated`, `read` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List Commerce process setups (admin metadata). Paginated. Does not list live transactions. |

#### `list_commerce_processes_table`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceProcessSetups` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceProcessSetups` |
| **Tags** | `commerce`, `cpq`, `metadata`, `read`, `table` |
| **Parameters** | `page_size` (int, default 100) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List all Commerce process setups as a flat table with variable_name, name, description, id, and label. Pages until complete. Does not list live transactions. |

#### `list_saved_searches`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/searchResources/{resourceVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/searchResources/{resourceVarName}` |
| **Tags** | `commerce`, `cpq`, `paginated`, `read`, `saved_search` |
| **Parameters** | `resource_var_name` (str \| None, default None)<br>`process_var_name` (str \| None, default None)<br>`show_all` (Literal['ALL', 'HIDDEN', 'VISIBLE', 'INACTIVE'], default 'VISIBLE')<br>`limit` (int, default 100)<br>`offset` (int, default 0)<br>`total_results` (bool, default True) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List saved searches for a commerce document resource (GET /searchResources/{resource_var_name}). Paginated with limit/offset. Optional show_all maps to query showAll (ALL\|HIDDEN\|VISIBLE\|INACTIVE; default VISIBLE). When… |

#### `list_transaction_lines`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/transactionLine` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/transactionLine` |
| **Tags** | `commerce`, `cpq`, `lines`, `paginated`, `read`, `transactions` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0)<br>`total_results` (bool, default True)<br>`fields` (list[str] \| None, default None)<br>`orderby` (list[str] \| None, default None)<br>`expand` (str \| None, default None)<br>`exclude_field_types` (str \| None, default None)<br>`transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction') |
| **Filters** | `q_expr` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List line items for a Commerce transaction. Paginated collection with the same filter params as list_transactions. Empty items means no lines for that id. |

#### `list_transactions`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}` |
| **Tags** | `commerce`, `cpq`, `paginated`, `read`, `transactions` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0)<br>`total_results` (bool, default True)<br>`fields` (list[str] \| None, default None)<br>`orderby` (list[str] \| None, default None)<br>`expand` (str \| None, default None)<br>`exclude_field_types` (str \| None, default None)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction') |
| **Filters** | `q_expr` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List Commerce transactions for the configured process (GET /commerceDocuments{Process}{Doc}). Returns one page; if hasMore is true, call again with offset = offset + limit. Supports q_expr, fields, orderby, expand, excl… |

#### `sync_commerce_metadata_local`

| | |
|---|---|
| **Version** | `1.1.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `PRIVILEGED` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceProcesses/{process}/documents/{doc}/{resource}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceProcesses/{process}/documents/{doc}/{resource}` |
| **Tags** | `commerce`, `cpq`, `excel`, `export`, `local_data`, `read` |
| **Parameters** | `process_var_name` (str \| None, default None)<br>`expand_all` (bool, default True) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Fetch all header/line attributes and actions for a commerce process (paginated) and write JSON + Excel under data/{profile}/{env}/commerce/{process}/. |

### Write tools

#### `add_from_favorites`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None)<br>`action_var_name` (str, default '_s_addFromFavorites_t') |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Add favorites onto a Commerce transaction (POST .../actions/{action_var_name}; default _s_addFromFavorites_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only… |

#### `add_transaction_lines`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `lines`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None)<br>`action_var_name` (str, default 'addLineItem_t') |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Add line items to a Commerce transaction (POST .../actions/{action_var_name}; default addLineItem_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, ret… |

#### `copy_transaction`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/_copy_transaction` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/_copy_transaction` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Copy a Commerce transaction (POST .../actions/_copy_transaction). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview stating this will UPD… |

#### `copy_transaction_lines`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionName}` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `lines`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`action_name` (str, default 'copyLineItems_t')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Copy transaction lines onto a Commerce transaction (POST .../actions/{action_name}; default action_name=copyLineItems_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via… |

#### `create_transaction`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `transactions`, `write` |
| **Parameters** | `process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Create a Commerce transaction/quote (POST /commerceDocuments{Process}{Doc}). Pass documents/attributes in body as required by the site. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks… |

#### `create_transaction_version`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None)<br>`action_var_name` (str, default 'versionTransaction_t') |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Create a Commerce transaction version (POST .../actions/{action_var_name}; default versionTransaction_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs,… |

#### `delete_transaction_line`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `DESTRUCTIVE` |
| **Method** | `DELETE` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `lines`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`document_number` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Delete one transaction line (DELETE .../transactionLine/{documentNumber}). Destructive — permanently removes that line document. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existe… |

#### `display_transaction_history`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None)<br>`action_var_name` (str, required) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Display transaction history via a site-specific action (POST .../actions/{action_var_name}; action_var_name required). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via re… |

#### `export_attachment`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`attribute_var_name` (str, required)<br>`action_var_name` (str, default 'exportAttachment')<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Export/view a CPQ-generated transaction attachment via REST (POST .../actions/{action_var_name}). Requires attribute_var_name (attachment attribute; sent as body selections). Returns JSON (documents/warnings); does not… |

#### `generate_proposal`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/generateProposal` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/generateProposal` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Generate a proposal document for a Commerce transaction (POST .../actions/generateProposal). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a pr… |

#### `interact_transaction_line`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}/actions/_interact` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}/actions/_interact` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `lines`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`document_number` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Interact with a configured transaction line (POST .../transactionLine/{documentNumber}/actions/_interact). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs… |

#### `new_transaction`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/actions/_new_transaction` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/actions/_new_transaction` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `transactions`, `write` |
| **Parameters** | `process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Create a Commerce transaction via the _new_transaction action (POST .../actions/_new_transaction). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, return… |

#### `reconfigure_transaction`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/_reconfigure_action` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/_reconfigure_action` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Reconfigure a Commerce transaction (POST .../actions/_reconfigure_action). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview stating this… |

#### `reconfigure_transaction_line`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}/actions/_reconfigure_action` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}/actions/_reconfigure_action` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `lines`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`document_number` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Reconfigure a transaction line (POST .../transactionLine/{documentNumber}/actions/_reconfigure_action). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, r… |

#### `reconfigure_transaction_line_inbound`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}/actions/_reconfigure_inbound_action` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}/actions/_reconfigure_inbound_action` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `lines`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`document_number` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Inbound reconfigure of a transaction line (POST .../transactionLine/{documentNumber}/actions/_reconfigure_inbound_action). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence vi… |

#### `remove_transaction_lines`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `DESTRUCTIVE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/_remove_transactionLine` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/_remove_transactionLine` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `lines`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Remove transaction lines via action (POST .../actions/_remove_transactionLine). Destructive — removes selected lines from the quote. Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks ex… |

#### `save_transaction`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None)<br>`action_var_name` (str, default 'cleanSave_t') |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Save a Commerce transaction (POST .../actions/{action_var_name}; default cleanSave_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview… |

#### `save_transaction_version`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None)<br>`action_var_name` (str, default 'versionSave_t') |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Save a Commerce transaction version (POST .../actions/{action_var_name}; default versionSave_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns… |

#### `submit_transaction`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None)<br>`action_var_name` (str, default 'submit_t') |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Submit a Commerce transaction for approval (POST .../actions/{action_var_name}; default submit_t). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, return… |

#### `update_transaction_lines`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/_update_line_items` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/commerceDocuments{Process}{Doc}/{id}/actions/_update_line_items` |
| **Tags** | `commerce`, `confirmation`, `cpq`, `dry_run`, `lines`, `transactions`, `write` |
| **Parameters** | `transaction_id` (str, required)<br>`process_var_name` (str \| None, default None)<br>`doc_var_name` (str, default 'transaction')<br>`body` (dict[str, Any] \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Update transaction lines (POST .../actions/_update_line_items). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via read-only GETs, returns a preview stating this will UPDAT… |

## performance

_3 tool(s)_

- **Read:** [`get_performance_log`](#get-performance-log), [`list_performance_logs`](#list-performance-logs)
- **Write:** [`export_performance_logs`](#export-performance-logs)

### Read tools

#### `get_performance_log`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/performanceLogs/{id}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/performanceLogs/{id}` |
| **Tags** | `cpq`, `logs`, `performance`, `read` |
| **Parameters** | `log_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get a single performance log event by numeric id. Does not export CSV and does not create Performance Debugger logs. |

#### `list_performance_logs`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/performanceLogs` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/performanceLogs` |
| **Tags** | `cpq`, `logs`, `paginated`, `performance`, `read` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0)<br>`total_results` (bool, default True)<br>`fields` (list[str] \| None, default None)<br>`orderby` (list[str] \| None, default None) |
| **Filters** | `q_expr` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List Oracle CPQ performance log events (user activity timing / metrics). Returns one page of results. If hasMore is true, call again with offset = offset + limit. Supports collection filters: q_expr (MongoDB q), fields… |

### Write tools

#### `export_performance_logs`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `HIGH_RISK_WRITE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/performanceLogs/actions/export` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/performanceLogs/actions/export` |
| **Tags** | `confirmation`, `cpq`, `dry_run`, `export`, `logs`, `performance`, `write` |
| **Parameters** | `log_id` (str \| None, default None)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | `body` (dict[str, Any] \| None, default None) |
| **Output** | attachment/list (no root object schema) |
| **Description** | Export performance log events via REST. Optional log_id for single event. Does not list logs (use list_performance_logs). Safe execution: defaults to dry_run=true (preflight only — validates inputs, checks existence via… |

## parts

_3 tool(s)_

- **Read:** [`get_part`](#get-part), [`list_parts`](#list-parts), [`search_parts`](#search-parts)

### Read tools

#### `get_part`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/parts/{id}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/parts/{id}` |
| **Tags** | `cpq`, `parts`, `read` |
| **Parameters** | `part_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get a single part by id. |

#### `list_parts`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/parts` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/parts` |
| **Tags** | `cpq`, `paginated`, `parts`, `read` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0)<br>`fields` (list[str] \| None, default None) |
| **Filters** | `q_expr` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List parts from the CPQ site. Returns one page of results. If hasMore is true, call again with offset = offset + limit. |

#### `search_parts`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/parts/actions/search` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/parts/actions/search` |
| **Tags** | `cpq`, `parts`, `read`, `search` |
| **Parameters** | `body` (dict[str, Any], required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Search parts via POST /parts/actions/search with a search body. Not a mutating write; allowed under READ_ONLY via client allowlist. |

## tasks

_2 tool(s)_

- **Read:** [`download_task_file`](#download-task-file), [`get_task`](#get-task)

### Read tools

#### `download_task_file`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/tasks/{taskId}/files/{fileName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/tasks/{taskId}/files/{fileName}` |
| **Tags** | `cpq`, `export`, `read`, `tasks` |
| **Parameters** | `task_id` (str, required)<br>`file_name` (str, required) |
| **Filters** | — |
| **Output** | attachment/list (no root object schema) |
| **Description** | Download a file associated with a task (export zip/log). GET /tasks/{taskId}/files/{fileName}. Returns [envelope, File]. |

#### `get_task`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/tasks/{taskId}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/tasks/{taskId}` |
| **Tags** | `cpq`, `read`, `tasks` |
| **Parameters** | `task_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get task status/details by task_id (e.g. after export_datatables). GET /tasks/{taskId}. |

## configuration

_17 tool(s)_

- **Read:** [`get_array_set`](#get-array-set), [`get_array_set_attribute`](#get-array-set-attribute), [`get_config_attribute`](#get-config-attribute), [`get_config_layout`](#get-config-layout), [`get_config_menu_item`](#get-config-menu-item), [`get_layout_cache_attributes`](#get-layout-cache-attributes), [`get_model`](#get-model), [`get_product_family`](#get-product-family), [`get_product_line`](#get-product-line), [`list_array_set_attributes`](#list-array-set-attributes), [`list_array_sets`](#list-array-sets), [`list_config_attributes`](#list-config-attributes), [`list_config_menu_items`](#list-config-menu-items), [`list_models`](#list-models), [`list_product_families`](#list-product-families), [`list_product_hierarchy_table`](#list-product-hierarchy-table), [`list_product_lines`](#list-product-lines)

### Read tools

#### `get_array_set`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/.../arraySets/{arraySetVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/.../arraySets/{arraySetVarName}` |
| **Tags** | `arraySets`, `configuration`, `cpq`, `read` |
| **Parameters** | `scope` (Literal['family', 'line', 'model'], required)<br>`prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str \| None, default None)<br>`model_var_name` (str \| None, default None)<br>`array_set_var_name` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one array set at scope family\|line\|model. |

#### `get_array_set_attribute`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/.../arraySets/{arraySetVarName}/attributes/{attributeVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/.../arraySets/{arraySetVarName}/attributes/{attributeVarName}` |
| **Tags** | `arraySets`, `attributes`, `configuration`, `cpq`, `read` |
| **Parameters** | `scope` (Literal['family', 'line', 'model'], required)<br>`prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str \| None, default None)<br>`model_var_name` (str \| None, default None)<br>`array_set_var_name` (str, required)<br>`attribute_var_name` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one array-set attribute at scope family\|line\|model. |

#### `get_config_attribute`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/.../attributes/{attributeVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/.../attributes/{attributeVarName}` |
| **Tags** | `attributes`, `configuration`, `cpq`, `read` |
| **Parameters** | `scope` (Literal['family', 'line', 'model'], required)<br>`prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str \| None, default None)<br>`model_var_name` (str \| None, default None)<br>`attribute_var_name` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one configuration attribute at scope family\|line\|model by attribute_var_name. |

#### `get_config_layout`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/.../layouts/{layoutVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/.../layouts/{layoutVarName}` |
| **Tags** | `configuration`, `cpq`, `layouts`, `read` |
| **Parameters** | `scope` (Literal['family', 'line', 'model'], required)<br>`prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str \| None, default None)<br>`model_var_name` (str \| None, default None)<br>`layout_var_name` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get a configuration layout by layout_var_name at scope family\|line\|model. |

#### `get_config_menu_item`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/.../menuItems/{menuItemId}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/.../menuItems/{menuItemId}` |
| **Tags** | `configuration`, `cpq`, `menuItems`, `read` |
| **Parameters** | `scope` (Literal['family', 'line', 'model'], required)<br>`prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str \| None, default None)<br>`model_var_name` (str \| None, default None)<br>`parent_kind` (Literal['attribute', 'array_set_attribute'], required)<br>`attribute_var_name` (str, required)<br>`menu_item_id` (str, required)<br>`array_set_var_name` (str \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one menu item by menu_item_id for an attribute or array-set attribute at scope family\|line\|model. |

#### `get_layout_cache_attributes`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/layoutcache/{prodFamVarName}/{prodLineVarName}/{modelVarName}/attributes` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/layoutcache/{prodFamVarName}/{prodLineVarName}/{modelVarName}/attributes` |
| **Tags** | `configuration`, `cpq`, `layouts`, `read` |
| **Parameters** | `prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str, required)<br>`model_var_name` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get layout-cache attributes for a model via GET /layoutcache/{fam}/{line}/{model}/attributes. |

#### `get_model`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/{prodFamVarName}/productLines/{prodLineVarName}/models/{modelVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/{prodFamVarName}/productLines/{prodLineVarName}/models/{modelVarName}` |
| **Tags** | `configuration`, `cpq`, `metadata`, `read` |
| **Parameters** | `prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str, required)<br>`model_var_name` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one model by family, line, and model variable names. |

#### `get_product_family`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/{prodFamVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/{prodFamVarName}` |
| **Tags** | `configuration`, `cpq`, `metadata`, `read` |
| **Parameters** | `prod_fam_var_name` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one product family by prod_fam_var_name. |

#### `get_product_line`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/{prodFamVarName}/productLines/{prodLineVarName}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/{prodFamVarName}/productLines/{prodLineVarName}` |
| **Tags** | `configuration`, `cpq`, `metadata`, `read` |
| **Parameters** | `prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one product line by family + line variable names. |

#### `list_array_set_attributes`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/.../arraySets/{arraySetVarName}/attributes` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/.../arraySets/{arraySetVarName}/attributes` |
| **Tags** | `arraySets`, `attributes`, `configuration`, `cpq`, `read` |
| **Parameters** | `scope` (Literal['family', 'line', 'model'], required)<br>`prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str \| None, default None)<br>`model_var_name` (str \| None, default None)<br>`array_set_var_name` (str, required)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List attributes of an array set at scope family\|line\|model. |

#### `list_array_sets`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/.../arraySets` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/.../arraySets` |
| **Tags** | `arraySets`, `configuration`, `cpq`, `read` |
| **Parameters** | `scope` (Literal['family', 'line', 'model'], required)<br>`prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str \| None, default None)<br>`model_var_name` (str \| None, default None)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List array sets at scope family\|line\|model. |

#### `list_config_attributes`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/.../attributes` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/.../attributes` |
| **Tags** | `attributes`, `configuration`, `cpq`, `read` |
| **Parameters** | `scope` (Literal['family', 'line', 'model'], required)<br>`prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str \| None, default None)<br>`model_var_name` (str \| None, default None)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List configuration attributes at scope family\|line\|model (composite path under /productFamilies/.../attributes). |

#### `list_config_menu_items`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/.../menuItems` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/.../menuItems` |
| **Tags** | `configuration`, `cpq`, `menuItems`, `read` |
| **Parameters** | `scope` (Literal['family', 'line', 'model'], required)<br>`prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str \| None, default None)<br>`model_var_name` (str \| None, default None)<br>`parent_kind` (Literal['attribute', 'array_set_attribute'], required)<br>`attribute_var_name` (str, required)<br>`array_set_var_name` (str \| None, default None)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List menu items for an attribute or array-set attribute (parent_kind=attribute\|array_set_attribute) at scope family\|line\|model. |

#### `list_models`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/{prodFamVarName}/productLines/{prodLineVarName}/models` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/{prodFamVarName}/productLines/{prodLineVarName}/models` |
| **Tags** | `configuration`, `cpq`, `metadata`, `read` |
| **Parameters** | `prod_fam_var_name` (str, required)<br>`prod_line_var_name` (str, required)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List models under a product family/line. |

#### `list_product_families`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies` |
| **Tags** | `configuration`, `cpq`, `metadata`, `read` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List product family metadata via GET /productFamilies. |

#### `list_product_hierarchy_table`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/.../productLines/.../models` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/.../productLines/.../models` |
| **Tags** | `configuration`, `cpq`, `metadata`, `read`, `table` |
| **Parameters** | `page_size` (int, default 100) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Walk all product families → lines → models and return a flat table of variable names and display names (one row per model; empty model columns when a family/line has no models). Pages CPQ collections. Does not write pro… |

#### `list_product_lines`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/productFamilies/{prodFamVarName}/productLines` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/productFamilies/{prodFamVarName}/productLines` |
| **Tags** | `configuration`, `cpq`, `metadata`, `read` |
| **Parameters** | `prod_fam_var_name` (str, required)<br>`limit` (int, default 100)<br>`offset` (int, default 0) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List product lines under a product family. |

## metrics

_1 tool(s)_

- **Read:** [`list_metrics`](#list-metrics)

### Read tools

#### `list_metrics`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/metrics` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/metrics` |
| **Tags** | `cpq`, `metrics`, `paginated`, `read` |
| **Parameters** | `limit` (int, default 100)<br>`offset` (int, default 0)<br>`total_results` (bool, default True) |
| **Filters** | `name` (str \| None, default None)<br>`start_time` (str \| None, default None)<br>`end_time` (str \| None, default None)<br>`date_modified_from` (str \| None, default None)<br>`date_modified_to` (str \| None, default None)<br>`date_added_from` (str \| None, default None)<br>`date_added_to` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List Oracle CPQ site metrics (GET /metrics). Returns one page of items (name, value, startTime, endTime, dateModified, dateAdded). Optional filters: name (exact), start_time/end_time, date_modified_from/to, date_added_f… |

## collab

_2 tool(s)_

- **Read:** [`get_collab_operation_queue`](#get-collab-operation-queue)
- **Write:** [`clear_collab_operation_queue`](#clear-collab-operation-queue)

### Read tools

#### `get_collab_operation_queue`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/collabOperationQueues/{bs_id}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/collabOperationQueues/{bs_id}` |
| **Tags** | `collab`, `cpq`, `queue`, `read` |
| **Parameters** | `bs_id` (int, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get the collaborative quote operation queue for a commerce document (GET /collabOperationQueues/{bs_id}). Returns queuedOperations, currentlyExecutingOperation, operationCount, and node. Requires a REST version that exp… |

### Write tools

#### `clear_collab_operation_queue`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `write` / `DESTRUCTIVE` |
| **Method** | `POST` |
| **CPQ REST URL** | `/rest/{rest_api_version}/collabOperationQueues/{bs_id}/actions/clearCurrentQueue` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/collabOperationQueues/{bs_id}/actions/clearCurrentQueue` |
| **Tags** | `collab`, `confirmation`, `cpq`, `dry_run`, `queue`, `write` |
| **Parameters** | `bs_id` (int, required)<br>`dry_run` (bool, default True)<br>`confirmation_token` (str \| None, default None) |
| **Filters** | — |
| **Output** | write envelope `{status, tool, data}` |
| **Description** | Clear the collaborative quote operation queue for a commerce document (POST /collabOperationQueues/{bs_id}/actions/clearCurrentQueue). Destructive — removes queued/current collab operations for that bs_id. Safe executio… |

## admin

_4 tool(s)_

- **Read:** [`get_certificate`](#get-certificate), [`get_fusion_access_token`](#get-fusion-access-token), [`get_sso_configuration`](#get-sso-configuration), [`list_certificates`](#list-certificates)

### Read tools

#### `get_certificate`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/certificates/{name}` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/certificates/{name}` |
| **Tags** | `admin`, `certificates`, `cpq`, `read` |
| **Parameters** | `name` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one site certificate by name (GET /certificates/{name}). PEM/certificate material is redacted ([REDACTED]) in MCP responses. Docs target REST v19. Read-only. |

#### `get_fusion_access_token`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `admin`, `fusion`, `meta`, `oauth`, `read` |
| **Parameters** | `include_token` (bool, default False) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Obtain an IDCS/Fusion OAuth access token for the active profile when cpq_mode=fusion and fusion_enabled=true (client_credentials using oauth_* fields from the current environment). Returns token_type, expires_in, scope,… |

#### `get_sso_configuration`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/ssoConfiguration` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/ssoConfiguration` |
| **Tags** | `admin`, `cpq`, `read`, `sso` |
| **Parameters** | — |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get site SSO configuration (GET /ssoConfiguration). IdP certificate and SAML keystore fields are redacted ([REDACTED]) in MCP responses. Docs target REST v19. Read-only; does not change SSO settings. |

#### `list_certificates`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `cpq` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | `/rest/{rest_api_version}/certificates` |
| **Fusion REST URL** | `/cpq/rest/{rest_api_version}/certificates` |
| **Tags** | `admin`, `certificates`, `cpq`, `read` |
| **Parameters** | — |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List site certificates (GET /certificates). PEM/certificate material in responses is redacted ([REDACTED]) before reaching the LLM. Docs target REST v19 (set REST_API_VERSION=v19 if v18 returns 404). Read-only; does not… |

## sales

_14 tool(s)_

- **Read:** [`get_account`](#get-account), [`get_account_team_member`](#get-account-team-member), [`get_contact`](#get-contact), [`get_lead`](#get-lead), [`get_lead_opportunity`](#get-lead-opportunity), [`get_product`](#get-product), [`get_territory`](#get-territory), [`list_account_team`](#list-account-team), [`list_accounts`](#list-accounts), [`list_contacts`](#list-contacts), [`list_lead_opportunities`](#list-lead-opportunities), [`list_leads`](#list-leads), [`list_products`](#list-products), [`list_territories`](#list-territories)

### Read tools

#### `get_account`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/accounts/{PartyNumber}` |
| **Tags** | `accounts`, `cx`, `read`, `sales` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`party_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one Fusion CX Sales account by party_number (PartyNumber). Requires Sales in cx.modules. |

#### `get_account_team_member`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/accounts/{PartyNumber}/child/AccountTeam/{AccountTeamUniqId}` |
| **Tags** | `accounts`, `cx`, `read`, `sales` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`party_number` (str, required)<br>`account_team_uniq_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one account team member by party_number and account_team_uniq_id. |

#### `get_contact`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/contacts/{PartyNumber}` |
| **Tags** | `contacts`, `cx`, `read`, `sales` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`party_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one contact by party_number. |

#### `get_lead`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/leads/{leadsUniqID}` |
| **Tags** | `cx`, `leads`, `read`, `sales` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`leads_uniq_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one lead by leads_uniq_id from the leads collection (ADF uniq id in links). |

#### `get_lead_opportunity`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/leads/{leadsUniqID}/child/LeadOpportunity/{LeadNumber}` |
| **Tags** | `cx`, `leads`, `read`, `sales` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`leads_uniq_id` (str, required)<br>`lead_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one lead opportunity by leads_uniq_id and lead_number. |

#### `get_product`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/products/{InventoryItemId}` |
| **Tags** | `cx`, `products`, `read`, `sales` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`inventory_item_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one product by inventory_item_id. |

#### `get_territory`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/territories/{TerritoryVersionId}` |
| **Tags** | `cx`, `read`, `sales`, `territories` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`territory_version_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one Fusion CX Sales territory by territory_version_id (TerritoryVersionId path key). Requires cx.enabled and Sales in cx.modules. Optional fields, only_data, expand. |

#### `list_account_team`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/accounts/{PartyNumber}/child/AccountTeam` |
| **Tags** | `accounts`, `cx`, `paginated`, `read`, `sales` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False)<br>`party_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List account team members for an account (child AccountTeam). Requires Sales in cx.modules. |

#### `list_accounts`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/accounts` |
| **Tags** | `accounts`, `cx`, `paginated`, `read`, `sales` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List Fusion CX Sales accounts (GET accounts collection). Requires Sales in cx.modules. Paginated; supports q, finder, fields, order_by, only_data, total_results. |

#### `list_contacts`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/contacts` |
| **Tags** | `contacts`, `cx`, `paginated`, `read`, `sales` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List Fusion CX Sales contacts. Requires Sales in cx.modules. Paginated collection filters. |

#### `list_lead_opportunities`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/leads/{leadsUniqID}/child/LeadOpportunity` |
| **Tags** | `cx`, `leads`, `paginated`, `read`, `sales` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False)<br>`leads_uniq_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List lead opportunities for a lead (child LeadOpportunity). |

#### `list_leads`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/leads` |
| **Tags** | `cx`, `leads`, `paginated`, `read`, `sales` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False) |
| **Filters** | `effective_date` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List Fusion CX Sales leads. Optional effective_date (yyyy-MM-dd). leads_uniq_id for get_lead comes from collection links — do not invent. |

#### `list_products`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/products` |
| **Tags** | `cx`, `paginated`, `products`, `read`, `sales` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List Fusion CX Sales products (inventory items). Paginated. |

#### `list_territories`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `sales` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Sales REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/territories` |
| **Tags** | `cx`, `paginated`, `read`, `sales`, `territories` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List Fusion CX Sales territories (GET /crmRestApi/resources/11.13.18.05/territories) via the profile cx: connection (Basic or Bearer). Requires cx.enabled and Sales in cx.modules. Returns one page; if hasMore is true, c… |

## prm

_17 tool(s)_

- **Read:** [`get_deal`](#get-deal), [`get_partner`](#get-partner), [`get_partner_contact`](#get-partner-contact), [`get_partner_contact_address`](#get-partner-contact-address), [`get_partner_contact_attachment`](#get-partner-contact-attachment), [`get_partner_contact_contact_point`](#get-partner-contact-contact-point), [`get_partner_contact_user_detail`](#get-partner-contact-user-detail), [`get_partner_program`](#get-partner-program), [`list_deals`](#list-deals), [`list_partner_contact_addresses`](#list-partner-contact-addresses), [`list_partner_contact_attachments`](#list-partner-contact-attachments), [`list_partner_contact_contact_points`](#list-partner-contact-contact-points), [`list_partner_contact_user_details`](#list-partner-contact-user-details), [`list_partner_contacts`](#list-partner-contacts), [`list_partner_lov`](#list-partner-lov), [`list_partner_programs`](#list-partner-programs), [`list_partners`](#list-partners)

### Read tools

#### `get_deal`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/deals/{dealsUniqID}` |
| **Tags** | `cx`, `deals`, `prm`, `read` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`deals_uniq_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one deal registration by deals_uniq_id from the deals collection. |

#### `get_partner`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partners/{CompanyNumber}` |
| **Tags** | `cx`, `partners`, `prm`, `read` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`company_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one partner by company_number. |

#### `get_partner_contact`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}` |
| **Tags** | `cx`, `partners`, `prm`, `read` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`party_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one partner contact by party_number. |

#### `get_partner_contact_address`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/addresses/{AddressNumber}` |
| **Tags** | `cx`, `partners`, `prm`, `read` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`party_number` (str, required)<br>`address_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one partner-contact address by party_number and address_number. |

#### `get_partner_contact_attachment`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/attachments/{attachmentsUniqID}` |
| **Tags** | `cx`, `partners`, `prm`, `read` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`party_number` (str, required)<br>`attachments_uniq_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one partner-contact attachment by party_number and attachments_uniq_id (from attachments collection links). Does not invent hash keys. |

#### `get_partner_contact_contact_point`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/contactPoints/{ContactPointId}` |
| **Tags** | `cx`, `partners`, `prm`, `read` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`party_number` (str, required)<br>`contact_point_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one partner-contact contact point by party_number and contact_point_id. |

#### `get_partner_contact_user_detail`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/userdetails/{Username}` |
| **Tags** | `cx`, `partners`, `prm`, `read` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`party_number` (str, required)<br>`username` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one partner-contact user-detail row by party_number and username (Username path key; @ is URL-encoded). |

#### `get_partner_program`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partnerPrograms/{ProgramNumber}` |
| **Tags** | `cx`, `partners`, `prm`, `read` |
| **Parameters** | `fields` (str \| None, default None)<br>`only_data` (bool, default True)<br>`expand` (str \| None, default None)<br>`program_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Get one partner program by program_number (ProgramNumber path key). |

#### `list_deals`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/deals` |
| **Tags** | `cx`, `deals`, `paginated`, `prm`, `read` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False) |
| **Filters** | `effective_date` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List PRM deal registrations. Optional effective_date. deals_uniq_id for get_deal comes from collection links — do not invent. |

#### `list_partner_contact_addresses`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/addresses` |
| **Tags** | `cx`, `paginated`, `partners`, `prm`, `read` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False)<br>`party_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List addresses for a PRM partner contact (child addresses). Requires party_number and PRM in cx.modules. Paginated ADF collection filters. |

#### `list_partner_contact_attachments`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/attachments` |
| **Tags** | `cx`, `paginated`, `partners`, `prm`, `read` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False)<br>`party_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List attachment metadata for a PRM partner contact (child attachments). attachments_uniq_id for get_partner_contact_attachment comes from collection links — do not invent. Does not download attachment binary content. |

#### `list_partner_contact_contact_points`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/contactPoints` |
| **Tags** | `cx`, `paginated`, `partners`, `prm`, `read` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False)<br>`party_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List contact points (phone/email) for a PRM partner contact (child contactPoints). Requires party_number and PRM in cx.modules. |

#### `list_partner_contact_user_details`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/userdetails` |
| **Tags** | `cx`, `paginated`, `partners`, `prm`, `read` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False)<br>`party_number` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List user-account details for a PRM partner contact (child userdetails). Requires party_number and PRM in cx.modules. |

#### `list_partner_contacts`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partnerContacts` |
| **Tags** | `cx`, `paginated`, `partners`, `prm`, `read` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List PRM partner contacts (partnerContacts collection). Requires PRM in cx.modules. |

#### `list_partner_lov`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partners/{CompanyNumber}/lov/{LovName}` |
| **Tags** | `cx`, `paginated`, `partners`, `prm`, `read` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False)<br>`company_number` (str, required)<br>`lov_name` (str, required) |
| **Filters** | `lookup_code` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List Fusion CX PRM partner ADF LOV rows (GET partners/{CompanyNumber}/lov/{LovName}). Use after list_partners/get_partner to resolve LookupCode values to Meaning/DisplayLabel. For field PartnerProfilePEO_<suffix>, lov_n… |

#### `list_partner_programs`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partnerPrograms` |
| **Tags** | `cx`, `paginated`, `partners`, `prm`, `read` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List Fusion CX PRM partner programs (GET partnerPrograms). Requires PRM in cx.modules. Paginated; supports q, finder, fields, order_by, only_data, total_results. |

#### `list_partners`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `prm` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | `GET` |
| **CPQ REST URL** | — (CX Prm REST; not CPQ) |
| **Fusion REST URL** | `/crmRestApi/resources/11.13.18.05/partners` |
| **Tags** | `cx`, `paginated`, `partners`, `prm`, `read` |
| **Parameters** | `limit` (int, default 25)<br>`offset` (int, default 0)<br>`q` (str \| None, default None)<br>`finder` (str \| None, default None)<br>`fields` (str \| None, default None)<br>`order_by` (str \| None, default None)<br>`only_data` (bool, default True)<br>`total_results` (bool, default False) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List Fusion CX PRM partners. Requires PRM in cx.modules. |

## meta

_24 tool(s)_

- **Read:** [`append_customer_knowledge`](#append-customer-knowledge), [`discover_tools`](#discover-tools), [`ensure_customer_knowledge`](#ensure-customer-knowledge), [`ensure_prompt_studio`](#ensure-prompt-studio), [`export_response_excel`](#export-response-excel), [`export_response_word`](#export-response-word), [`get_customer_knowledge`](#get-customer-knowledge), [`get_local_data_status`](#get-local-data-status), [`get_local_job`](#get-local-job), [`get_saved_prompt`](#get-saved-prompt), [`list_local_data`](#list-local-data), [`list_saved_prompts`](#list-saved-prompts), [`load_local_data`](#load-local-data), [`offer_export_response`](#offer-export-response), [`offer_save_refined_prompt`](#offer-save-refined-prompt), [`offer_use_local_data`](#offer-use-local-data), [`record_prompt_use`](#record-prompt-use), [`save_refined_prompt`](#save-refined-prompt), [`search_saved_prompts`](#search-saved-prompts), [`set_auto_save_refined_prompt`](#set-auto-save-refined-prompt), [`set_local_data_policy`](#set-local-data-policy), [`set_post_response_export`](#set-post-response-export), [`set_saved_prompt_enabled`](#set-saved-prompt-enabled), [`start_prompt_picker`](#start-prompt-picker)

### Read tools

#### `append_customer_knowledge`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `knowledge`, `memory`, `meta`, `read` |
| **Parameters** | `summary` (str, required)<br>`title` (str \| None, default None)<br>`tags` (list[str] \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Append a dated markdown discovery entry to the active profile customer knowledge file (env-tagged). Rejects secret-like content. Caps entry size. Auto-ensures stub + profile field when missing. Does not call Oracle CPQ.… |

#### `discover_tools`

| | |
|---|---|
| **Version** | `1.0.2` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `discovery`, `meta`, `read` |
| **Parameters** | `limit` (int, default 20) |
| **Filters** | `query` (str \| None, default None)<br>`domain` (Literal['users', 'groups', 'datatables', 'bml', 'commerce', 'performance', …], default 'all')<br>`operation` (Literal['read', 'write', 'all'], default 'all')<br>`cx_module` (Literal['cpq', 'sales', 'prm', 'service', 'field_service', 'subscription', …], default 'all') |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Search and filter the Oracle CPQ MCP tool catalog by domain (users/groups/datatables/bml/commerce/performance/parts/tasks/configuration/metrics/collab/admin/sales/prm/…), cx_module (cpq/sales/prm/service/field_service/s… |

#### `ensure_customer_knowledge`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `knowledge`, `memory`, `meta`, `read` |
| **Parameters** | — |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Create knowledge/{customer_id}.md stub if missing and set profile customer_knowledge_file when unset (allowlisted YAML/.env rewrite). Idempotent when already configured. Does not call Oracle CPQ. Reload MCP so injected… |

#### `ensure_prompt_studio`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `meta`, `prompt_studio`, `read`, `saved_prompts` |
| **Parameters** | — |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Probe local Prompt Studio (GET http://127.0.0.1:8765/api/health by default) and auto-start it in the background if it is not running (python -m apps.prompt_studio). Returns running/started, url, host, port, optional pid… |

#### `export_response_excel`

| | |
|---|---|
| **Version** | `1.1.0` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `excel`, `export`, `meta`, `read` |
| **Parameters** | `title` (str, required)<br>`sheets` (list[ExportResponseSheetInput], required)<br>`notes` (str \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Build a multi-sheet Excel (.xlsx) from structured sheets [{name, columns?, rows}] and write under data/{profile}/{env}/exports/. Returns a success envelope with path, absolute_path, and file:// uri (no MCP File attachme… |

#### `export_response_word`

| | |
|---|---|
| **Version** | `1.4.0` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `export`, `meta`, `read` |
| **Parameters** | `title` (str, required)<br>`sheets` (list[ExportResponseSheetInput], required)<br>`notes` (str \| None, default None)<br>`diagrams` (list[ExportResponseDiagramInput] \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Build a Word (.docx) from structured sheets (optional notes) and optional diagrams [{title, mermaid?, image_path?, caption?}] and write under data/{profile}/{env}/exports/. Mermaid is rasterized locally via mmdc (@merma… |

#### `get_customer_knowledge`

| | |
|---|---|
| **Version** | `1.0.0` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `knowledge`, `memory`, `meta`, `read` |
| **Parameters** | — |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Read the active profile's customer knowledge markdown under knowledge/ (cross-session engagement memory). Returns path, text, and character_count. Does not call Oracle CPQ. Use before repeating discovery work. |

#### `get_local_data_status`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `local_data`, `meta`, `read` |
| **Parameters** | `process_var_name` (str \| None, default None)<br>`table_name` (str \| None, default None) |
| **Filters** | `domain` (Literal['users', 'groups', 'bml', 'commerce', 'datatables'], required) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Check whether a local snapshot exists for a domain (users/groups/bml/commerce/datatables). For commerce pass process_var_name; for datatables pass table_name. Does not call Oracle CPQ. |

#### `get_local_job`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `async`, `local_data`, `meta`, `read` |
| **Parameters** | `job_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Poll an MCP-local background job started by start_bml_site_export (or future local job starters). Returns status queued\|running\|succeeded\|failed plus result paths or error. Does not call Oracle CPQ. For Oracle CPQ async… |

#### `get_saved_prompt`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `meta`, `read`, `saved_prompts` |
| **Parameters** | `prompt_id` (str, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Load one saved refined prompt by id, including refined_prompt text and variables. Does not call Oracle CPQ. |

#### `list_local_data`

| | |
|---|---|
| **Version** | `1.1.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `discovery`, `local_data`, `meta`, `read` |
| **Parameters** | — |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List local data/{profile}/{env} snapshots (manifests) for the active profile. Does not call Oracle CPQ. Use before live list/export tools when LOCAL_DATA_POLICY is ask or prefer. |

#### `list_saved_prompts`

| | |
|---|---|
| **Version** | `1.1.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `meta`, `read`, `saved_prompts` |
| **Parameters** | `limit` (int, default 50) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | List locally saved refined prompts (title, tags, tools, last_run). Does not call Oracle CPQ. Library file defaults to .prompts/saved_prompts.json. |

#### `load_local_data`

| | |
|---|---|
| **Version** | `1.1.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `local_data`, `meta`, `read` |
| **Parameters** | `process_var_name` (str \| None, default None)<br>`table_name` (str \| None, default None)<br>`include_payload` (bool, default False)<br>`payload_keys` (list[str] \| None, default None) |
| **Filters** | `domain` (Literal['users', 'groups', 'bml', 'commerce', 'datatables'], required) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Load a local snapshot summary and file paths under data/. Default omits large payloads (include_payload=false) to save tokens. Does not call Oracle CPQ. |

#### `offer_export_response`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `excel`, `export`, `local_data`, `meta`, `read` |
| **Parameters** | `title` (str, required)<br>`sheets` (list[ExportResponseSheetInput] \| None, default None)<br>`notes` (str \| None, default None)<br>`choice` (Literal['excel', 'word', 'both', 'skip', 'always_excel', 'never'] \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | After a tabular chat answer, offer to export structured sheets to Excel and/or Word. Omit choice for needs_user_input (excel / word / both / skip / always_excel / never). always_excel/never also write POST_RESPONSE_EXPO… |

#### `offer_save_refined_prompt`

| | |
|---|---|
| **Version** | `1.2.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `meta`, `read`, `saved_prompts` |
| **Parameters** | `title` (str, required)<br>`original_user_prompt` (str, required)<br>`refined_prompt` (str, required)<br>`variables` (dict[str, Any] \| None, default None)<br>`tags` (list[str] \| None, default None)<br>`tools` (list[str] \| None, default None)<br>`output_format` (Literal['chat_text', 'json', 'excel_download'], default 'chat_text')<br>`save` (bool \| None, default None)<br>`always` (bool \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Offer to save a refined prompt after a CPQ-related task. If save is omitted, returns needs_user_input with choices: save once, save and always auto-save, or skip (chat fallback when elicitation is unavailable). With sav… |

#### `offer_use_local_data`

| | |
|---|---|
| **Version** | `1.1.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `local_data`, `meta`, `read` |
| **Parameters** | `process_var_name` (str \| None, default None)<br>`table_name` (str \| None, default None)<br>`choice` (Literal['use_cache', 'fetch_fresh', 'prefer', 'never'] \| None, default None) |
| **Filters** | `domain` (Literal['users', 'groups', 'bml', 'commerce', 'datatables'], required) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Ask whether to use a local data/ snapshot or fetch fresh CPQ data. Omit choice for needs_user_input (use_cache / fetch_fresh / prefer / never). prefer/never also write LOCAL_DATA_POLICY on the profile .env. Does not cal… |

#### `record_prompt_use`

| | |
|---|---|
| **Version** | `1.1.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `meta`, `read`, `saved_prompts` |
| **Parameters** | `prompt_id` (str, required)<br>`duration_ms` (int \| None, default None)<br>`source` (Literal['cache', 'api', 'mixed'] \| None, default None)<br>`profile` (str \| None, default None)<br>`environment` (Literal['dev', 'test', 'prod'] \| None, default None) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Record a completed saved-prompt run after the agent finishes the task. Updates last_run_at and run_count. When duration_ms and source are set (source=cache\|api\|mixed), also appends run history and updates that source's… |

#### `save_refined_prompt`

| | |
|---|---|
| **Version** | `1.2.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `meta`, `read`, `saved_prompts` |
| **Parameters** | `title` (str, required)<br>`original_user_prompt` (str, required)<br>`refined_prompt` (str, required)<br>`variables` (dict[str, Any] \| None, default None)<br>`tags` (list[str] \| None, default None)<br>`tools` (list[str] \| None, default None)<br>`output_format` (Literal['chat_text', 'json', 'excel_download'], default 'chat_text') |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Save a refined prompt (title, original user prompt, refined text, variables, tags, tools, output_format) into the local library. output_format is chat_text (default), json, or excel_download. Dedupes by content hash (in… |

#### `search_saved_prompts`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `meta`, `read`, `saved_prompts`, `search` |
| **Parameters** | `limit` (int, default 20) |
| **Filters** | `query` (str \| None, default None)<br>`tag` (str \| None, default None)<br>`tool_domain` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Search saved refined prompts by title text, tag, and/or tool domain. Does not call Oracle CPQ. |

#### `set_auto_save_refined_prompt`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `meta`, `read`, `saved_prompts` |
| **Parameters** | `enabled` (bool, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Set AUTO_SAVE_REFINED_PROMPT=true\|false on the active customer profile .env (allowlisted key rewrite only). Does not call Oracle CPQ. Treat the tool result as source of truth for the rest of this session; reload MCP if… |

#### `set_local_data_policy`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `local_data`, `meta`, `read` |
| **Parameters** | `policy` (Literal['ask', 'prefer', 'never'], required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Set LOCAL_DATA_POLICY=ask\|prefer\|never on the active customer profile .env (allowlisted key rewrite only). Does not call Oracle CPQ. Reload MCP if you need server instructions rebuilt from the new flag. |

#### `set_post_response_export`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `export`, `local_data`, `meta`, `read` |
| **Parameters** | `policy` (Literal['ask', 'never', 'always_excel'], required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Set POST_RESPONSE_EXPORT=ask\|never\|always_excel on the active customer profile .env (allowlisted key rewrite only). Does not call Oracle CPQ. Reload MCP if you need server instructions rebuilt from the new flag. |

#### `set_saved_prompt_enabled`

| | |
|---|---|
| **Version** | `1.0.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `meta`, `read`, `saved_prompts` |
| **Parameters** | `prompt_id` (str, required)<br>`enabled` (bool, required) |
| **Filters** | — |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Enable or disable a saved refined prompt by id. Disabled prompts are hidden from list/search/picker. Local library file only; does not call Oracle CPQ. |

#### `start_prompt_picker`

| | |
|---|---|
| **Version** | `1.1.1` |
| **CX module** | `meta` |
| **Op / Risk** | `read` / `READ_ONLY` |
| **Method** | — |
| **CPQ REST URL** | — (local / no CPQ REST) |
| **Fusion REST URL** | — (local / no CPQ REST) |
| **Tags** | `discovery`, `meta`, `read`, `saved_prompts` |
| **Parameters** | `mode` (str \| None, default None)<br>`prompt_id` (str \| None, default None) |
| **Filters** | `query` (str \| None, default None)<br>`tag` (str \| None, default None)<br>`tool_domain` (str \| None, default None)<br>`tool` (str \| None, default None) |
| **Output** | read envelope `{status, tool, data}` |
| **Description** | Interactively pick an enabled saved refined prompt: all (by title), search, by_tag, by_tool (also last5 / by_domain). Omit mode for the top-level menu; pass prompt_id to load and record use. Disabled prompts are hidden.… |

---

## Regeneration

After adding or changing tools in `mcp/oracle_cpq_mcp/registry/tool_registry.py` (and matching input models), run:

```bash
oracle-cpq generate-tool-catalog
# or: python scripts/generate_tool_catalog.py
```
