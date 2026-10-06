# Prompt Studio

Local UI (app **0.4.4+**) to browse, edit, rate, and fill saved refined prompts from `.prompts/saved_prompts.json`.

Does **not** call Oracle CPQ. Never edits profile passwords. The header always shows the running version badge (e.g. `v0.4.4`). Toolbar **Product** (CPQ/CX) and **CX module** filters use tags stamped by `save_refined_prompt`.

In-app **Help** (sidebar) mirrors this guide and uses live paths/commands from the server.

## Contents

1. [Stack](#stack)
2. [Install](#install)
3. [Run / restart / stop](#run--restart--stop)
4. [Env overrides](#env-overrides)
5. [Library & MCP](#library--mcp)
6. [Browse & filters](#browse--filters)
7. [New / Import / Export](#new--import--export)
8. [Run, edit, ratings](#run-edit-ratings)
9. [Suites & favorites](#suites--favorites)
10. [API logs](#api-logs)
11. [Profiles & Paths](#profiles--paths)
12. [Troubleshooting](#troubleshooting)
13. [Backlog / out of scope](#backlog--out-of-scope)

## Stack

- FastAPI + uvicorn (optional extra `prompt-studio`)
- Static HTML/CSS/JS (no React build)
- Prompt bodies: MCP library (`saved_library`) — **editable in Studio**
- Studio state: `.config/prompt_studio.json` (favorites, suites, variable history; gitignored)

## Install

Use the **project venv**:

```powershell
.\.venv\Scripts\python.exe -m pip install '.[prompt-studio]'
```

Or runtime deps only:

```powershell
.\.venv\Scripts\python.exe -m pip install 'fastapi>=0.115.0' 'uvicorn[standard]>=0.30.0'
```

Running from repo root puts `mcp/` on `sys.path` automatically.

## Run / restart / stop

```powershell
.\.venv\Scripts\python.exe -m apps.prompt_studio
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765) (localhost only; no auth in v1). Confirm the header badge matches the package version after upgrades.

**Restart** (stops port **8765** / `CPQ_PROMPT_STUDIO_PORT`, then starts):

```powershell
.\.venv\Scripts\python.exe -m apps.prompt_studio restart
.\scripts\restart-prompt-studio.cmd
```

```bash
./scripts/restart-prompt-studio.sh
```

**Stop only:** `python -m apps.prompt_studio stop`

MCP `ensure_prompt_studio` only **starts** Studio when `/api/health` is down; it does **not** restart a live process. After restart or upgrade, hard-refresh (**Ctrl+F5**). Static assets are cache-busted with `?v=<studio version>`.

## Env overrides

| Variable | Purpose |
|----------|---------|
| `CPQ_SAVED_PROMPTS_PATH` | Path to `saved_prompts.json` |
| `CPQ_PROMPT_STUDIO_PATH` | Path to studio sidecar JSON |
| `CPQ_CONFIG_DIR` | Config directory (auto-set to `<repo>/.config` on startup if unset) |
| `CPQ_DEBUG_LOG_DIR` | Override directory for DEBUG_MODE `*.log` files (default `<repo>/logs`) |
| `CPQ_PROMPT_STUDIO_PORT` | Listen port (default `8765`) |

On startup, Studio pins `CPQ_CONFIG_DIR` and `CPQ_SAVED_PROMPTS_PATH` to repo defaults when unset — matching MCP.

## Library & MCP

Studio and MCP share `.prompts/saved_prompts.json`. Agents save via `save_refined_prompt` when `AUTO_SAVE_REFINED_PROMPT=true` on the active profile. The header shows the absolute library path (click to copy), prompt counts, and **version badge**.

## Browse & filters

- **Cards / List** layout toggle (persisted). List columns: title, rating, format, runs, last run, actions.
- Search, sidebar **tags**, **Profile** (All / Unscoped / stamped), **Rating** (All / Unrated / Rated / 7+ / 8+ / 9+ / 10), Favorites, **Show disabled**.
- Sorted by most recent (`last_run_at` / `created_at`).
- Auto-reload **banner** when the library file changes on disk (poll + window focus); **Refresh** reloads manually.

## New / Import / Export

- **New** — create a prompt (optional profile stamp, output format).
- **Import** — JSON library / array / single; require import name/tag; tags `imported` + `import:<slug>`; preserves rating/comments/telemetry without bumping runs.
- **Export all** / **Export selected** — download library JSON (includes feedback + per-source stats). Full download: `GET /api/prompts/download`.

## Run, edit, ratings

- **Run** — fill `{{snake_case}}` placeholders (recent values, Generate + Copy); `{{output_format}}` dropdown (Text / JSON / Excel download).
- **Edit** — title, original user prompt, refined template, enabled. **Make variable** wraps selection. Edit textareas **auto-grow** (still vertically resizable; capped for very long prompts).
- **Ratings (1–10)** + comments in the Run modal; rating badge on cards and list; toolbar rating filter.
- **Run telemetry** — Cached / API / Mixed last + average durations (never blended). MCP `record_prompt_use` records `duration_ms` + `source`.
- **Remove** — two confirms; clears favorites/suite references.

## Suites & favorites

Star for Favorites. Suites are named ordered lists (Suites view or card menu → Add to suite).

## API logs

Browse `logs/{profile}-{env}.log` from DEBUG_MODE: charts, filters, copy curl/blocks/JSON, download raw. Enable `DEBUG_MODE=true` on the CPQ profile. Curl passwords are redacted (`user:***`).

## Profiles & Paths

Read-only redacted profile YAML (`.config/<id>.yaml` only; never `.env`) plus copyable paths for library, studio state, logs, local cache, and exports. You own credentials — do not edit passwords in Studio.

## Troubleshooting

1. Hover the status line — confirm the **absolute path** matches where MCP writes.
2. If **library last write** never changes, the agent did not call `save_refined_prompt` (set `AUTO_SAVE_REFINED_PROMPT=true`, reload MCP).
3. Similar tasks **dedupe** by content hash **and profile**.
4. Toggle **Show disabled** for soft-disabled prompts.
5. Use **Refresh** / the Reload banner after disk updates.
6. Use the **Profile** filter (or leave All) if prompts seem missing.
7. Header still shows `v?` → `/api/health` failed; restart Studio and hard-refresh.

## Backlog / out of scope

**Backlog:** suite markdown pack, keyboard shortcuts, deep-links, dark mode, duplicate into suite, suite “Run all”.

**Out of scope:** multi-user auth, cloud sync, calling Oracle CPQ from Studio, editing profile credentials, replacing Cursor MCP saved-prompt tools.
