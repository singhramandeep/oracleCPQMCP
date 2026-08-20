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

Pending local changes that are not in `git log` yet (remove or rewrite this subsection after they land in a commit):

- Full API expansion (scope C): catalog **67** tools (was 41)
- New domains: **tasks** (`get_task`, `download_task_file`), **configuration** (productFamilies / layoutcache composites)
- Datatables: `create_datatable`, `export_datatables` (dry-run + confirmation)
- BML extensions: scripts search, common functions, library folders, dependentAttributes, library export
- Docs mark these additions as **untested (live)**; offline unit/contract tests cover them

<!-- git-commits -->
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
