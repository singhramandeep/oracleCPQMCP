# Prompt Studio

Lightweight local UI to browse and fill saved refined prompts from `.config/saved_prompts.json`.

## Stack

- FastAPI + uvicorn (optional extra `prompt-studio`)
- Static HTML/CSS/JS (no React build)
- Prompt bodies: existing MCP library (`saved_library`) — read-only from the studio
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

### Env overrides

| Variable | Purpose |
|----------|---------|
| `CPQ_SAVED_PROMPTS_PATH` | Path to `saved_prompts.json` |
| `CPQ_PROMPT_STUDIO_PATH` | Path to studio sidecar JSON |

## Features (v1)

- Library browse with search and tag chips
- **Cards / List** layout toggle (persisted in the browser)
- Rich metadata: format, run count, last run, created, placeholders
- Favorites (star toggle)
- Suites (named ordered prompt lists; add from cards)
- Run / fill: detect `{{snake_case}}` placeholders, recent values, Generate + Copy
- Run modal shows **expected response format** (Text by default; JSON / Excel download when set)
- **Refresh** reloads `.config/saved_prompts.json` after Cursor/MCP saves a refined prompt

After an agent saves a new refined prompt, click **Refresh** in the toolbar so the library updates (no auto-poll).

## Backlog

- Export suite as one markdown / clipboard pack
- Record “generated at” + bump `record_use` via MCP when tools available
- Edit/disable prompts from UI (write through to saved library)
- Keyboard shortcuts (`/`, `f` favorite, `g` generate)
- Deep-link `?prompt_id=` / `?suite=` (partially supported)
- Dark-mode workspace toggle
- Shareable filled-prompt file under `exports/`
- Duplicate prompt / clone into suite
- Suite “Run all” (v1 opens one-by-one)

## Out of scope

- Multi-user auth, cloud sync, calling Oracle CPQ from the studio
- Replacing Cursor MCP saved-prompt tools
