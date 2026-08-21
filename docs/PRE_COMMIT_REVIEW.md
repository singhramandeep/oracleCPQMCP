# Pre-commit review checklist

Use this before committing large batches (Prompt Studio, local data, saved prompts, catalog growth).

## Do not commit (secrets / local state)

Confirm these stay **untracked / ignored**:

- [ ] `.config/*.env` (real credentials) — only `.config/.env.example` is OK
- [ ] `.config/saved_prompts.json` and `.config/prompt_studio.json`
- [ ] `data/`, `dat/`, `exports/`, `*.xlsx` under exports
- [ ] `.venv/`, `__pycache__/`, `.pytest_cache/`
- [ ] Local MCP configs: `.cursor/mcp.json`, `.agents/mcp_config.json`, `.vscode/mcp.json`
- [ ] Any file with real passwords, tokens, or customer dumps

`git check-ignore -v` on suspected paths if unsure.

## Should commit (typical for this wave)

- [ ] `apps/prompt_studio/` (+ `apps/__init__.py`)
- [ ] `mcp/oracle_cpq_mcp/prompts/`, `tools/local_data.py`, `tools/saved_prompts.py`, `core/local_data.py`
- [ ] Registry / validation / `tool_manifest.json` / schema integrity updates
- [ ] `scripts/generate_tool_catalog.py`, `docs/TOOL_CATALOG.md`
- [ ] `docs/FEATURES.md`, `docs/RELEASE_NOTES.md`, `docs/QUICKSTART.md`, `README.md`
- [ ] Tests: `tests/test_prompt_studio.py`, `test_local_data.py`, `test_saved_prompts.py`, …
- [ ] `pyproject.toml` optional extra `prompt-studio`; hatch wheel fix (no duplicate `oracle_cpq_mcp`)
- [ ] `.gitignore` entries for studio sidecar + saved prompts
- [ ] `.cursor/rules/`, `.cursor/commands/`, `.cursor/skills/` if intentional for the team
- [ ] `command-center-DESIGN.md` if you want design tokens in-repo

## Consistency gates (run before commit)

```powershell
.\.venv\Scripts\python.exe scripts\generate_tool_catalog.py
.\.venv\Scripts\python.exe scripts\lint_tool_schemas.py
.\.venv\Scripts\python.exe -m pytest -q -m "not live_eval"
```

- [ ] Catalog tool count matches README / FEATURES (currently **87**)
- [ ] `tool_manifest.json` regenerated/updated with new tools (schema integrity)
- [ ] No failing unit tests; launcher example tests if you changed MCP JSON examples

## Product / ops checks

- [ ] Reload MCP after pull so new tools (`*_local`, saved prompts) appear
- [ ] Prompt Studio: `pip install '.[prompt-studio]'` then `python -m apps.prompt_studio`
- [ ] Writes still default `dry_run=true`; `READ_ONLY=true` in example profile
- [ ] Document live **untested** domains honestly (tasks, configuration, some BML/datatable writes)

## Commit hygiene

- [ ] Prefer focused commits (docs vs features vs security) if the diff is large
- [ ] Do **not** amend published commits; do **not** force-push main
- [ ] After commit, if pre-commit rewrites `RELEASE_NOTES.md`, re-stage and commit again (or run `python scripts/update_release_notes.py`)
