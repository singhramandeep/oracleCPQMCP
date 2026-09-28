# Release notes

Changelog for the **Oracle CPQ MCP** server. Format inspired by [Keep a Changelog](https://keepachangelog.com/).  
Package version today: **`0.3.0`** (see [`pyproject.toml`](../pyproject.toml)).

Related docs: [FEATURES.md](FEATURES.md) · [FAQ.md](FAQ.md) · [TOOL_CATALOG.md](TOOL_CATALOG.md) · [LIVE_SMOKE_MATRIX.md](LIVE_SMOKE_MATRIX.md) · [SETUP.md](SETUP.md) · [QUICKSTART.md](QUICKSTART.md) · [SECURITY.md](../SECURITY.md) · [README — Update the package version](../README.md#update-the-package-version)

## How to refresh

```bash
python scripts/update_release_notes.py
```

The script regenerates **only** the git-backed list between `<!-- git-commits -->` markers from `git log` (idempotent). A **pre-commit** hook runs the same command; if the file changes, re-stage `docs/RELEASE_NOTES.md` and commit again.

Narrative sections above the markers are **hand-maintained** — update them when you ship meaningful features (do not rely on commit subjects alone).

## How to cut a versioned release

See also the contributor checklist in the [README](../README.md#update-the-package-version).

1. Bump `version` in [`pyproject.toml`](../pyproject.toml).
2. Move the current Unreleased **Highlights / Added / Changed / …** blocks under a new heading such as `## [0.3.0] - YYYY-MM-DD`.
3. Leave a fresh Unreleased section and keep the standalone git-commits HTML comment markers for future commits.
4. If tools changed: regenerate `tool_manifest.json` and `docs/TOOL_CATALOG.md`, then run tests.
5. Commit and optionally tag: `git tag v0.3.0`.

---

## Unreleased

Package remains **`0.3.0`**; Prompt Studio app is **`0.4.3`**. Narrative below includes everything still shipping under Unreleased; **bold items marked “since last notes pass”** are the delta after the prior documentation revision (`d004860` → `c8ef795` and related).

### Highlights

- Branded Word/Excel/PPT exports via `.config/template/` + Mermaid diagrams in analytical Word exports (local `mmdc`, center-aligned, structured `notes`).
- Prompt Studio **0.3.1**: fixed Refresh cache-bust / event binds; **Profile** filter on saved prompts (stamped from active CPQ customer).
- Prompt Studio **0.3.2**: **API logs** view — parse `logs/{profile}-{env}.log`, status/latency charts, filters, copy curl/blocks/JSON, download raw.
- Prompt Studio **0.4.0**: prompt ratings (1–10) + comments; per-source cache/api/mixed run telemetry via `record_prompt_use`; read-only **Profiles & Paths** (redacted YAML + workspace path map); import/export preserves feedback/telemetry without double-counting runs.
- **Since last notes pass — Prompt Studio 0.4.1–0.4.3:** list column alignment + default rating badge + toolbar rating filter; autosizing Original/Refined edit textareas; permanent header version badge; expanded in-app Help + README; agents prefer Mermaid **pie** / **xychart-beta** / **flowchart** by content for Word diagrams.
- Unified customer profile: prefer one gitignored `.config/<id>.yaml` (secrets + catalog); legacy `.env` / `.catalog.yaml` still load when no full YAML exists.
- Removed committed `.config/.catalog.yaml.example` (use `example.yaml` only; legacy sidecars still load for `.env` upgrades).
- Installable maintainer CLI: `oracle-cpq` (`migrate-yaml`, `migrate-catalog`, `lint-schemas`, `generate-tool-catalog`); `scripts/*.py` are thin wrappers.
- Profile defaults: `local_data_policy=prefer`, `post_response_export=always_excel` (aliases `true`/`yes`/`on` accepted); example includes a commented setup prompt to sync `product_families` from live CPQ.
- Slim profile config / unified YAML migrate docs: FAQ “How do I migrate from a legacy `.env` to `.yaml`?”; QUICKSTART (full guide); SETUP (8-step quick guide) prefers `.config/example.yaml` (renamed from `.profile.yaml.example`).
- Agents call `ensure_prompt_studio` after YES-gate CPQ work (auto-start local UI on port 8765 when down).
- Docs: `SETUP.md` is the 8-step quick guide; `QUICKSTART.md` is the full setup guide.

### Added

- `oracle_cpq_mcp.exporters.branded_documents` and `mermaid_render` (clone templates; local Mermaid PNG).
- Word `diagrams` on `export_response_word`; lightweight structured `notes` (`##` / bullets); center-aligned diagram images/captions; tall-diagram height cap.
- Cross-IDE agent policy in `AGENTS.md` + MCP `DOCUMENT_TEMPLATES` (Mermaid expected for analytical Word without user ask).
- Prompt Studio profile stamp/filter (`SavedPrompt.profile`, `GET /api/profiles`, toolbar select); restart scripts `scripts/restart-prompt-studio.*`.
- MCP tools `list_product_hierarchy_table` and `list_commerce_processes_table` (flat variable-name tables).
- MCP tool `ensure_prompt_studio` — probe/auto-start local Prompt Studio after YES-gate site/cache turns (catalog **122** tools; see `docs/TOOL_CATALOG.md`).
- [`mcp/oracle_cpq_mcp/core/profile_yaml.py`](../mcp/oracle_cpq_mcp/core/profile_yaml.py) full-document loader; [`scripts/migrate_profile_yaml.py`](../scripts/migrate_profile_yaml.py); [`.config/example.yaml`](../.config/example.yaml).
- `PyYAML` dependency and [`mcp/oracle_cpq_mcp/core/catalog.py`](../mcp/oracle_cpq_mcp/core/catalog.py) loader (`load_catalog`, flat `PRODUCT_FAMILY_*` parser).
- [`scripts/migrate_profile_catalog.py`](../scripts/migrate_profile_catalog.py) (deprecated sidecar helper; prefer `migrate_profile_yaml.py` / `oracle-cpq migrate-yaml`).
- Product family / line / model aliases injected into MCP server instructions.
- Prompt Studio ratings/comments APIs (`PATCH /api/prompts/{id}/rating`, comment CRUD) and per-source stats on prompt summaries.
- Read-only `GET /api/config/profiles`, `GET /api/config/profiles/{id}`, `GET /api/workspace/paths` (redacted YAML; never `.env`).
- `record_prompt_use` **1.1.0** optional `duration_ms` + `source=cache|api|mixed` (averages never blended). Optional `profile` / `environment` may be stripped by some MCP hosts — duration/source are sufficient.
- **Since last notes pass:** Prompt Studio library `rating_filter` (`unrated`|`rated`) and `min_rating` (1–10) on `search_entries` / `GET /api/prompts`; toolbar Rating select (persisted).
- **Since last notes pass:** `/api/health` and `/api/library_info` return `version`; UI `#studioVersion` badge always visible.
- **Since last notes pass:** `export_response_word` catalog **1.2.0** + MCP `DOCUMENT_TEMPLATES` / `AGENTS.md` / Cursor `document-templates` mirror — choose Mermaid `pie` (shares), `xychart-beta` (numeric bars/lines), `flowchart`/`graph` (flows); pictographs only via optional `image_path` PNG under `tmp/`.

### Changed

- Prompt Studio static assets cache-bust via regex on served HTML (Studio app **0.3.1**); Refresh/toolbar binds are null-safe.
- Saved-prompt dedupe is per **content hash + profile** (same template under different profiles = separate rows).
- Example profiles default `AUTO_SAVE_REFINED_PROMPT=true` (user owns live profile flags).
- Saved-prompt upsert/import no longer treat save/import as completed runs; import preserves rating/comments/telemetry.
- **Since last notes pass:** Prompt Studio list layout uses fixed shared CSS grid tracks (`minmax(0, …)`) so Rating / Format / Runs / Last run columns stay aligned; rating shown on card title row.
- **Since last notes pass:** Edit-mode Original/Refined textareas autosize to content (`autosizeCodeEdit`); larger min-heights; `max-height: min(45vh, 420px)`.
- **Since last notes pass:** Prompt Studio Help (`GET /api/help`) and [`apps/prompt_studio/README.md`](../apps/prompt_studio/README.md) expanded (TOC, filters, ratings, Paths, restart); FAQ/FEATURES/QUICKSTART/PRE_COMMIT point at Studio **0.4.3+**.
- Profile template path renamed `.config/.profile.yaml.example` → `.config/example.yaml` (gitignore + Prompt Studio config viewer blocked stem `example`).

### Fixed

- Empty Word/Excel table rows when agents passed list-of-list sheet `rows` — `coerce_sheet_records` maps positional lists to column dicts before Excel/Word builders.
- MCP startup fail-closed on stale `tool_manifest.json` after tool-description edits — regenerate via `write_manifest_file()` / commit updated hash (required after `export_response_word` **1.2.0** text).
- Invalid profile YAML `local_data_policy: true` (bool) rejected by schema — must be `ask`|`prefer`|`never` (string).

### Git commits (auto-generated)

<!-- git-commits -->
- `c8ef795` feature additions
- `d004860` improved documentation
- `b5bba1d` generic improvements
- `3f86111` generic improvements
- `2b890d5` committed some leftovers
- `3f71082` Ship branded Word/Mermaid exports and Prompt Studio profile filter.
- `9afbe0c` add yaml support
- `62bcf6f` Ship 0.3.0 agent UX and Prompt Studio editing.
- `17d2b93` major feature addition
- `32f8320` major feature addition
- `f90354a` some documentation
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

---

## [0.3.0] - 2026-09-01

### Highlights

Agent-UX release: **async BML jobs**, **local cache resources**, **dual-env examples**, **capability/smoke honesty**, configurable HTTP timeouts. Catalog **103** tools.

| Area | What you get |
|------|----------------|
| Async BML | `start_bml_site_export` → poll `get_local_job` (avoids multi-minute MCP blocks) |
| Local search | `search_local_bml` over `data/.../bml/site/` |
| Resources | `cpq://local`, `cpq://local/bml/{path}` |
| Timeouts | Profile `HTTP_TIMEOUT` / host `CPQ_HTTP_TIMEOUT` (default 60s) |
| Dual env | `.cursor/mcp.json.dual.example.json` + Antigravity dual example; envelopes stamp `profile` |
| Honesty | [`LIVE_SMOKE_MATRIX.md`](LIVE_SMOKE_MATRIX.md) + capability card in server instructions |

### Added

- `start_bml_site_export`, `get_local_job`, `search_local_bml`
- MCP resources for local data index and BML file reads
- Dual-MCP config examples; FAQ async agent loop for BML/exports
- Configurable HTTP timeout (5–3600s)

### Changed

- Tool envelopes include `profile` (alias of `customer_id`) plus `environment`
- `get_all_bml_code` docs point agents at async job path for large sites
- Package version **0.3.0**

---

## [0.2.0] - 2026-08-26

### Highlights

**100 MCP tools**, local caching, reusable refined prompts, optional Prompt Studio, and stronger operator diagnostics.

| Area | What you get |
|------|----------------|
| Tool catalog | **100** tools — users, groups, datatables, BML, commerce (incl. saved searches), metrics, collab, **admin** (certificates/SSO), performance, parts, tasks, configuration, meta |
| Diagnostics | **DEBUG_MODE** file logging of redacted CPQ request traces under `logs/{profile}-{environment}.log` |
| Local cache | Snapshots under `data/{profile}/{env}/` with ask/prefer/never policy |
| Refined prompts | End-of-task footer + optional auto-save + picker |
| Prompt Studio | UI on **8765** — cards/list, favorites/suites, Run modal, **Download all** library JSON |
| Docs | FAQ, FEATURES, formal TOOL_CATALOG, contributor version-bump section in README |

### Added

#### This release focus

- Commerce **saved searches** — `list_saved_searches`, `get_saved_search` (`GET /searchResources/...`; resource defaults from commerce process var).
- Site **admin** domain — `list_certificates`, `get_certificate`, `get_sso_configuration`; PEM / IdP / SAML keystore fields redacted to `[REDACTED]`.
- Prompt Studio **Download all** — `GET /api/prompts/download` (full `.prompts/saved_prompts.json`; includes disabled by default).
- **DEBUG_MODE API file logging** — profile `DEBUG_MODE` (default `true`; host `CPQ_DEBUG_MODE` / `CPQ_DEBUG_LOG_DIR`). Appends timestamped, redacted request traces (curl + parameters) to `logs/{profile}-{environment}.log`. Passwords stay `***`; response bodies are not logged. Live `CPQClient` HTTP only (cache-only work writes nothing).
- Formal catalog at **100** tools ([`TOOL_CATALOG.md`](TOOL_CATALOG.md); regenerate: `python scripts/generate_tool_catalog.py`).

#### Catalog domains already in this line (summary)

Shipped earlier in the 0.1.x → 0.2.0 growth path (not re-listed as new APIs this week):

- Metrics (`list_metrics`), collab queues, commerce UI settings, transactions, performance logs, parts, tasks, configuration (`productFamilies`), broader BML/datatables, `discover_tools`.
- Refined-prompt footer + library tools; local `data/` sync policy; post-response Excel/Word export.
- BML zip + extract to `data/.../bml/site/`; Prompt Studio app; FAQ / FEATURES / pre-commit docs.

Details for those areas remain in [FEATURES.md](FEATURES.md) and the README domain summary.

### Changed

- README tool list slimmed to a **domain summary** (full per-tool tables live in TOOL_CATALOG).
- README adds **Update the package version** for contributors cutting releases.
- `.env.example` / server instructions cover DEBUG_MODE, refined prompts, local-data policy, post-response export.
- Schema integrity / `tool_manifest.json` updated for the 100-tool catalog.

### Security

- Default **`READ_ONLY=true`**; writes use dry-run + HMAC `confirmation_token`.
- Certificate/SSO PEM material never returned unredacted through MCP.
- Credentials never belong in MCP JSON — [SECURITY.md](../SECURITY.md).

### Known gaps / testing honesty

Offline unit/contract tests cover the catalog. Against **live** CPQ, still **untested**:

- Tasks (`get_task`, `download_task_file`)
- Configuration / `productFamilies` / layout cache
- Some newer BML extensions and datatable create/export writes
- Saved searches / certificates / SSO may 404 on sites still on REST **v18** (Oracle docs target **v19**)

**Dual environments:** one MCP process = one active env. For dev+test in one prompt, use two MCP entries or compare `data/{profile}/dev` vs `test` — [FAQ](FAQ.md#can-the-llm-connect-with-two-environments-at-the-same-time).

### Earlier milestones (summarized)

| Milestone | Summary |
|-----------|---------|
| Commerce metadata | Main + line attribute/action tools; process defaults from `COMMERCE_PROCESS_VAR_NAME` |
| BML export | `get_all_bml_code` zip + util-library JSON delivery |
| MCP quality | JSON Schema output contracts, envelopes/annotations/progress, schema integrity |
| Cross-platform MCP | Antigravity / Cursor / VS Code examples; `.cmd` + `.sh` launchers |
| Catalog growth | 67 → 87 → **100** tools |
| Quick setup (`SETUP.md`) | 8-step first-time path |
| Full setup guide (`QUICKSTART.md`) | Detailed install, MCP connect, samples |

### Git commits (through 0.2.0 cut)

<!-- git-commits-0.2.0 -->
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
<!-- /git-commits-0.2.0 -->

Note: the live auto-update script only rewrites the **Unreleased** `<!-- git-commits -->` block. Historical lists above are frozen for this release.
