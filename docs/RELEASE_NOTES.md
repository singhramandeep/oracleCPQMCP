# Release notes

Changelog for the Oracle CPQ MCP server. Format inspired by [Keep a Changelog](https://keepachangelog.com/).

## How to refresh

```bash
python scripts/update_release_notes.py
```

The script regenerates the git-backed list under `## Unreleased` from `git log` (idempotent). A **pre-commit** hook runs the same command; if the file changes, re-stage `docs/RELEASE_NOTES.md` and commit again.

## How to cut a versioned release

1. Bump `version` in [`pyproject.toml`](../pyproject.toml).
2. Move the current Unreleased commit bullets (and any Pending notes you want to keep) under a new heading such as `## [0.2.0] - YYYY-MM-DD`.
3. Leave a fresh Unreleased section and keep the standalone git-commits HTML comment markers for future commits.
4. Commit and optionally tag: `git tag v0.2.0`.

## Unreleased

### Working tree (not yet committed)

Pending local changes that are not in `git log` yet (remove or rewrite this subsection after they land in a commit). Grouped for the upcoming commit:

#### Added

- **MCP catalog → 87 tools** — formal tables in [`docs/TOOL_CATALOG.md`](TOOL_CATALOG.md) (`python scripts/generate_tool_catalog.py`); regenerated `tool_manifest.json` + schema integrity coverage
- **Saved refined prompts** — agent footer `### Refined prompt (Better token usage)` after CPQ work (live and/or local cache); tools `offer_save_refined_prompt`, `save_refined_prompt`, `list_saved_prompts`, `search_saved_prompts`, `get_saved_prompt`, `record_prompt_use`, `set_saved_prompt_enabled`, `start_prompt_picker`, `set_auto_save_refined_prompt`; library `.config/saved_prompts.json`; profile flags `REFINED_PROMPT`, `AUTO_SAVE_REFINED_PROMPT`; Cursor `/OracleCPQ_SavedPrompts` + skill
- **Local `data/` snapshots** — `data/{profile}/{env}/` with `list_local_data`, `get_local_data_status`, `load_local_data`, `offer_use_local_data`, `set_local_data_policy`, and `sync_*_local` (users/groups/BML/commerce/datatables); policy `LOCAL_DATA_POLICY=ask|prefer|never`; optional `CPQ_LOCAL_DATA_DIR`
- **BML zip extract** — `persist_bml_zip_snapshot` keeps the archive and extracts the site tree to `data/.../bml/site/` (zip-slip safe); manifest records `bml_zip` + `site_dir`; auto-persist from `get_all_bml_code`
- **Prompt Studio** — optional local FastAPI UI (`pip install '.[prompt-studio]'`, `python -m apps.prompt_studio` → http://127.0.0.1:8765); browse/search/favorites/suites, placeholder fill, expected output format; sidecar `.config/prompt_studio.json`
- **Excel helpers** — shared records exporter path used by user (and related) exports; users export can persist under local `data/`
- **Docs** — [`FEATURES.md`](FEATURES.md) (capabilities + security/HITL + Prompt Studio), [`PRE_COMMIT_REVIEW.md`](PRE_COMMIT_REVIEW.md), [`FAQ.md`](FAQ.md) (setup, dual-env MCP, cache, troubleshooting), README / QUICKSTART updates

#### Changed

- Profile template [`.config/.env.example`](.config/.env.example) — document refined-prompt, auto-save, and local-data policy knobs
- Server instructions / Cursor rules — refined-prompt footer + local-data policy workflow
- Schema integrity + validation — support expanded catalog and new local/saved-prompt tool schemas
- Hatch packaging — avoid double-including `oracle_cpq_mcp` in `packages` + `force-include` (fixes broken `pip install .`)

#### Notes / known gaps

- Scope C areas remain **untested live**: tasks, configuration (`productFamilies` / layoutcache), some newer BML/datatable write flows — see README testing-status table
- Dual-environment agent work: register two MCP server entries (`CPQ_ENVIRONMENT=dev` and `test`) or compare `data/{profile}/dev` vs `.../test` caches — see [FAQ — two environments](FAQ.md#can-the-llm-connect-with-two-environments-at-the-same-time)

<!-- git-commits -->
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
