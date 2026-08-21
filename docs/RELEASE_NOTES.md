# Release notes

Changelog for the **Oracle CPQ MCP** server. Format inspired by [Keep a Changelog](https://keepachangelog.com/).  
Package version today: **`0.1.0`** (see [`pyproject.toml`](../pyproject.toml)).

Related docs: [FEATURES.md](FEATURES.md) · [FAQ.md](FAQ.md) · [TOOL_CATALOG.md](TOOL_CATALOG.md) · [QUICKSTART.md](QUICKSTART.md) · [SECURITY.md](../SECURITY.md)

## How to refresh

```bash
python scripts/update_release_notes.py
```

The script regenerates **only** the git-backed list between `<!-- git-commits -->` markers from `git log` (idempotent). A **pre-commit** hook runs the same command; if the file changes, re-stage `docs/RELEASE_NOTES.md` and commit again.

Narrative sections above the markers are **hand-maintained** — update them when you ship meaningful features (do not rely on commit subjects alone).

## How to cut a versioned release

1. Bump `version` in [`pyproject.toml`](../pyproject.toml).
2. Move the current Unreleased **Highlights / Added / Changed / …** blocks under a new heading such as `## [0.2.0] - YYYY-MM-DD`.
3. Leave a fresh Unreleased section and keep the standalone git-commits HTML comment markers for future commits.
4. Commit and optionally tag: `git tag v0.2.0`.

---

## Unreleased

### Highlights

Major capability growth since the early “few tools + quickstart” phase: the server is now an **87-tool** CPQ agent surface with **local caching**, **reusable refined prompts**, optional **Prompt Studio** UI, and expanded **docs** (FAQ, features, formal catalog).

| Area | What you get |
|------|----------------|
| Tool catalog | **87** MCP tools across users, groups, datatables, BML, commerce, performance, parts, tasks, configuration, and meta |
| Local cache | Snapshots under `data/{profile}/{env}/` with ask/prefer/never policy |
| Refined prompts | Automatic end-of-task footer (title, tags, format, tools used, `{{vars}}`) + optional auto-save + picker |
| Prompt Studio | Local UI on **8765**: cards/list, favorites/suites, placeholder Run modal, expected output format |
| BML | Full zip export **and** extract to `data/.../bml/site/` for offline analysis |
| Docs | FAQ (incl. dual-env), FEATURES + HITL security, TOOL_CATALOG, pre-commit review |

### Added

#### MCP tools and domains

- Expanded catalog to **87 tools** with formal per-tool tables in [`TOOL_CATALOG.md`](TOOL_CATALOG.md) (regenerate: `python scripts/generate_tool_catalog.py`).
- **Tasks** — `get_task`, `download_task_file` (async export follow-up; **untested live**).
- **Configuration** — `productFamilies` / layout-cache family (list/get attributes, array sets, menu items, layouts; **untested live**).
- **Parts** — list/get/search parts.
- **Commerce transactions** — list/get transactions and lines, layouts, proposal/attachment/copy flows (writes remain dry-run + confirmation).
- **Performance logs** — list/get/export performance log events.
- Broader **BML** surface beyond zip export — scripts search, common functions, library folders, dependent attributes, library export (**some untested live**).
- Broader **datatables** — fields APIs, create/export (**create/export untested live**).
- **`discover_tools`** — filter the catalog by domain and read/write operation.

#### Saved refined prompts (automatic end-of-task footer)

After **any** CPQ-related task (live MCP tools, local `data/` cache reads, or both), the agent is instructed to append a reusable block:

```text
### Refined prompt (Better token usage)
```

That footer is intentionally detailed so the next run uses fewer tokens. It includes:

| Section | Purpose |
|---------|---------|
| **Title** | One-line name for the reusable prompt |
| **Tags** | Searchable labels (e.g. `users`, `bml`, `audit`) |
| **Output format** | `chat_text` (default), `json`, or `excel_download` — also as `{{output_format}}` |
| **Cached data** | `yes` / `no` / `mixed` (with path when cached) |
| **Prose body** | 1–3 plain-English paragraphs with `{{snake_case}}` placeholders |
| **Variables** | Explicit list (must include `{{output_format}}`) |
| **Tools (for the agent)** | Exact MCP tool names used / required, or `none (local file read only)` |

**Turn on/off the footer:** profile `REFINED_PROMPT=true` (default). Set `REFINED_PROMPT=false` (or `CPQ_REFINED_PROMPT=false`) to disable.

**Saving prompts (offer vs auto-save):**

- By default (`AUTO_SAVE_REFINED_PROMPT=false`), after the footer the agent calls `offer_save_refined_prompt` with choices: **save once** / **save and always** / **skip**.
- Choosing **save and always** writes `AUTO_SAVE_REFINED_PROMPT=true` via `set_auto_save_refined_prompt`, so future refined prompts are saved without asking (`save_refined_prompt`).
- Library file: `.config/saved_prompts.json` (gitignored). Each saved entry stores `output_format` and is honored when replayed.
- Disable entries with `set_saved_prompt_enabled` (disabled prompts stay hidden from pickers).

**Pick / reuse later:**

- Cursor: **`/OracleCPQ_SavedPrompts`** or say “use a saved prompt” → `start_prompt_picker` (all / search / by tag / by tool).
- Related tools: `list_saved_prompts`, `search_saved_prompts`, `get_saved_prompt`, `record_prompt_use`.
- Also exposed as MCP resource `cpq://saved-prompts` and prompt `run_saved_prompt`.

#### Local `data/` snapshots

- Path: `data/{profile}/{env}/…` (gitignored); override root with `CPQ_LOCAL_DATA_DIR`.
- Tools: `list_local_data`, `get_local_data_status`, `load_local_data`, `offer_use_local_data`, `set_local_data_policy`.
- Sync tools: `sync_users_local`, `sync_groups_local`, `sync_bml_local`, `sync_commerce_metadata_local`, `sync_datatable_local` / `sync_datatables_local`.
- Policy: `LOCAL_DATA_POLICY=ask|prefer|never` (default `ask`).
- Auto-persist from flows such as `export_users_excel` and `get_all_bml_code`.

#### BML zip + site extract

- `get_all_bml_code` (`delivery=zip`) downloads Commerce BML/BMLT via `/adminMeta`.
- Persist keeps the `.zip` **and** extracts the full tree to `data/.../bml/site/` (zip-slip safe; replaced each fetch).
- Manifest records `bml_zip`, `site_dir`, and extracted file `item_count`.
- Enables offline impact analysis (e.g. which BML files reference a data table).

#### Prompt Studio (optional local app)

Lightweight **local** FastAPI + static UI to work with the same saved-prompt library the MCP tools write — without calling Oracle CPQ.

**Install & run** (from repo root, prefer project venv):

```powershell
.\.venv\Scripts\python.exe -m pip install '.[prompt-studio]'
.\.venv\Scripts\python.exe -m apps.prompt_studio
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765) (binds to `127.0.0.1` only).

**What you can do in the UI:**

- **Cards** or **List** views of saved refined prompts from `.config/saved_prompts.json`
- **Refresh** to reload after MCP saves a new prompt
- Filter / search by tags; mark **favorites**; organize **suites**
- **Run** modal: fill `{{placeholders}}`, preview the resolved prompt, and see **expected response format** (Text / JSON / Excel) matching the saved `output_format`
- Studio-only state (favorites, suites, variable history) in `.config/prompt_studio.json` (gitignored)

**Not a substitute for MCP:** Prompt Studio does not hit CPQ APIs and does not bypass write guardrails. Use it to craft/reuse prompts; execute CPQ work through the MCP agent.

More detail: [`apps/prompt_studio/README.md`](../apps/prompt_studio/README.md) and [FEATURES — Prompt Studio](FEATURES.md#prompt-studio-enable-and-run).

#### Documentation

- [`FAQ.md`](FAQ.md) — install, credentials, **dual environments in one prompt**, security, cache, BML, Prompt Studio, troubleshooting.
- [`FEATURES.md`](FEATURES.md) — product capabilities + **security guardrails / human-in-the-loop**.
- [`PRE_COMMIT_REVIEW.md`](PRE_COMMIT_REVIEW.md) — secrets / catalog / test checklist before commit.
- [`TOOL_CATALOG.md`](TOOL_CATALOG.md) — formal Parameters / Filters tables for all tools.
- README + QUICKSTART updates (Antigravity-first MCP setup, Prompt Studio, FAQ link).

#### Packaging / tooling

- Hatch packaging fix: do not double-include `oracle_cpq_mcp` in `packages` + `force-include` (broken `pip install .`).
- `scripts/generate_tool_catalog.py` for regenerating TOOL_CATALOG from the registry.
- Shared Excel records helper for exports; users export can land under local `data/`.

### Changed

- [`.config/.env.example`](../.config/.env.example) documents `REFINED_PROMPT`, `AUTO_SAVE_REFINED_PROMPT`, `LOCAL_DATA_POLICY`, and related knobs.
- Server instructions and Cursor rules encode refined-prompt footer + local-data policy workflow.
- Schema integrity / validation / `tool_manifest.json` updated for the expanded catalog and new meta tools.
- Output envelopes remain consistent: `{status, tool, data}` (errors `{status: error, code, message, hint, details}`); file tools return `[envelope, File]`.

### Security (ongoing)

- Default **`READ_ONLY=true`** blocks mutations.
- Writes use **dry-run preflight** + HMAC **`confirmation_token`** (requires `CPQ_CONFIRMATION_SECRET` when writes enabled).
- Prod blocked unless `CPQ_ALLOW_PROD=1`.
- Credentials never belong in MCP JSON; see [SECURITY.md](../SECURITY.md) and [FAQ](FAQ.md).

### Known gaps / testing honesty

Offline unit/contract tests cover the catalog. Against **live** CPQ, these remain **untested** (see README table):

- Tasks (`get_task`, `download_task_file`)
- Configuration / `productFamilies` / layout cache
- Some newer BML extensions and datatable create/export writes

Previously shipped domains (users, groups, core datatable list/get/deploy, core BML export, commerce metadata, performance, parts, `discover_tools`) are in active use.

**Dual environments:** one MCP process = one active env. For a single prompt that analyzes **dev and test**, register two MCP server entries (`CPQ_ENVIRONMENT=dev` and `test`) or compare `data/{profile}/dev` vs `data/{profile}/test` — see [FAQ](FAQ.md#can-the-llm-connect-with-two-environments-at-the-same-time).

### Earlier milestones (summarized)

Useful context for readers skimming git history:

| Milestone | Summary |
|-----------|---------|
| Commerce metadata | Main + line attribute/action tools; process defaults from `COMMERCE_PROCESS_VAR_NAME` |
| BML export | `get_all_bml_code` zip + util-library JSON delivery |
| MCP quality | JSON Schema output contracts, best-practice envelopes/annotations/progress, schema integrity |
| Cross-platform MCP | Antigravity / Cursor / VS Code example configs; Windows `.cmd` + Unix `.sh` launchers |
| Catalog growth | Jump to **67** tools (tasks, configuration, parts, transactions) before the later **87** expansion |
| Quickstart | Restructured first-time setup (clone, profile, smoke test, IDE MCP) |

### Git commits (auto-generated)

<!-- git-commits -->
- `d88bb7b` some documentation
- `2ee4c83` Added couple of tools, better prompt suggestios, prompt studio
- `fda086e` release notes
- `a1b39e2` release notes
- `c000974` Expand MCP catalog to 67 tools with tasks, configuration, parts, and transactions.
- `b3f0445` updated quickstart
- `b5c97c5` updated documentation
- `c05cd49` updated documentation
- `494b2ee` Restructure QUICKSTART for clearer first-time setup flow.
- `90bb92c` Add cross-platform MCP config, output validation, and doc sync for 19 tools.
- `62f1a29` Add MCP best-practice envelopes, annotations, and progress
- `df85397` Add JSON Schema output contracts for all MCP tools
- `0714bcb` Add commerce and line-level attribute and action metadata tools
- `130ba9b` Add get_all_bml_code MCP tool for BML export and util library source
- `ceaa2a6` first commit
<!-- /git-commits -->
