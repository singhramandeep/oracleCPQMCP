# Oracle CPQ MCP Server

MCP server for **Oracle CPQ** — exposes **Users**, **Groups**, **Data Tables**, **BML**, and **Commerce metadata** REST APIs to AI agents (Cursor, VS Code Copilot, Google Antigravity, and other MCP clients).

## Get started

**New here?** Follow the full walkthrough:

**[docs/QUICKSTART.md](docs/QUICKSTART.md)** — download repo, create credential profile, smoke test, and wire Cursor / VS Code / Antigravity step by step.

Quick smoke test after install — run in the **IDE integrated terminal** (`` Ctrl+` ``, repo root):

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

## Documentation

| Document | Contents |
|----------|----------|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | **Start here** — clone, credentials, IDE setup, sample agent prompts |
| [docs/SETUP.md](docs/SETUP.md) | Short setup summary |
| [SECURITY.md](SECURITY.md) | Guardrails, confirmation tokens, audit |
| [SECURITY_TESTING.md](SECURITY_TESTING.md) | Security test suite and CI |
| [THREAT_MODEL.md](THREAT_MODEL.md) | STRIDE / MCP threat analysis |
| [.config/.env.example](.config/.env.example) | CPQ profile field reference |

## Features

- **19 MCP tools** — users, groups, data tables, BML export, commerce metadata, tool discovery
- **Read-only by default** — profile `READ_ONLY=true` blocks all mutations
- **Safe writes** — preflight + HMAC `confirmation_token` (when writes enabled)
- **Structured errors** — `{status, code, message, hint, details}` (no stack traces)
- **Consistent output envelopes** — read/write tools return MCP object payloads (`status`, `tool`, `data`; errors use `status: error`)
- **Server-side security** — validation, rate limits, replay protection, output redaction, post-execution output schema validation

## MCP tools (summary)

**19 tools** across six domains. Use `discover_tools(domain="users", operation="read")`, `discover_tools(domain="bml")`, or `discover_tools(domain="commerce")` in Agent mode to filter the catalog.

Write tools default to **dry-run preflight** (`dry_run=true`). Mutations require user confirmation, `dry_run=false`, and a `confirmation_token` from preflight. Blocked when `READ_ONLY=true` (default).

BML zip export returns `[object envelope, File attachment]`. Commerce tools default `process_var_name` from `COMMERCE_PROCESS_VAR_NAME` in your profile.

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
| `deploy_datatables` | Write | **Deploy** one or more data tables to the live CPQ site — admin-only, changes production configuration. Destructive/privileged. Preflight previews; apply with confirmation token. **API:** `POST /datatables/actions/deploy` |

### BML

| Tool | Type | Description |
|------|------|-------------|
| `get_all_bml_code` | Read | Download or retrieve **BML source code**. `delivery='zip'` (default) exports all Commerce BML and BMLT files via `GET /adminMeta` — equivalent to **cpq-toolkit pull** — and returns a zip `File` attachment. `delivery='json'` returns util library functions with inline `scriptText` (paginated `/bml/library/functions` fetch). Requires admin permissions. |

### Commerce metadata

Read-only metadata for Commerce process documents. All tools default `process_var_name` from profile (`COMMERCE_PROCESS_VAR_NAME`) and accept optional `doc_var_name` and `expand_all` (include translations via `expand=all*`).

| Tool | Type | Description |
|------|------|-------------|
| `get_commerce_attributes` | Read | List **attribute definitions** on a Commerce **main document** (default `doc_var_name='transaction'`). Names, types, constraints, display metadata. **API:** `GET /commerceProcesses/{process}/documents/{doc}/attributes` |
| `get_commerce_actions` | Read | List **action definitions** on a Commerce **main document** (default `transaction`). **API:** `GET /commerceProcesses/{process}/documents/{doc}/actionDefs` |
| `get_line_attributes` | Read | List **attribute definitions** on a Commerce **line document** (default `doc_var_name='transactionLine'`). **API:** `GET /commerceProcesses/{process}/documents/{doc}/attributes` |
| `get_line_actions` | Read | List **action definitions** on a Commerce **line document** (default `transactionLine`). **API:** `GET /commerceProcesses/{process}/documents/{doc}/actionDefs` |

### Meta

| Tool | Type | Description |
|------|------|-------------|
| `discover_tools` | Read | Search and filter this server's tool catalog by **domain**, **operation** (`read` / `write`), or free-text query. Use before calling tools to find read-only vs write capabilities, HTTP methods, and API paths. Does not call CPQ. |

<details>
<summary><strong>Configuration reference</strong></summary>

### Profile env (`.config/<customer>.env`)

| Variable | Description |
|----------|-------------|
| `CPQ_CUSTOMER_PROFILE` | Profile file name without `.env` (set in MCP config) |
| `CPQ_ENVIRONMENT` | Override default: `dev`, `test`, `prod` |
| `READ_ONLY` | Default `true` — blocks create/update/delete |
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
<summary><strong>IDE configuration files</strong></summary>

| IDE | Config file | Example in repo |
|-----|-------------|-----------------|
| Cursor | `.cursor/mcp.json` (local, gitignored) | [`.cursor/mcp.json.example`](../.cursor/mcp.json.example) (Windows) or [`.cursor/mcp.json.unix.example`](../.cursor/mcp.json.unix.example) (macOS/Linux) |
| VS Code | `.vscode/mcp.json` (local, gitignored) | [`.vscode/mcp.json.example`](../.vscode/mcp.json.example) or [`.vscode/mcp.json.unix.example`](../.vscode/mcp.json.unix.example) |
| Antigravity | `.agents/mcp_config.json` (local) | [`.agents/mcp_config.example.json`](../.agents/mcp_config.example.json) |

All examples use cross-platform launchers: [`scripts/mcp-server.cmd`](../scripts/mcp-server.cmd) (Windows) and [`scripts/mcp-server.sh`](../scripts/mcp-server.sh) (macOS/Linux). See [docs/QUICKSTART.md](docs/QUICKSTART.md#step-5--connect-your-ide--llm-client).

</details>

## Development

**IDE terminal** (repo root, venv activated):

```bash
pip install -e ".[dev]"
pytest
```

## Project structure

```
mcp/oracle_cpq_mcp/   # MCP server package
  core/               # Config, CPQClient, errors, preflight
  security/           # Policy, validation, confirmation, audit
  tools/              # MCP tool handlers
  registry/           # Tool catalog
.config/              # Customer profiles (*.env gitignored)
scripts/              # mcp-server.cmd / mcp-server.sh launchers
.cursor/              # MCP examples only (local mcp.json gitignored)
docs/                 # QUICKSTART, SETUP, security review
tests/                # Unit + security tests
```

## Security & git

- **Never commit** `.cursor/mcp.json` or `.config/*.env` — see [.gitignore](.gitignore)
- **Never put passwords** in `mcp.json` / MCP config
- Pre-commit checklist: [docs/QUICKSTART.md#before-you-commit-git-safety-checklist](docs/QUICKSTART.md#before-you-commit-git-safety-checklist)

## Remote MCP (future)

Local stdio works with desktop IDEs today. Cloud clients (ChatGPT, Gemini) need HTTPS + Streamable HTTP — see Phase 2 notes in [docs/SETUP.md](docs/SETUP.md).

## License

Internal / project-specific — see repository settings.
