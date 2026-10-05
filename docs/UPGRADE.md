# Upgrade — existing MCP installs

Step-by-step commands to move an **older Oracle CPQ MCP checkout** to the latest code without redoing first-time setup.

**First-time install?** Use [SETUP.md](SETUP.md) (quick) or [QUICKSTART.md](QUICKSTART.md) (full).  
**What’s new?** [RELEASE_NOTES.md](RELEASE_NOTES.md).  
**Short checklist:** [README — Update from an older version](../README.md#update-from-an-older-version).

Open the **IDE integrated terminal** (`` Ctrl+` ``). Run every command from the **repository root** (folder that contains `pyproject.toml`).

---

## Who this is for

- You already cloned (or unzipped) this repo and connected Oracle CPQ MCP in Antigravity, Cursor, or VS Code.
- You want the latest tools, docs, and MCP server instructions.
- You want to **keep** passwords, profile YAML/`.env`, local `data/`, and IDE MCP JSON.

You do **not** need to recreate credentials or re-copy MCP config from scratch.

---

## Before you start

| Do | Do not |
|----|--------|
| Pull / reinstall into the **same** `.venv` your MCP launcher uses | Overwrite a live `.config/<profile>.yaml` with `example.yaml` (wipes URLs/passwords) |
| Keep `.agents/mcp_config.json`, `.cursor/mcp.json`, `.vscode/mcp.json` as-is | Put CPQ passwords into MCP JSON |
| Skim [RELEASE_NOTES.md](RELEASE_NOTES.md) for breaking notes | Delete `data/`, `logs/`, or `.prompts/` unless you intend to |

Never edit `username` / `password` (or `*_USERNAME` / `*_PASSWORD`) in profile files as part of an upgrade — you own credentials. On 401 after upgrade, fix passwords yourself; do not ask an agent to “repair” them.

---

## Step 1 — Open the project and terminal

1. In your IDE: **File → Open Folder** → select the `oracleCPQMCP` project root (must contain `pyproject.toml`).
2. Open the integrated terminal: `` Ctrl+` ``.
3. Confirm you are at the repo root:

```bash
# Windows PowerShell / CMD / macOS / Linux / Git Bash
pwd
# Expect a path ending in oracleCPQMCP (or your clone name)
dir pyproject.toml   # Windows CMD / PowerShell: also `ls pyproject.toml`
# macOS / Linux: ls pyproject.toml
```

If the file is missing, `cd` into the clone first (examples):

```powershell
# Windows PowerShell — adjust the path to your machine
cd C:\Users\YourName\workspaces\oracleCPQMCP
```

```bash
# macOS / Linux / Git Bash
cd ~/workspaces/oracleCPQMCP
```

---

## Step 2 — Confirm location, branch, and remote

```bash
git status
git remote -v
git branch --show-current
```

Expected remote (default):

`https://github.com/singhramandeep/oracleCPQMCP.git`

If `git` says this is not a repository, you likely installed from a **ZIP** — skip to [Step 3b — ZIP-only installs](#step-3b--zip-only-installs-no-git).

---

## Step 3 — Get the latest code (git)

### Clean working tree

If `git status` is clean (or only shows gitignored files such as `.config/*.yaml`):

```bash
git fetch origin
git pull
```

If you track `main` explicitly:

```bash
git fetch origin
git pull origin main
```

### Local changes you care about

```bash
# Option A — stash, pull, restore
git stash push -u -m "pre-upgrade"
git pull
git stash pop

# Option B — commit on a branch, then pull / rebase as you usually do
git add -A
git commit -m "WIP before upgrade"
git pull
```

If `git pull` reports **merge conflicts**, resolve the conflicted files, then:

```bash
git add <resolved-files>
git commit   # only if a merge commit is required
```

Do **not** resolve conflicts by overwriting your live profile YAML with the example template.

### Step 3b — ZIP-only installs (no git)

Prefer switching to git once:

```bash
# Outside the old folder — example paths
cd ~/workspaces   # or your Windows workspaces path
git clone https://github.com/singhramandeep/oracleCPQMCP.git oracleCPQMCP-new
```

Then **copy local-only data** from the old folder into the new clone (do not commit these):

| From old install | Into new clone |
|------------------|----------------|
| `.config/*.yaml` (and any `.env` you still use) | `.config/` |
| `.config/archive/` | `.config/archive/` |
| `data/` | `data/` |
| `logs/` | `logs/` |
| `.prompts/` | `.prompts/` |
| `.agents/mcp_config.json` | `.agents/mcp_config.json` |
| `.cursor/mcp.json` | `.cursor/mcp.json` |
| `.vscode/mcp.json` | `.vscode/mcp.json` |
| Customized `.config/template/` (if you changed branding) | `.config/template/` |

Open the new folder in the IDE and continue from [Step 4](#step-4--activate-the-same-venv). Update MCP JSON paths if the folder name changed.

If you must stay on ZIP: download a fresh ZIP from GitHub, extract beside the old folder, copy the same paths above into the new extract, then open that folder.

---

## Step 4 — Activate the same venv

Use the **existing** `.venv` at the repo root (recreate only if missing or broken).

**Create only if `.venv` is missing:**

```bash
python -m venv .venv
```

**Windows PowerShell** (typical Cursor / VS Code terminal on Windows):

```powershell
.venv\Scripts\Activate.ps1
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
```

**Windows CMD:**

```bat
.venv\Scripts\activate.bat
```

**macOS / Linux / Git Bash:**

```bash
source .venv/bin/activate
```

Your prompt should show `(.venv)`. Confirm:

```bash
python --version
where python   # Windows
which python   # macOS / Linux / Git Bash
```

---

## Step 5 — Reinstall the package and extras

With the venv active, from the repo root:

```bash
python -m pip install --upgrade pip
python -m pip install --prefer-binary -e ".[dev]"
```

Optional extras (install the ones you already use):

```bash
python -m pip install --prefer-binary -e ".[prompt-studio]"   # Prompt Studio UI
python -m pip install --prefer-binary -e ".[docs]"            # Word export (python-docx)
```

Optional — Mermaid CLI for Word diagrams (needs [Node.js LTS](https://nodejs.org/)):

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc --version
```

If `mmdc` is not found, close and reopen the IDE terminal so PATH picks up the npm global bin, then retry `mmdc --version`. Detail: [QUICKSTART §2.1](QUICKSTART.md#21-optional--mermaid-cli-for-word-diagrams).

Confirm the CLI entry points resolve:

```bash
oracle-cpq-smoke --help
python -m oracle_cpq_mcp --help
```

---

## Step 6 — Legacy `.env` → YAML (only if needed)

New setups use **one** file: `.config/<id>.yaml`. Flat `.env` profiles are still supported for upgrades.

Skip this step if you already have `.config/<id>.yaml` and no longer rely on `.config/<id>.env`.

If you still have `.config/<id>.env` (replace `mycompany` with your profile id):

```bash
# Preview (may print passwords — keep output local)
python scripts/migrate_profile_yaml.py mycompany --dry-run

# Write .config/mycompany.yaml
python scripts/migrate_profile_yaml.py mycompany

# Overwrite YAML if it already exists
python scripts/migrate_profile_yaml.py mycompany --force
```

Maintainer CLI equivalent (after editable install): `oracle-cpq migrate-yaml mycompany`.

While both `.yaml` and `.env` exist for the same id, **YAML wins**. After a successful smoke test and MCP reload, move the old `.env` aside (for example into `.config/archive/`) and remove any `.catalog.yaml` sidecar.

Field mapping and troubleshooting: [FAQ — How do I migrate from a legacy `.env` to `.yaml`?](FAQ.md#how-do-i-migrate-from-a-legacy-env-to-yaml).

---

## Step 7 — Refresh profile knobs (keep passwords)

Edit `.config/<profile>.yaml` and compare **non-secret** flags to [`.config/example.yaml`](../.config/example.yaml) (or [`.config/example_fusion.yaml`](../.config/example_fusion.yaml) if Fusion-active). Do **not** copy the whole example over a live profile.

| YAML key / legacy env key | Typical default | Purpose |
|---------------------------|-----------------|--------|
| `cpq.hosted` / legacy `cpq_mode` | `standalone` | `standalone` → `/rest/…`; `fusion` → `/cpq/rest/…` |
| `cpq.auth` / `cx.auth` | `basic` | `basic` (credentials) or `bearer` (`oauth_*`) per product |
| `cx.modules` / `fusion_modules` (`CPQ_FUSION_MODULES` host) | blank | CX modules when `cx.enabled`; **Sales**/**PRM** register GET tools; other names reserved |
| `debug_mode` / `DEBUG_MODE` | `true` | Redacted API traces → `logs/{profile}-{env}.log` |
| `refined_prompt` / `REFINED_PROMPT` | `true` | End-of-task refined-prompt footer |
| `auto_save_refined_prompt` / `AUTO_SAVE_REFINED_PROMPT` | `true` in example profile | Auto-save refined prompts |
| `frugal_mode` / `FRUGAL_MODE` (`CPQ_FRUGAL_MODE` host) | `false` | Shorter MCP instructions; forces refined off + `post_response_export=never` (no Prompt Studio ensure) |
| `local_data_policy` / `LOCAL_DATA_POLICY` | `prefer` | Cache vs live CPQ before big lists (`ask` / `prefer` / `never`) — must be a **string**, not `true`/`false` |
| `post_response_export` / `POST_RESPONSE_EXPORT` | `always_excel` | Post-response Excel (`ask` / `never` / `always_excel`) |
| `rest_api_version` / `REST_API_VERSION` | site-specific | Prefer `v19` for metrics / collab / admin / saved searches if v18 404s |

If you have not migrated yet, you can still compare a legacy `.env` to `.config/archive/.env.example` (local archive only) for key names.

---

## Step 8 — Reload MCP in your IDE

New tools and updated **MCP server instructions** load only when the MCP process restarts. Keep your local MCP JSON paths and `CPQ_CUSTOMER_PROFILE` / `CPQ_ENVIRONMENT` unless a release note says otherwise.

| IDE | What to do |
|-----|------------|
| **Antigravity** | Reload / restart the Oracle CPQ MCP server (or restart Antigravity). Config: `.agents/mcp_config.json`. |
| **Cursor** | MCP panel → restart `oracle-cpq` (or fully quit and reopen Cursor). Config: `.cursor/mcp.json`. |
| **VS Code** | Reload window or restart the MCP server entry. Config: `.vscode/mcp.json` (`"servers"` + `"type": "stdio"`). |

Launcher scripts (usually unchanged): [`scripts/mcp-server.cmd`](../scripts/mcp-server.cmd) (Windows) / [`scripts/mcp-server.sh`](../scripts/mcp-server.sh) (macOS/Linux).

**Dual environments:** two server entries with `CPQ_ENVIRONMENT=dev` and `test` — see [`.cursor/mcp.json.dual.example.json`](../.cursor/mcp.json.dual.example.json) / [`.agents/mcp_config.dual.example.json`](../.agents/mcp_config.dual.example.json).

If you use Prompt Studio, restart it after upgrades so UI assets refresh:

```bash
# Stop the old process (Ctrl+C in its terminal), then:
python -m apps.prompt_studio
# Or: scripts/restart-prompt-studio.cmd / .sh
```

Hard-refresh the browser once at [http://127.0.0.1:8765](http://127.0.0.1:8765) so cache-busted JS/CSS load. Version badge should match the Studio version in [RELEASE_NOTES](RELEASE_NOTES.md) / [FEATURES](FEATURES.md).

---

## Step 9 — Verify

**Smoke (IDE terminal, venv active)** — replace `mycompany` with your profile id:

```bash
oracle-cpq-smoke --profile mycompany --env dev
```

**Agent chat** (after MCP shows connected):

- *“Discover CPQ tools and list 5 users.”*
- *“Discover tools for domain admin”* or *“list saved searches”*

Optional: ask for a Word export on an analytical answer to confirm Mermaid (`mmdc`) if you use Word diagrams.

Read the delta: [RELEASE_NOTES.md](RELEASE_NOTES.md) (package version in [`pyproject.toml`](../pyproject.toml)).

---

## Leave alone (local / secrets)

These are gitignored on purpose — upgrades must not wipe them:

- `.config/*.yaml` profiles and credentials
- `.config/archive/`
- Customized `.config/template/` branding (treat as read-only for agents; you maintain it)
- `data/` local CPQ snapshots
- `logs/`
- `.prompts/saved_prompts.json` (and Prompt Studio sidecar data)
- Local MCP JSON: `.agents/mcp_config.json`, `.cursor/mcp.json`, `.vscode/mcp.json`

---

## Troubleshooting

| Symptom | What to run / check |
|---------|---------------------|
| `ModuleNotFoundError: oracle_cpq_mcp` | Venv active + `python -m pip install --prefer-binary -e ".[dev]"` from repo root |
| Stale tools / old instructions after pull | Reinstall editable package, then **restart MCP** (Step 8) |
| Schema integrity / `tool_manifest` startup failure | See [FAQ — Schema integrity](FAQ.md#schema-integrity--startup-hash-errors) and [SECURITY_TESTING.md](../SECURITY_TESTING.md) |
| Wrong Python in MCP | Use `scripts/mcp-server.cmd` / `.sh`; ensure MCP JSON points at this repo’s `.venv` |
| Prompt Studio old UI | Restart Studio + hard-refresh browser; `pip install -e ".[prompt-studio]"` |
| Profile load / `local_data_policy` errors | Use string `ask` \| `prefer` \| `never` — not boolean `true` |

More: [FAQ.md](FAQ.md) · [QUICKSTART troubleshooting](QUICKSTART.md#troubleshooting).
