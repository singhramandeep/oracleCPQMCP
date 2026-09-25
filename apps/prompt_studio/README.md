# Prompt Studio

Lightweight local UI to browse and fill saved refined prompts from `.prompts/saved_prompts.json`.

## Stack

- FastAPI + uvicorn (optional extra `prompt-studio`)
- Static HTML/CSS/JS (no React build)
- Prompt bodies: MCP library (`saved_library`) — **editable in Studio** (title, template, variables, enable/disable)
- Studio state: `.config/prompt_studio.json` (favorites, suites, variable history; gitignored)

## Install

Use the **project venv** (system Python often lacks deps and may hit a non-writable site-packages):

```powershell
.\.venv\Scripts\python.exe -m pip install '.[prompt-studio]'
```

Or install only the runtime deps into the venv:

```powershell
.\.venv\Scripts\python.exe -m pip install 'fastapi>=0.115.0' 'uvicorn[standard]>=0.30.0'
```

Running from repo root puts `mcp/` on `sys.path` automatically (no editable install required for Studio).

## Run

```powershell
.\.venv\Scripts\python.exe -m apps.prompt_studio
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Bound to localhost only; no auth in v1.

After updating Studio, **hard-refresh once** (Ctrl+F5) if buttons look stale; static assets use version cache-busting automatically on later loads.

## Restart

One command (repo root, project venv) — stops listeners on port **8765** (or `CPQ_PROMPT_STUDIO_PORT`), then starts Studio in the foreground:

```powershell
.\.venv\Scripts\python.exe -m apps.prompt_studio restart
```

```powershell
.\scripts\restart-prompt-studio.cmd
```

```bash
./scripts/restart-prompt-studio.sh
# or: ./.venv/bin/python -m apps.prompt_studio restart
```

Stop only:

```powershell
.\.venv\Scripts\python.exe -m apps.prompt_studio stop
```

MCP `ensure_prompt_studio` only **starts** Studio when `/api/health` is down; it does **not** restart a live process. After restart, hard-refresh the browser (**Ctrl+F5**).

### Env overrides

| Variable | Purpose |
|----------|---------|
| `CPQ_SAVED_PROMPTS_PATH` | Path to `saved_prompts.json` |
| `CPQ_PROMPT_STUDIO_PATH` | Path to studio sidecar JSON |
| `CPQ_CONFIG_DIR` | Config directory (auto-set to `<repo>/.config` on startup if unset) |

## Features (v1)

- Library browse with search and tag chips
- **Cards / List** layout toggle (persisted in the browser)
- Rich metadata: format, run count, last run, created, placeholders
- Favorites (star toggle)
- Suites (named ordered prompt lists; add from cards)
- **New prompt** — create a prompt manually in the UI
- **Import** — upload JSON (library / array / single), require an import name/tag, select/deselect rows; tags `imported` + `import:<slug>`
- **Export all** / **Export selected** — download library JSON
- **Help** — in-app docs for library path, start/restart commands, import/export
- Header shows the **absolute library file path** (click to copy)
- Run / fill: detect `{{snake_case}}` placeholders, recent values, Generate + Copy; `{{output_format}}` uses a dropdown (Text / JSON / Excel download)
- Run modal shows **expected response format** (Text by default; JSON / Excel download when set)
- **Refresh** reloads `.prompts/saved_prompts.json` after Cursor/MCP saves a refined prompt (status shows absolute path, counts, disabled count, and library last write). Toolbar binds are null-safe; static assets are cache-busted from the Studio version (`0.3.1+`).
- **Profile filter** — dropdown (All / Unscoped / each stamped profile). MCP `save_refined_prompt` stamps `profile` from the active CPQ customer profile; New prompt accepts an optional profile.
- **Auto-reload banner** when the library file changes on disk (poll + window focus)
- **Show disabled** toggle for prompts with `enabled=false`
- **Edit prompt** — change title, original/refined text, enable/disable; **Make variable** wraps selected text as `{{snake_case}}`
- Sorted by **most recent** (`last_run_at` / `created_at`) like MCP `list_saved_prompts`
- **Export all** downloads the full library JSON (`GET /api/prompts/download`; includes disabled prompts by default)
- Run modal shows **original user prompt** and refined template
- **Remove** on cards/list permanently deletes a prompt from the shared library after **two** confirms; also clears favorites/suite references

Studio and MCP share the same `.prompts/saved_prompts.json` (override with `CPQ_SAVED_PROMPTS_PATH`). On startup, Studio pins `CPQ_CONFIG_DIR` to `<repo>/.config/` and `CPQ_SAVED_PROMPTS_PATH` to `<repo>/.prompts/saved_prompts.json` when unset — matching MCP defaults.

**Prompts not appearing?**

1. Hover the status line — confirm the **absolute path** matches where MCP writes.
2. Check **library last write** — if it never changes, the agent did not call `save_refined_prompt` (set `AUTO_SAVE_REFINED_PROMPT=true` on the active profile and reload MCP).
3. Similar tasks **dedupe** by content hash — you may see one updated row instead of a new card.
4. Toggle **Show disabled** if a prompt was soft-disabled.
5. Click **Refresh** or use the **Reload** banner when the file changes on disk.
6. Use the **Profile** filter if you only want prompts stamped for one customer profile (leave **All profiles** to see everything; **Unscoped** shows rows with no profile).

## Backlog

- Export suite as one markdown / clipboard pack
- Record “generated at” + bump `record_use` via MCP when tools available
- Edit / soft-disable prompts from UI (**Edit** on cards + run modal; hard Remove still available)
- Keyboard shortcuts (`/`, `f` favorite, `g` generate)
- Deep-link `?prompt_id=` / `?suite=` (partially supported)
- Dark-mode workspace toggle
- Shareable filled-prompt file under `exports/`
- Duplicate prompt / clone into suite
- Suite “Run all” (v1 opens one-by-one)

## Out of scope

- Multi-user auth, cloud sync, calling Oracle CPQ from the studio
- Replacing Cursor MCP saved-prompt tools
