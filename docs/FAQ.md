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

Users, groups, data tables, BML, commerce metadata and transactions (including saved searches), metrics, collab queues, site admin (certificates/SSO), performance logs, parts, async tasks, configuration (`productFamilies` / layout cache), plus meta tools (discovery, saved prompts, local `data/` sync, `ensure_prompt_studio`). See [FEATURES.md](FEATURES.md) and [TOOL_CATALOG.md](TOOL_CATALOG.md) (106 tools). Current package: **0.3.0** — [RELEASE_NOTES.md](RELEASE_NOTES.md).

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

**Preferred:** one gitignored file `.config/<customer_id>.yaml` (secrets, flags, commerce processes, data tables, metrics, and product families). Start from [`.config/.profile.yaml.example`](../.config/.profile.yaml.example) or migrate:

```bash
python scripts/migrate_profile_yaml.py mycompany
```

**Legacy (still supported):** `.config/<customer_id>.env` for secrets/flags, optionally plus `.config/<customer_id>.catalog.yaml` for catalog sections. If both `.yaml` and `.env` exist for the same id, **the unified `.yaml` wins**.

### How do I migrate from a legacy `.env` to `.yaml`?

Use the migrate script so secrets, flags, commerce processes, data tables, metrics, and product-family trees land in one file. The script **does not delete** your `.env`.

#### Prerequisites

1. Repo root open in the IDE, venv activated (same as QUICKSTART).
2. An existing profile file: `.config/<customer_id>.env` (for example `.config/mycompany.env` → id `mycompany`).
3. PyYAML installed (comes with the package deps: `pip install -e ".[dev]"` or `pip install "PyYAML>=6.0.0"`).

#### Step-by-step

1. **Confirm the profile id**  
   It is the filename stem only: `.config/focalpoint.env` → `focalpoint`. MCP still uses `CPQ_CUSTOMER_PROFILE=focalpoint` after migration (no extension).

2. **Preview the YAML (no write)**  
   From the project root:

   ```bash
   python scripts/migrate_profile_yaml.py focalpoint --dry-run
   ```

   Check the printed summary (`envs`, `commerce`, `tables`, `metrics`, `families`) and skim the YAML. Passwords appear in the preview — do not paste that output into chat, tickets, or commits.

3. **Write `.config/<id>.yaml`**  

   ```bash
   python scripts/migrate_profile_yaml.py focalpoint
   ```

   Creates `.config/focalpoint.yaml`. If that file already exists:

   ```bash
   python scripts/migrate_profile_yaml.py focalpoint --force
   ```

4. **What gets mapped**

   | Legacy `.env` | Unified `.yaml` |
   | ------------- | --------------- |
   | `CUSTOMER_NAME`, flags (`READ_ONLY`, `LOCAL_DATA_POLICY`, …) | Top-level keys (`customer_name`, `read_only`, …) |
   | `DEV_URL` / `DEV_USERNAME` / `DEV_PASSWORD` (+ `_1`, …) | `environments.dev.url` + `credentials` (same for `test` / `prod`) |
   | `DEFAULT_ENVIRONMENT`, `REST_API_VERSION`, `COMPANY_LOGIN_NAME` | `default_environment`, `rest_api_version`, `company_login_name` |
   | `COMMERCE_PROCESS_VAR_NAME[_N]` + `ALIAS` + `ENABLED` | `commerce_processes:` list |
   | `CUSTOM_DATA_TABLE_NAME[_N]` + `ALIAS` | `data_tables:` list |
   | `METRICS_*` | `metrics:` map |
   | `PRODUCT_FAMILY_*` / `PRODUCT_LINE_*` / `MODEL_*` | Nested `product_families:` |

5. **Review the new file**  
   Open `.config/<id>.yaml` and confirm URLs, users, `default_environment`, and catalog lists. Optionally set `environments.<name>.enabled: false` or `data_tables[].enabled: false` for entries you want to keep but not use.

6. **Verify connectivity**  

   ```bash
   oracle-cpq-smoke --profile focalpoint --env dev
   ```

   Expect `Profile loaded` and PASS rows. Then **reload / restart** the Oracle CPQ MCP server in Cursor (same `CPQ_CUSTOMER_PROFILE`).

7. **Precedence while both files exist**  
   If `.config/focalpoint.yaml` and `.config/focalpoint.env` both exist, **only the YAML is loaded**. The `.env` is ignored until you remove the YAML (or rename it).

