# FAQ — Oracle CPQ MCP

Common questions for installing, connecting, securing, and using this MCP server with an AI agent (Antigravity, Cursor, VS Code, and similar).

**Start here for setup:** [QUICKSTART.md](QUICKSTART.md) · **Features & guardrails:** [FEATURES.md](FEATURES.md) · **Tool tables:** [TOOL_CATALOG.md](TOOL_CATALOG.md) · **Security:** [SECURITY.md](../SECURITY.md)

---

## Contents

1. [What is this project?](#1-what-is-this-project)
2. [Setup and install](#2-setup-and-install)
3. [Credentials and profiles](#3-credentials-and-profiles)
4. [Environments (dev / test / prod)](#4-environments-dev--test--prod)
5. [IDE and MCP connection](#5-ide-and-mcp-connection)
6. [Security and write operations](#6-security-and-write-operations)
7. [Tools and domains](#7-tools-and-domains)
8. [Users, groups, and data tables](#8-users-groups-and-data-tables)
9. [BML and commerce](#9-bml-and-commerce)
10. [Local `data/` cache](#10-local-data-cache)
11. [Refined prompts and Prompt Studio](#11-refined-prompts-and-prompt-studio)
12. [Errors and troubleshooting](#12-errors-and-troubleshooting)
13. [Development and contributing](#13-development-and-contributing)
14. [Remote / future](#14-remote--future)

---

## 1. What is this project?

### What does Oracle CPQ MCP do?

It is an **MCP (Model Context Protocol) server** that exposes Oracle CPQ REST APIs to AI agents as typed tools. Agents can list users, inspect groups, read data tables, export BML, explore commerce metadata/transactions, and more — without you pasting credentials into chat.

### What CPQ areas are covered?

Users, groups, data tables, BML, commerce metadata and transactions (including saved searches), metrics, collab queues, site admin (certificates/SSO), performance logs, parts, async tasks, configuration (`productFamilies` / layout cache), plus meta tools (discovery, saved prompts, local `data/` sync). See [FEATURES.md](FEATURES.md) and [TOOL_CATALOG.md](TOOL_CATALOG.md) (103 tools). Current package: **0.3.0** — [RELEASE_NOTES.md](RELEASE_NOTES.md).

### Which IDE should I use?

**[Google Antigravity](https://antigravity.google/)** is the recommended client (setup partially tested). Cursor and VS Code configs are included but still need more end-to-end testing on this project. See [QUICKSTART.md](QUICKSTART.md).

### Does this replace the CPQ UI or Admin?

No. It is an **agent integration layer** for exploration, audits, exports, and carefully gated writes. CPQ remains the system of record; CPQ RBAC still applies to the integration user.

### Is this official Oracle software?

No. This is a project-specific MCP server for Oracle CPQ REST APIs. Licensing is internal / repository-specific — see the repo settings and root [README](../README.md).

---

## 2. Setup and install

### What do I need before installing?

| Requirement | Details |
|-------------|---------|
| Python | **3.11+** |
| Oracle CPQ | REST API enabled; integration user with Basic Auth |
| Network | CPQ site reachable from your machine (VPN if required) |
| Git | Optional but recommended |

Full walkthrough: [QUICKSTART.md](QUICKSTART.md).

### How do I install the package?

From the **repository root** (IDE terminal recommended):

```bash
python -m venv .venv
# activate .venv for your shell, then:
pip install -e ".[dev]"
```

### How do I verify CPQ connectivity?

```bash
oracle-cpq-smoke --profile mycompany --env dev
```

Replace `mycompany` with your profile id (the name of `.config/mycompany.env` without `.env`).

### Do I need to run the server manually?

For IDE use, the MCP host launches it via `scripts/mcp-server.cmd` (Windows) or `scripts/mcp-server.sh` (macOS/Linux). You can also run `python -m oracle_cpq_mcp` for local checks; prefer the launchers in MCP config.

### Windows vs macOS / Linux — what differs?

| Topic | Windows | macOS / Linux |
|-------|---------|----------------|
| Copy profile template | `copy .config\.env.example .config\mycompany.env` | `cp .config/.env.example .config/mycompany.env` |
| MCP launcher | `scripts/mcp-server.cmd` | `scripts/mcp-server.sh` (+ `chmod +x`) |
| Path style in Antigravity | Absolute Windows paths (`C:\\Users\\...`) | Absolute POSIX paths |

---

## 3. Credentials and profiles

### Where do credentials live?

In **gitignored** profile files: `.config/<customer_id>.env` (for example `.config/mycompany.env`). Start from [`.config/.env.example`](../.config/.env.example).

**Never** put CPQ passwords in MCP JSON, chat, commits, or screenshots.

### What is `CPQ_CUSTOMER_PROFILE`?

It is the profile **file stem** (without `.env`). If the file is `.config/acme.env`, set `CPQ_CUSTOMER_PROFILE=acme` in the MCP host env.

### Can I have multiple customers?

Yes. Create one `.env` per customer (for example `acme.env`, `focalpoint.env`) and point MCP config at the profile you want — or register **separate MCP server entries** per customer. See QUICKSTART “Optional: multiple customers”.

### What is `COMPANY_LOGIN_NAME`?

Used for company-scoped APIs (especially **groups**). Default `_host` targets the host company. Change it when you need a different company login context.

### What REST API version should I set?

Set `REST_API_VERSION` in the profile to match your CPQ site (template mentions versions such as `v15`–`v18` depending on release). Wrong version often shows up as 404/unexpected payloads.

### What is the knowledge base?

- Shared rules: [`knowledge/CPQBaseKnowledge.md`](../knowledge/CPQBaseKnowledge.md) — loaded into MCP instructions for every customer.
- Customer notes: set `CUSTOMER_KNOWLEDGE_FILE=focalpoint.md` (basename only) to also load [`knowledge/focalpoint.md`](../knowledge/focalpoint.md).
- Missing customer files log a warning and are skipped (MCP still starts). Reload MCP after editing knowledge or aliases.

### What are property aliases?

Friendly names paired with real CPQ variable names on the profile:

```env
COMMERCE_PROCESS_VAR_NAME=oraclecpqo
COMMERCE_PROCESS_ALIAS=base commerce process
CUSTOM_DATA_TABLE_NAME=ModelMaster
CUSTOM_DATA_TABLE_ALIAS=model master
```

If you say “base commerce process” in a prompt, the agent should use `process_var_name=oraclecpqo`. Numbered `_1`, `_2` suffixes pair the same way.

Optional `COMMERCE_PROCESS_ENABLED[_N]` (default **true**): set `false` to keep the name/alias in the profile env but omit that slot from tool defaults and instruction aliases. Reload MCP after changing ENABLED or aliases.

---

## 4. Environments (dev / test / prod)

### How do environments work in a profile?

One profile file holds **all three** credential sets (`DEV_*`, `TEST_*`, `PROD_*`) plus URLs. `DEFAULT_ENVIRONMENT` picks which set is used when MCP starts (unless overridden by host env `CPQ_ENVIRONMENT`).

### Can the LLM connect with two environments at the same time?

**Yes.** A single chat / prompt can analyze **both** environments (for example **dev** and **test**) in one request.

**How it works in practice**

- Each MCP server process has **one active environment** (`CPQ_ENVIRONMENT` or `DEFAULT_ENVIRONMENT`). Tools do **not** accept an `environment` argument (blocked for security).
- To work with two live sites in the **same** agent session, register **two MCP server entries** that share the same profile and config dir but differ only by environment, for example:

```json
{
  "mcpServers": {
    "oracle-cpq-dev": {
      "command": "C:\\path\\to\\oracleCPQMCP\\scripts\\mcp-server.cmd",
      "args": [],
      "cwd": "C:\\path\\to\\oracleCPQMCP",
      "env": {
        "MCP_MODE": "stdio",
        "DISABLE_CONSOLE_OUTPUT": "true",
        "CPQ_CUSTOMER_PROFILE": "mycompany",
        "CPQ_ENVIRONMENT": "dev",
        "CPQ_CONFIG_DIR": "C:\\path\\to\\oracleCPQMCP\\.config",
        "CPQ_SCHEMA_INTEGRITY": "1"
      }
    },
    "oracle-cpq-test": {
      "command": "C:\\path\\to\\oracleCPQMCP\\scripts\\mcp-server.cmd",
      "args": [],
      "cwd": "C:\\path\\to\\oracleCPQMCP",
      "env": {
        "MCP_MODE": "stdio",
        "DISABLE_CONSOLE_OUTPUT": "true",
        "CPQ_CUSTOMER_PROFILE": "mycompany",
        "CPQ_ENVIRONMENT": "test",
        "CPQ_CONFIG_DIR": "C:\\path\\to\\oracleCPQMCP\\.config",
        "CPQ_SCHEMA_INTEGRITY": "1"
      }
    }
  }
}
```

- Alternatively (or in combination), sync or export into local cache under `data/{profile}/dev/` and `data/{profile}/test/`, then ask the agent to compare those snapshots without hammering live APIs.

**Example prompt**

> Compare active users between **dev** and **test**. Identify users present in both (match on email), users only in dev, and users only in test. Summarize group membership differences for the overlapping accounts.

That pattern is already reflected in sample prompts such as “Which users are common in both the dev and test environments?” in [COMMON_PROMPTS.md](COMMON_PROMPTS.md).

### Can I use prod?

Yes, but only with explicit host opt-in: set `CPQ_ALLOW_PROD=1` and use `CPQ_ENVIRONMENT=prod` (or `DEFAULT_ENVIRONMENT=prod`). Prefer read-only profiles for production. See [SECURITY.md](../SECURITY.md).

### Does local cache separate environments?

Yes. Snapshots are stored under `data/{profile}/{env}/…` (for example `data/mycompany/dev/users/`, `data/mycompany/test/bml/`). Dev and test caches do not overwrite each other.

---

## 5. IDE and MCP connection

### How do I connect Antigravity?

1. Install, create profile, run smoke test.
2. Copy `.agents/mcp_config.example.json` → `.agents/mcp_config.json`.
3. Use **absolute paths** (Antigravity does not expand `${workspaceFolder}` the same way).
4. Set `MCP_MODE=stdio`, `DISABLE_CONSOLE_OUTPUT=true`, `CPQ_CUSTOMER_PROFILE`, `CPQ_CONFIG_DIR`.
5. Reload MCP servers / restart the IDE.

Details: [QUICKSTART — Antigravity](QUICKSTART.md#google-antigravity-ide-recommended) and the root [README](../README.md#add-mcp-in-google-antigravity-recommended).

### How do I connect Cursor or VS Code?

Copy the matching example to a **local gitignored** config:

| IDE | Example → local file |
|-----|----------------------|
| Cursor | `.cursor/mcp.json.example` → `.cursor/mcp.json` |
| VS Code | `.vscode/mcp.json.example` → `.vscode/mcp.json` |

Restart the IDE after changes. Prefer Antigravity until Cursor/VS Code paths are fully validated on your machine.

### Why must Antigravity use absolute paths?

The client expects concrete `command`, `cwd`, and `CPQ_CONFIG_DIR` paths. Relative / `${workspaceFolder}` placeholders often fail to launch the server.

### Should passwords go in MCP JSON?

**No.** Only profile selection and host flags belong in MCP JSON. Credentials stay in `.config/<profile>.env`.

### MCP tools are missing or outdated after a pull — what do I do?

Reload / restart MCP servers (or the IDE). Tool catalogs and descriptions are loaded at process start. After upgrades, restart so new tools (saved prompts, local data, etc.) appear.

---

## 6. Security and write operations

### Are writes enabled by default?

**No.** Profiles default to `READ_ONLY=true`, which blocks create/update/deploy mutations.

### Where are DEBUG_MODE API logs?

When `DEBUG_MODE=true` (default if omitted; override with host `CPQ_DEBUG_MODE`), every CPQ HTTP call through `CPQClient` appends a timestamped block to **`logs/{profile}-{environment}.log`** (for example `logs/focalpoint-dev.log`). Each block includes a redacted `curl` (password as `***`) and a per-parameter list. Response bodies are not written. Override the directory with `CPQ_DEBUG_LOG_DIR`. The `logs/` folder is gitignored — treat files as sensitive (usernames and business query strings). Reload MCP after changing the flag. This is separate from `CPQ_VERBOSE` (console/stderr curl traces).

### How do safe writes work when enabled?

1. Call with `dry_run=true` (default) → preflight preview + `confirmation_token`.
2. **You** approve in chat.
3. Agent calls again with `dry_run=false` **and** the token.

See [FEATURES.md — Security guardrails](FEATURES.md#security-guardrails-and-human-in-the-loop) and [SECURITY.md](../SECURITY.md).

### What is `CPQ_CONFIRMATION_SECRET`?

A host-only secret used to mint HMAC confirmation tokens for writes. Required when `READ_ONLY=false`. Do not put it in the profile file that you share casually, and never commit it.

### Can the LLM bypass READ_ONLY by asking nicely?

No. Enforcement is **server-side**. Prompts cannot override profile `READ_ONLY`, confirmation tokens, prod allowlist, or blocked security arguments.

### What gets redacted from tool responses?

Credentials and other sensitive fields are stripped/sanitized so they are not echoed back into the model context. Errors are structured (`status`, `code`, `message`, `hint`, `details`) without stack traces.

### What should never be committed?

- `.config/*.env` (except `.env.example`)
- `.agents/mcp_config.json`, `.cursor/mcp.json`, `.vscode/mcp.json` (local)
- `.config/saved_prompts.json`, `.config/prompt_studio.json`
- `data/`, `exports/`
- Any real passwords or confirmation secrets

See [.gitignore](../.gitignore) and [PRE_COMMIT_REVIEW.md](PRE_COMMIT_REVIEW.md).

---

## 7. Tools and domains

### How many tools are there?

**103** MCP tools (regenerate the catalog after tool changes with `python scripts/generate_tool_catalog.py`). Formal tables: [TOOL_CATALOG.md](TOOL_CATALOG.md).

### How do I find the right tool?

Ask the agent to call `discover_tools` with a domain (`users`, `groups`, `datatables`, `bml`, `commerce`, `performance`, `parts`, `tasks`, `configuration`, `metrics`, `collab`, `admin`) and/or `operation` (`read` / `write`), or a free-text query.

### Which areas are untested against live CPQ?

Offline unit/contract tests cover the catalog. Some newer areas are still **untested live** (for example tasks, configuration `productFamilies`, some datatable create/export and BML extensions). The root [README](../README.md#testing-status-live-cpq) keeps an honest status table.

### What does a successful tool response look like?

Most tools return a single object:

```json
{ "status": "ok", "tool": "<name>", "data": { }, "pagination": { } }
```

Errors use `status: "error"` with `code`, `message`, `hint`. Export/BML tools may return `[envelope, File attachment]`.

### How does pagination work?

List tools return one page (`limit`, `offset`). When `hasMore` is true, call again with `pagination.nextOffset`. For a full user dump prefer `export_users_excel` (auto-paginates, row cap applies).

---

## 8. Users, groups, and data tables

### Why does `get_user` need a party number instead of a login?

CPQ’s user resource is keyed by **`partyNumber`**, not login name. Use `list_users` / export to discover party numbers, then `get_user`.

### Does `list_users` include inactive users?

By default it focuses on **active** users. Use `status_filter` (`active` / `inactive` / `all`) when you need others.

### How do I export all users to Excel?

Use `export_users_excel`. Large sites may take a while or time out in some MCP hosts; the server can also persist under `data/{profile}/{env}/users/`. If the MCP call times out, retry, raise host timeouts, or use a local client/smoke path as documented in troubleshooting.

### How do groups relate to companies?

`list_groups` / `list_group_users` are scoped by `COMPANY_LOGIN_NAME` (default `_host`).

### What is the default data table name?

`CUSTOM_DATA_TABLE_NAME` in the profile. Datatable tools can omit `table_name` when that default is set.

### Is deploying a data table dangerous?

Yes — `deploy_datatables` is privileged and can change live configuration. It stays behind `READ_ONLY`, dry-run, and confirmation. Prefer dry-run previews and non-prod first.

---

## 9. BML and commerce

### How do I get all BML code?

Call `get_all_bml_code` with `delivery='zip'` (default). That pulls Commerce BML/BMLT via `GET /adminMeta` (similar to a toolkit pull) and returns a zip attachment. `delivery='json'` returns util library functions with inline `scriptText` (paginated).

### Where is BML stored locally after a fetch?

Under `data/{profile}/{env}/bml/`:

- the `.zip` archive
- extracted tree at `data/{profile}/{env}/bml/site/` (zip-slip–safe extract; replaced on each successful zip persist)

### Why did my BML or Excel export time out in the IDE?

Large payloads can exceed MCP / host timeouts even when CPQ itself succeeds.

**Preferred BML site zip path (async local job):**

1. Call `start_bml_site_export` — returns immediately with `job_id`.
2. Poll `get_local_job(job_id=...)` until `status` is `succeeded` or `failed`.
3. Use `search_local_bml` or MCP resource `cpq://local` / `cpq://local/bml/{path}` against `data/{profile}/{env}/bml/site/`.

**Oracle CPQ task exports** (datatables / util library export): `export_*` (confirm) → poll `get_task` → `download_task_file`.

Also raise profile `HTTP_TIMEOUT` or host `CPQ_HTTP_TIMEOUT` (seconds, e.g. `300`) for long single HTTP calls. Prefer working from cached `data/` when a snapshot already exists. See [LIVE_SMOKE_MATRIX.md](LIVE_SMOKE_MATRIX.md).

### What is `COMMERCE_PROCESS_VAR_NAME`?

Profile default for commerce metadata/transaction tools (for example `oraclecpqo`). Tools accept overrides where the schema allows, but the profile default avoids repeating it every call. Pair with `COMMERCE_PROCESS_ALIAS` / numbered `_N` slots; use `COMMERCE_PROCESS_ENABLED[_N]=false` to leave a process in the env without exposing it to defaults or aliases (reload MCP after edits).

### Can I read transaction lines and layouts?

Yes — tools such as `list_transactions`, `get_transaction`, `list_transaction_lines`, `get_document_layout`, plus attribute/action metadata tools. Sample prompts: [COMMON_PROMPTS.md](COMMON_PROMPTS.md).

---

## 10. Local `data/` cache

### What is the local cache for?

Full collection snapshots so agents can answer from disk (faster, cheaper, offline-friendly) instead of always hitting live CPQ.

Path pattern: `data/{profile}/{env}/…` (gitignored). Override root with `CPQ_LOCAL_DATA_DIR`.

### What is `LOCAL_DATA_POLICY`?

| Value | Behavior |
|-------|----------|
| `ask` (default) | Agent should offer cache vs fresh when a snapshot exists |
| `prefer` | Use cache when present |
| `never` | Always fetch live |

Tools: `list_local_data`, `get_local_data_status`, `offer_use_local_data`, `load_local_data`, `set_local_data_policy`, plus `sync_*_local` domain syncs.

### When should I say “use cached data” vs “fresh data”?

- **Cached** — audits, cross-env diffs you already synced, browsing BML under `site/`, token-efficient follow-ups.
- **Fresh** — verifying a just-changed CPQ config, user access right now, or anything time-sensitive.

### Does export auto-save to `data/`?

Yes for flows such as `export_users_excel` and `get_all_bml_code` (zip + extract). Explicit `sync_*_local` tools also write full collections.

### Can I export a tabular chat answer to Excel or Word?

Yes. After a tabular answer, with `POST_RESPONSE_EXPORT=ask` (default), the agent calls `offer_export_response` (Excel / Word / both / skip / always_excel / never).

| Tool | Result |
|------|--------|
| `export_response_excel` | Multi-sheet `.xlsx` under `data/{profile}/{env}/exports/` + attachment |
| `export_response_word` | `.docx` in the same folder + local `file://` path (needs `python-docx`) |

Pass structured `sheets` (not scraped markdown). Install Word support with `pip install python-docx` or `pip install -e ".[docs]"`. Set policy with `set_post_response_export` or env `POST_RESPONSE_EXPORT` / `CPQ_POST_RESPONSE_EXPORT`.

---

## 11. Refined prompts and Prompt Studio

### What is the “Refined prompt” footer?

After CPQ-related work (live tools and/or local cache), agents append a reusable block:

`### Refined prompt (Better token usage)`

with title, tags, output format, cached-data flag, prose with `{{placeholders}}`, variables, and tools. Disable with profile `REFINED_PROMPT=false`.

### How do I save and reuse prompts?

- Offer/save: `offer_save_refined_prompt` / `save_refined_prompt`
- Auto-save: `AUTO_SAVE_REFINED_PROMPT=true` (or choose “save and always”)
- Pick later: `/OracleCPQ_SavedPrompts` or “use a saved prompt” → `start_prompt_picker`
- Library file: `.config/saved_prompts.json` (gitignored)

### What is Prompt Studio?

A **local** FastAPI UI to browse/search/favorite saved prompts and fill placeholders. It does **not** call Oracle CPQ.

```powershell
.\.venv\Scripts\python.exe -m pip install '.[prompt-studio]'
.\.venv\Scripts\python.exe -m apps.prompt_studio
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Details: [FEATURES.md — Prompt Studio](FEATURES.md#prompt-studio-enable-and-run) and [`apps/prompt_studio/README.md`](../apps/prompt_studio/README.md).

**Edit prompts:** use **Edit** on a card or in the run modal — change title, original/refined text, enable/disable. Select text and click **Make variable** to wrap it as `{{snake_case}}` (e.g. `OCL , FPL` → `{{token_a}}`).

**Latest prompts missing after Refresh?**

1. Hover the status line — Studio path must match MCP’s `.config/saved_prompts.json` (Studio pins `<repo>/.config` on startup when env vars are unset).
2. If **library last write** never changes, MCP did not call `save_refined_prompt` — enable `AUTO_SAVE_REFINED_PROMPT=true` on the active profile and reload MCP.
3. Similar tasks dedupe by content hash — one row updates instead of a new card.
4. Toggle **Show disabled** if the prompt was soft-disabled.
5. Use the **Reload** banner when the file changes on disk (auto-detected every 30s / on window focus).

---

## 12. Errors and troubleshooting

### Smoke test fails with auth / 401

Check URL (no trailing slash), username/password for the **selected** environment, and that the integration user can use REST. Confirm you passed `--env` matching the credentials you edited.

### Network / TLS / VPN errors

Confirm the CPQ host is reachable from your machine, VPN is connected if required, and the URL matches the site you use in a browser.

### MCP server does not start in the IDE

- Absolute paths (especially Antigravity)
- `CPQ_CONFIG_DIR` points at the real `.config` folder
- Profile file exists for `CPQ_CUSTOMER_PROFILE`
- Launcher script path is correct; on Unix ensure `mcp-server.sh` is executable
- Required Antigravity flags: `MCP_MODE=stdio`, `DISABLE_CONSOLE_OUTPUT=true`

### Schema integrity / startup hash errors

Host sets `CPQ_SCHEMA_INTEGRITY=1` to verify the tool manifest. After intentional tool catalog changes, regenerate manifests/catalogs per project scripts and restart. Do not disable integrity casually in shared environments.

### Tool returns `status: error` — how do I read it?

Use `code`, `message`, and `hint` first. `details` may include safe context. Do not ask the model to “print the password” or raw exception chains — they should not be present.

### Prod calls are blocked

Set `CPQ_ALLOW_PROD=1` only when intentional, and ensure the active environment is `prod`. Keep `READ_ONLY=true` unless you fully understand write guardrails.

### Rate limit or session tool cap

Host may set `CPQ_MAX_TOOL_CALLS` (default often 20). Large multi-page audits may need higher caps or cache-first workflows.

---

## 13. Development and contributing

### How do I run tests?

```bash
pip install -e ".[dev]"
pytest
```

Security-focused notes: [SECURITY_TESTING.md](../SECURITY_TESTING.md).

### What standards apply to new tools?

[STANDARDS.md](STANDARDS.md) — strict Pydantic models (`extra=forbid`), route HTTP only through `CPQClient`, sanitize errors, dry-run + confirmation for writes. After tool changes, use [prompts/compliance_check.md](../prompts/compliance_check.md).

### How do I refresh docs after tool changes?

```bash
python scripts/generate_tool_catalog.py
python scripts/update_release_notes.py
```

Pre-commit checklist: [PRE_COMMIT_REVIEW.md](PRE_COMMIT_REVIEW.md).

### How do I bump the package version for a GitHub release?

Follow [README — Update the package version](../README.md#update-the-package-version): bump `pyproject.toml`, move Unreleased notes under `## [x.y.z] - YYYY-MM-DD` in [RELEASE_NOTES.md](RELEASE_NOTES.md), regenerate catalog/manifest if tools changed, commit, optionally `git tag vX.Y.Z`.

### Where is the package code?

```
mcp/oracle_cpq_mcp/   # server package
  core/                # config, CPQClient, errors, local data
  security/            # policy, validation, confirmation, audit
  tools/               # MCP tool handlers
  registry/            # tool catalog
apps/prompt_studio/    # local Prompt Studio UI
```

---

## 14. Remote / future

### Can I use this from ChatGPT / cloud agents today?

Local **stdio** MCP works with desktop IDEs. Cloud clients that need HTTPS / Streamable HTTP are a later phase — see notes in [SETUP.md](SETUP.md).

### Is there a public support channel?

Treat this repository’s maintainers / internal process as the support path unless the README or org settings say otherwise.

---

## Related documents

| Document | Use when |
|----------|----------|
| [QUICKSTART.md](QUICKSTART.md) | First-time install and IDE connect |
| [FEATURES.md](FEATURES.md) | Product capabilities + HITL security |
| [TOOL_CATALOG.md](TOOL_CATALOG.md) | Exact tool parameters |
| [COMMON_PROMPTS.md](COMMON_PROMPTS.md) | Sample agent prompts |
| [SECURITY.md](../SECURITY.md) | Guardrail architecture |
| [THREAT_MODEL.md](../THREAT_MODEL.md) | Threat analysis |
| [RELEASE_NOTES.md](RELEASE_NOTES.md) | Changelog |
| [README.md](../README.md) | Project overview |
