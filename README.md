# Oracle CPQ MCP Server

MCP server for **Oracle CPQ** — exposes **Users**, **Groups**, and **Data Tables** REST APIs to AI agents (Cursor, VS Code Copilot, Google Antigravity, and other MCP clients).

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

- **14 MCP tools** — users, groups, data tables, tool discovery
- **Read-only by default** — profile `READ_ONLY=true` blocks all mutations
- **Safe writes** — preflight + HMAC `confirmation_token` (when writes enabled)
- **Structured errors** — `{status, code, message, hint, details}` (no stack traces)
- **Server-side security** — validation, rate limits, replay protection, output redaction

## MCP tools (summary)

| Domain | Read | Write |
|--------|------|-------|
| Users | `list_users`, `get_user`, `get_user_groups`, `export_users_excel` | `update_user` |
| Groups | `list_groups`, `get_group`, `list_group_users` | `create_group` |
| Data tables | `list_datatables`, `get_datatable`, `get_datatable_rows` | `deploy_datatables` |
| Meta | `discover_tools` | — |

Use `discover_tools(domain="users", operation="read")` in Agent mode to explore the catalog.

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
| `CUSTOM_DATA_TABLE_NAME` | Default table for smoke test / tools |

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
| Cursor | `.cursor/mcp.json` | Committed (no secrets) |
| VS Code | `.vscode/mcp.json` | Copy from [`.vscode/mcp.json.example`](.vscode/mcp.json.example) |
| Antigravity | `.agents/mcp_config.json` | Copy from [`.agents/mcp_config.example.json`](.agents/mcp_config.example.json) |

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
.cursor/              # Cursor MCP config
docs/                 # QUICKSTART, SETUP, security review
tests/                # Unit + security tests
```

## Security & git

- **Never commit** `.config/*.env` (credentials) — see [.gitignore](.gitignore)
- **Never put passwords** in `mcp.json` / MCP config
- Pre-commit checklist: [docs/QUICKSTART.md#before-you-commit-git-safety-checklist](docs/QUICKSTART.md#before-you-commit-git-safety-checklist)

## Remote MCP (future)

Local stdio works with desktop IDEs today. Cloud clients (ChatGPT, Gemini) need HTTPS + Streamable HTTP — see Phase 2 notes in [docs/SETUP.md](docs/SETUP.md).

## License

Internal / project-specific — see repository settings.