8. **Clean up after a successful smoke + MCP reload**  
   - Rename or delete `.config/<id>.env` (keep a backup outside the repo if you want).  
   - Delete `.config/<id>.catalog.yaml` if you ever created a catalog-only sidecar (`migrate_profile_catalog.py` is deprecated).  
   - Confirm `.gitignore` still ignores `.config/*.yaml` and `.config/*.env` (except examples).  
   - Never commit real profile YAML/ENV files.

#### Troubleshooting

| Symptom | Fix |
| ------- | --- |
| `Legacy profile .env not found` | Wrong id or file not under `.config/`; check `CPQ_CONFIG_DIR` if set |
| `Profile YAML already exists` | Use `--force`, or rename the existing `.yaml` first |
| Smoke still reads old values | A `.yaml` already existed and wasn’t overwritten — use `--force` or delete it |
| `environment '…' is disabled` | Set `environments.<name>.enabled: true` or pick another env |
| Import / PyYAML errors | `pip install -e .` from repo root (includes `PyYAML`) |

#### Related

- Template for new profiles: [`.config/.profile.yaml.example`](../.config/.profile.yaml.example)
- Script: [`scripts/migrate_profile_yaml.py`](../scripts/migrate_profile_yaml.py)
- Deprecated catalog-only migrate: `scripts/migrate_profile_catalog.py` (prefer the full YAML migrate above)

**Never** put CPQ passwords in MCP JSON, chat, commits, or screenshots.

### What is `CPQ_CUSTOMER_PROFILE`?

It is the profile **file stem** (without `.yaml` / `.env`). If the file is `.config/acme.yaml` (or legacy `acme.env`), set `CPQ_CUSTOMER_PROFILE=acme` in the MCP host env.

### Can I have multiple customers?

Yes. Create one profile file per customer (for example `acme.yaml`, `focalpoint.yaml`, or legacy `acme.env`) and point MCP config at the profile you want — or register **separate MCP server entries** per customer. See QUICKSTART “Optional: multiple customers”.

### What is `COMPANY_LOGIN_NAME`?

Used for company-scoped APIs (especially **groups**). Default `_host` targets the host company. Change it when you need a different company login context.

### What REST API version should I set?

Set `REST_API_VERSION` in the profile to match your CPQ site (template mentions versions such as `v15`–`v18` depending on release). Wrong version often shows up as 404/unexpected payloads.

### What is the knowledge base?

- Shared rules: [`knowledge/CPQBaseKnowledge.md`](../knowledge/CPQBaseKnowledge.md) — loaded into MCP instructions for every customer.
- Customer notes: set `CUSTOMER_KNOWLEDGE_FILE=focalpoint.md` (basename only) to also load [`knowledge/focalpoint.md`](../knowledge/focalpoint.md).
- Missing customer files log a warning and are skipped (MCP still starts). Reload MCP after editing knowledge or aliases.

### What are property aliases?

Friendly names paired with real CPQ variable names on the profile (unified `.yaml` or legacy `.env` / `.catalog.yaml`):

```yaml
commerce_processes:
  - var_name: oraclecpqo
    alias: base commerce process
    enabled: true
data_tables:
  - name: ModelMaster
    alias: model master
    enabled: true
  - name: DiscountMatrix
    alias: discount matrix
    enabled: true
product_families:
  - var_name: laptop
    alias: Laptop family
    enabled: true
```

You can list **multiple** `data_tables` entries. The **first enabled** table is the default for tools that take a single `table_name`; aliases, smoke checks, and `sync_datatables_local` use the full enabled list.

Legacy flat `.env` form still works when no unified `.yaml` is present:

```env
COMMERCE_PROCESS_VAR_NAME=oraclecpqo
COMMERCE_PROCESS_ALIAS=base commerce process
CUSTOM_DATA_TABLE_NAME=ModelMaster
CUSTOM_DATA_TABLE_ALIAS=model master
CUSTOM_DATA_TABLE_NAME_1=DiscountMatrix
CUSTOM_DATA_TABLE_ALIAS_1=discount matrix
```

If you say “base commerce process” in a prompt, the agent should use `process_var_name=oraclecpqo`. Product family / line / model aliases are injected into MCP instructions the same way.

Optional `enabled: false` on commerce processes, data tables, or YAML `environments.<name>` (or legacy `COMMERCE_PROCESS_ENABLED[_N]=false`): omit that entry from tool defaults / aliases, or block selecting that environment. Reload MCP after changing ENABLED or aliases.

---

## 4. Environments (dev / test / prod)

### How do environments work in a profile?

