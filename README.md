# Oracle CPQ MCP Server

MCP server for **Oracle CPQ** — **100 MCP tools** for Users, Groups, Data Tables, BML, Commerce, Metrics, Admin, Parts, Performance Logs, and more.

**Current package version:** **`0.2.0`** — see [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md). Contributor version bumps: [Update the package version](#update-the-package-version).

**Recommended IDE:** [Google Antigravity](https://antigravity.google/) (MCP setup partially tested). Cursor and VS Code configs are included but still need testing.

## Get started

**New here?** Follow the full walkthrough:

**[docs/QUICKSTART.md](docs/QUICKSTART.md)** — download repo, create credential profile, smoke test, and connect **Antigravity** (recommended) step by step.

**Already on an older checkout?** Jump to [Update from an older version](#update-from-an-older-version) — pull latest, reinstall, reload MCP (keep your `.env` and local MCP JSON).

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

## Update from an older version

Use this if you already cloned the repo and connected MCP earlier. You do **not** need to recreate credentials or re-copy MCP config from scratch.

1. **Pull the latest code** (repo root, your branch / `main` as appropriate):

```bash
git fetch origin
git pull
```

2. **Reinstall the package** into the same venv you use for MCP (so new tools and dependencies load):

```bash
# activate your venv first if needed
pip install -e ".[dev]"
```

Optional extras you already use:

```bash
pip install -e ".[prompt-studio]"   # Prompt Studio UI
pip install -e ".[docs]"            # Word export (python-docx)
```

3. **Refresh profile knobs (keep passwords).** Compare your `.config/<profile>.env` to [`.config/.env.example`](.config/.env.example) and add any new keys you care about (examples that appeared in recent releases):

| Key | Typical default | Purpose |
|-----|-----------------|--------|
| `DEBUG_MODE` | `true` | Redacted API traces → `logs/{profile}-{env}.log` |
| `REFINED_PROMPT` | `true` | End-of-task refined-prompt footer |
| `AUTO_SAVE_REFINED_PROMPT` | `false` | Auto-save refined prompts |
| `LOCAL_DATA_POLICY` | `ask` | Cache vs live CPQ before big lists |
| `POST_RESPONSE_EXPORT` | `ask` | Offer Excel/Word after tabular answers |
| `REST_API_VERSION` | site-specific | Prefer `v19` for metrics / collab / admin / saved searches if v18 404s |

Do **not** overwrite your profile with `.env.example` — that would wipe URLs and passwords.

4. **Keep local MCP JSON as-is** (gitignored): `.agents/mcp_config.json`, `.cursor/mcp.json`, or `.vscode/mcp.json`. Paths and `CPQ_CUSTOMER_PROFILE` / `CPQ_CONFIG_DIR` usually stay the same. Only re-check the example files if a release note says launcher paths or required env vars changed.

5. **Reload the Oracle CPQ MCP server** in your IDE (or restart the IDE). New tools (e.g. saved searches, admin/certificates, export helpers) will not appear until the process restarts.

6. **Quick check** in Agent chat:

- *“Discover tools for domain admin”* or *“list saved searches”*
- Optional: `oracle-cpq-smoke --profile <your-profile> --env dev`

7. **Read the delta:** [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md) (current package **0.2.0**). Full first-time path remains [QUICKSTART](docs/QUICKSTART.md).

**Leave alone (local / secrets):** `.config/*.env`, `data/`, `logs/`, `saved_prompts.json`, Prompt Studio sidecar, and your local MCP config — they are gitignored on purpose.

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
| [README — Update from an older version](#update-from-an-older-version) | **Existing users** — `git pull`, reinstall, merge new `.env` keys, reload MCP |
| [docs/FAQ.md](docs/FAQ.md) | **FAQ** — install, dual env (dev+test), security, local cache, BML, Prompt Studio, troubleshooting |
| [docs/FEATURES.md](docs/FEATURES.md) | **Detailed features** + **security guardrails / human-in-the-loop** + Prompt Studio enable/run |
| [docs/TOOL_CATALOG.md](docs/TOOL_CATALOG.md) | Formal per-tool Parameters / Filters tables (100 tools; regenerate with `python scripts/generate_tool_catalog.py`) |
| [docs/PRE_COMMIT_REVIEW.md](docs/PRE_COMMIT_REVIEW.md) | Pre-commit secrets / catalog / test checklist |
| [docs/STANDARDS.md](docs/STANDARDS.md) | Tool authoring standards — checklist, lint, contract/eval gates |
| [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md) | Changelog — current **0.2.0**; refresh Unreleased commits with `python scripts/update_release_notes.py` |
| [docs/SETUP.md](docs/SETUP.md) | Short setup summary |
| [docs/others/AUDIT_REPORT.md](docs/others/AUDIT_REPORT.md) | Historical technical audit (archived) |
| [SECURITY.md](SECURITY.md) | Guardrails, confirmation tokens, audit |
| [SECURITY_TESTING.md](SECURITY_TESTING.md) | Security test suite and CI |
| [THREAT_MODEL.md](THREAT_MODEL.md) | STRIDE / MCP threat analysis |
| [.config/.env.example](.config/.env.example) | CPQ profile field reference |

## Features

Full product write-up (including **security / human-in-the-loop**): **[`docs/FEATURES.md`](docs/FEATURES.md)**. What’s new in **0.2.0**: [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md).

- **100 MCP tools** — domain summary below; formal tables in [`docs/TOOL_CATALOG.md`](docs/TOOL_CATALOG.md)
- **Read-only by default** — `READ_ONLY=true`; writes use dry-run + `confirmation_token`
- **DEBUG_MODE logging** — redacted CPQ request traces in `logs/{profile}-{environment}.log`
- **Refined prompts** — reusable footer + library / picker; optional Prompt Studio on port **8765** (Download all)
- **Local `data/` snapshots** — `LOCAL_DATA_POLICY=ask|prefer|never`; sync tools under `data/{profile}/{env}/`
- **Post-response export** — Excel/Word under `data/.../exports/` after tabular answers
- **Server-side security** — validation, rate limits, replay protection, PEM/credential redaction

### Testing status (live CPQ)

Offline unit/contract tests cover the full catalog. Against a live CPQ site, these areas are still **untested** (no complete smoke yet):

| Area | Tools | Live status |
|------|--------|-------------|
| Data tables (new) | `create_datatable`, `export_datatables` | **Untested** |
| BML (extensions) | `search_bml_scripts`, common/library helpers, `export_bml_library_functions` | **Untested** |
| Tasks | `get_task`, `download_task_file` | **Untested** |
| Configuration | `list_product_families` … layoutcache tools | **Untested** |
| Admin / saved searches | certificates, SSO, `list_saved_searches` | May **404** on REST **v18** (docs target **v19**) |

## MCP tools (summary)

**100 MCP tools.** Full Parameters / Filters tables: [`docs/TOOL_CATALOG.md`](docs/TOOL_CATALOG.md). In the agent, filter with `discover_tools(domain="…")` (e.g. `users`, `commerce`, `admin`, `metrics`, `collab`).

Write tools default to **dry-run** (`dry_run=true`); apply with `confirmation_token`. Blocked when `READ_ONLY=true`. Commerce tools default `process_var_name` from `COMMERCE_PROCESS_VAR_NAME`.

| Domain | Example tools | Notes |
|--------|---------------|--------|
| **users** | `list_users`, `get_user`, `export_users_excel`, `update_user` | Active-by-default lists; Excel export |
| **groups** | `list_groups`, `get_group`, `list_group_users`, `create_group` | Company from `COMPANY_LOGIN_NAME` |
| **datatables** | `list_datatables`, `get_datatable_rows`, `deploy_datatables`, `create_datatable`, `export_datatables` | Create/export **untested** live |
| **bml** | `get_all_bml_code`, `get_bml_function`, `search_bml_scripts`, … | Zip via `/adminMeta`; some APIs **untested** live |
| **commerce** | `get_commerce_attributes`, `list_transactions`, `list_saved_searches`, `get_commerce_ui_settings`, … | Metadata, transactions, UI settings, saved searches |
| **metrics** | `list_metrics` | Prefer REST **v19** if v18 404s |
| **collab** | `get_collab_operation_queue`, `clear_collab_operation_queue` | Clear is destructive (dry-run + confirm) |
| **admin** | `list_certificates`, `get_certificate`, `get_sso_configuration` | PEM redacted; prefer **v19** |
| **performance** | `list_performance_logs`, `get_performance_log`, `export_performance_logs` | Activity timing logs |
| **parts** | `list_parts`, `get_part`, `search_parts` | |
| **tasks** | `get_task`, `download_task_file` | Async export follow-up; **untested** live |
| **configuration** | `list_product_families`, layout/attribute/array-set tools | **Untested** live |
| **meta** | `discover_tools`, saved-prompt tools, `list_local_data`, `sync_*_local`, export-response tools | Local library / cache / chat exports |

Also: MCP resource `cpq://saved-prompts`, prompt `run_saved_prompt`.

<details>
<summary><strong>Configuration reference</strong></summary>

### Profile env (`.config/<customer>.env`)

| Variable | Description |
|----------|-------------|
| `CPQ_CUSTOMER_PROFILE` | Profile file name without `.env` (set in MCP config) |
| `CPQ_ENVIRONMENT` | Override default: `dev`, `test`, `prod` |
| `READ_ONLY` | Default `true` — blocks create/update/delete |
| `DEBUG_MODE` | Default `true` — append redacted CPQ API traces to `logs/{profile}-{environment}.log` |
| `REFINED_PROMPT` | Default `true` — append refined-prompt footer after CPQ-related tasks (live and/or local cache) |
| `AUTO_SAVE_REFINED_PROMPT` | Default `false` — when true, auto-save refined prompts; when false, agent asks |
| `LOCAL_DATA_POLICY` | Default `ask` — `ask` / `prefer` / `never` for using `data/` snapshots before live CPQ |
| `POST_RESPONSE_EXPORT` | Default `ask` — `ask` / `never` / `always_excel` for post-response Excel/Word export offers |
| `CPQ_LOCAL_DATA_DIR` | Optional override for local snapshot root (default `<repo>/data`) |
| `CPQ_SAVED_PROMPTS_PATH` | Optional override for saved refined-prompt library JSON |
| `DEV_URL`, `DEV_USERNAME`, `DEV_PASSWORD` | Dev CPQ credentials |
| `REST_API_VERSION` | e.g. `v18` |
| `CUSTOM_DATA_TABLE_NAME` | Default table for smoke test / datatable tools |
| `CUSTOM_DATA_TABLE_ALIAS` | Friendly name for the default table (pair with `_1` / `_2` as needed) |
| `COMMERCE_PROCESS_VAR_NAME` | Commerce process variable for metadata tools (e.g. `oraclecpqo`) |
| `COMMERCE_PROCESS_ALIAS` | Friendly name (e.g. `base commerce process`) mapped to the process var |
| `CUSTOMER_KNOWLEDGE_FILE` | Basename under `knowledge/` (e.g. `focalpoint.md`); shared `CPQBaseKnowledge.md` always loads |

See [.config/.env.example](.config/.env.example) for all fields.

### Host env (MCP JSON — not in profile file)

| Variable | Default | Purpose |
|----------|---------|---------|
| `CPQ_CONFIRMATION_SECRET` | — | Required when writes enabled |
| `CPQ_SCHEMA_INTEGRITY` | `1` | Verify tool manifest at startup |
| `CPQ_ALLOW_PROD` | unset | Must be `1` for prod |
| `CPQ_MAX_TOOL_CALLS` | `20` | Session tool call cap |
| `CPQ_VERBOSE` | off | Redacted request/curl logging to the process logger (stderr) |
| `CPQ_DEBUG_MODE` | profile / true | Override profile `DEBUG_MODE` for file logging |
| `CPQ_DEBUG_LOG_DIR` | `<repo>/logs` | Directory for `DEBUG_MODE` log files |

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

## Update the package version

Use this when cutting a numbered release for GitHub (e.g. `0.2.0` → `0.3.0`). Full narrative lives in [`docs/RELEASE_NOTES.md`](docs/RELEASE_NOTES.md).

1. **Bump** `version` in [`pyproject.toml`](pyproject.toml).
2. **Move** the current `## Unreleased` Highlights / Added / Changed blocks under a new heading:  
   `## [x.y.z] - YYYY-MM-DD`  
   Leave a fresh empty `## Unreleased` (keep the `<!-- git-commits -->` markers for the auto script).
3. **If tools changed**, regenerate integrity + catalog:
   ```bash
   # from repo root, with PYTHONPATH=mcp (or editable install)
   python -c "from oracle_cpq_mcp.security.schema_integrity import write_manifest_file; write_manifest_file()"
   python scripts/generate_tool_catalog.py
   python scripts/lint_tool_schemas.py
   pytest
   ```
4. **Commit** the version + docs (and code). Optionally **tag**: `git tag v0.y.z` then `git push origin v0.y.z`.
5. Refresh the Unreleased git list anytime with `python scripts/update_release_notes.py` (pre-commit may do this for you — re-stage if it rewrites the file).

Do **not** put CPQ passwords, profile `.env` files, or `data/` / `logs/` in the release commit.

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