**Unified YAML** (`.config/<id>.yaml`): one file holds `environments.dev` / `test` / `prod` (url + credentials). `default_environment` picks which set is used when MCP starts (unless overridden by host env `CPQ_ENVIRONMENT`).

Set `environments.<name>.enabled: false` to keep credentials in the file but **block** selecting that environment (load fails with a clear error). Default is `enabled: true` when omitted.

**Legacy `.env`**: one file holds all three credential sets (`DEV_*`, `TEST_*`, `PROD_*`) plus URLs. Omit an environment’s URL/creds to leave it unused (there is no separate disable key).

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

### Do Antigravity (or VS Code) users need `.cursor/rules`?

**No.** `.cursor/rules/` is Cursor-only. Antigravity, VS Code Copilot, and other MCP clients get agent policy from **MCP server instructions** when Oracle CPQ MCP is connected. Use root [`AGENTS.md`](../AGENTS.md) as the portable entry point. Reload/restart MCP after instruction changes so refined prompts, turn metrics, and document templates apply.

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

- `.config/*.yaml` / `.config/*.env` (except `.profile.yaml.example`, `.env.example`, `.catalog.yaml.example`)
- `.agents/mcp_config.json`, `.cursor/mcp.json`, `.vscode/mcp.json` (local)
- `.prompts/saved_prompts.json`, `.config/prompt_studio.json`
- `data/`, `exports/`
- Any real passwords or confirmation secrets

See [.gitignore](../.gitignore) and [PRE_COMMIT_REVIEW.md](PRE_COMMIT_REVIEW.md).

---

## 7. Tools and domains

### How many tools are there?

**106** MCP tools (regenerate the catalog after tool changes with `python scripts/generate_tool_catalog.py`). Formal tables: [TOOL_CATALOG.md](TOOL_CATALOG.md).

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
| `export_response_word` | `.docx` in the same folder + local `file://` path (needs `python-docx`); `diagrams` with Mermaid/`image_path` PNG (expected for analytical exports) |

Pass structured `sheets` (not scraped markdown). Install Word support with `pip install python-docx` or `pip install -e ".[docs]"`. Set policy with `set_post_response_export` or env `POST_RESPONSE_EXPORT` / `CPQ_POST_RESPONSE_EXPORT`.

### Should Word exports include Mermaid?

**Yes for analytical or structured answers** (audits, pass/fail summaries, flows, comparisons, relationship reviews). When calling `export_response_word` (or Word as part of `both`), agents must pass **1–3** items in `diagrams: [{title, mermaid?, image_path?, caption?}]` (max 8) **without waiting for the user to ask**. Prefer `flowchart` / `graph`. Skip diagrams for trivial short lists or pure errors. Embedded diagram images and captions are **center-aligned**.

Structure Word `notes` with newlines, `##` / `###` headings, and `-` / `*` bullets — not one dense paragraph (lightweight markers only; not full Markdown).

Mermaid is rasterized **locally** with `mmdc` (`npm i -g @mermaid-js/mermaid-cli`). Do not use public Kroki/mermaid.ink. If `mmdc` is missing, the export still succeeds: Mermaid source is kept as prose and listed in `diagrams_skipped`. Alternatively pass a pre-rendered PNG under `tmp/{profile}/{env}/` via `image_path`.

### How do I install Mermaid for Word diagrams?

1. Install [Node.js LTS](https://nodejs.org/) (includes `npm`).
2. From any shell: `npm i -g @mermaid-js/mermaid-cli`
3. Verify: `mmdc --version` (reopen the IDE terminal if `mmdc` is not found — PATH must include the npm global bin).

Full steps: [QUICKSTART — Step 2.1](QUICKSTART.md#21-optional--mermaid-cli-for-word-diagrams).

### Why don’t Word exports match my branding?

Exports clone a valid Word package. Resolution order:

1. `CPQ_WORD_TEMPLATE` (full path to a `.docx`)
2. `.config/template/Word Template.docx` (exact filename; folder is agent-read-only)
3. `data/templates/Word Template.docx` (writable working copy; override dir with `CPQ_TEMPLATE_WORK_DIR`)

Excel/PowerPoint use the same pattern (`CPQ_EXCEL_TEMPLATE` / `CPQ_PPTX_TEMPLATE`, then config, then working dir). If none are valid Office ZIPs, the exporter falls back to a blank document and reports `template.applied=false` (with `template.source` when a candidate was used).

To use a renamed branding file without editing `.config/template/`, copy it once:

```text
data/templates/Word Template.docx
```

### Why are Word tables hard to read?

Wide `sheets` no longer get equal-width portrait columns. Auto layout:

| Columns | Behavior |
|---------|----------|
| ≤ 4 (and widths fit) | Portrait table, weighted column widths, 8 pt body font, repeating header |
| ≤ 7 | Landscape section with floored minimum column widths when needed |
| > 7 (or still too narrow) | Per-row label/value blocks (2-column tables) so long BMQL/paths stay readable |

Diagram images scale to the active section content width.

---

## 11. Refined prompts and Prompt Studio

### What is the “Refined prompt” footer?

After **real site/cache data work** (live CPQ MCP tools that read/write CPQ or load/sync `data/{profile}/{env}/`, or answers built from that cache), agents append a reusable block:

`### Refined prompt (Better token usage)`

with title, tags, output format, cached-data flag, prose with `{{placeholders}}`, variables, and tools.

**Not every chat in this repo.** Coding, reviews, plans, docs, and “how does the server work” turns should **skip** the footer (and skip `offer_save_refined_prompt` / `save_refined_prompt`). Disable globally with profile `REFINED_PROMPT=false`.

### How do I save and reuse prompts?

- Offer/save: `offer_save_refined_prompt` / `save_refined_prompt`
- Auto-save: `AUTO_SAVE_REFINED_PROMPT=true` (or choose “save and always”)
- Pick later: `/OracleCPQ_SavedPrompts` or “use a saved prompt” → `start_prompt_picker`
- Library file: `.prompts/saved_prompts.json` (gitignored)

### What is Prompt Studio?

A **local** FastAPI UI to browse/search/favorite saved prompts and fill placeholders. It does **not** call Oracle CPQ.

After YES-gate site/cache CPQ work, agents call MCP tool **`ensure_prompt_studio`**, which probes `http://127.0.0.1:8765/api/health` and **auto-starts** Studio in the background if needed (then cites the URL). You can still start it manually:

```powershell
.\.venv\Scripts\python.exe -m pip install '.[prompt-studio]'
.\.venv\Scripts\python.exe -m apps.prompt_studio
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Details: [FEATURES.md — Prompt Studio](FEATURES.md#prompt-studio-enable-and-run) and [`apps/prompt_studio/README.md`](../apps/prompt_studio/README.md).

**New / Import / Export:** use toolbar **New**, **Import** (JSON + import name/tag + select rows), **Export all** / **Export selected**. The header shows the library file path. See the in-app **Help** view for start/restart commands.

### How do I restart Prompt Studio?

```powershell
.\.venv\Scripts\python.exe -m apps.prompt_studio restart
```

Or: `.\scripts\restart-prompt-studio.cmd` (Windows) / `./scripts/restart-prompt-studio.sh` (macOS/Linux).

That stops whatever is on port **8765** and starts Studio again. Hard-refresh the browser (**Ctrl+F5**). MCP `ensure_prompt_studio` only auto-starts when Studio is down — it does not restart a live process. See [QUICKSTART — Restart Prompt Studio](QUICKSTART.md#restart-prompt-studio-one-command).

**Edit prompts:** use **Edit** on a card or in the run modal — change title, original/refined text, enable/disable. Select text and click **Make variable** to wrap it as `{{snake_case}}` (e.g. `OCL , FPL` → `{{token_a}}`).

**Latest prompts missing after Refresh?**

1. Hover the status line — Studio path must match MCP’s `.prompts/saved_prompts.json` (Studio pins `CPQ_CONFIG_DIR` to `<repo>/.config` and `CPQ_SAVED_PROMPTS_PATH` to `<repo>/.prompts/saved_prompts.json` when unset).
2. If the status path shows **`.config/saved_prompts.json`**, you are on the legacy split library. Stop Studio, run `pip install -e ".[prompt-studio]"` from the repo root, restart `python -m apps.prompt_studio`, and confirm `/api/library_info` points at `.prompts/`. Merge any leftover rows from `.config/saved_prompts.json` into `.prompts/` if needed.
3. If **library last write** never changes, MCP did not call `save_refined_prompt` — enable `AUTO_SAVE_REFINED_PROMPT=true` on the active profile and reload MCP.
4. Similar tasks dedupe by content hash **and profile** — one row updates instead of a new card (same content under a different profile creates a separate row).
5. Toggle **Show disabled** if the prompt was soft-disabled.
6. Use the **Reload** banner when the file changes on disk (auto-detected every 30s / on window focus).
7. Use the **Profile** filter (All / Unscoped / named profiles). MCP saves stamp the active customer profile; older prompts without a stamp appear under **Unscoped**.

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
