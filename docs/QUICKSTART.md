# Quickstart — Download, Configure, and Connect

Step-by-step guide to clone the Oracle CPQ MCP server, add your CPQ credentials, verify connectivity, and connect an IDE.

**Recommended IDE:** [Google Antigravity](https://antigravity.google/) — instructions below are **partially tested**. Cursor and VS Code setup steps are provided but **still need testing** on this project.

---

## What you need


| Requirement       | Details                                                                                                                                                                                                                                                                                       |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Python            | 3.11 or newer                                                                                                                                                                                                                                                                                 |
| Oracle CPQ access | REST API enabled; integration user with Basic Auth                                                                                                                                                                                                                                            |
| Network           | CPQ site should be publically accessible                                                                                                                                                                                                                                                      |
| IDE               | **Google Antigravity IDE(recommended)**; Cursor or VS Code Copilot Agent also supported The quickstart guide is tested for Antigravity IDE. The tool should work for other supported IDE's too but the quick start guide might not be up to date and instructions might need minor tweaking |
| Git               | Optional but recommended (`git clone`)                                                                                                                                                                                                                                                        |


---



## Step 1 — Get the code



### 1 a Checking the pre-requisties

 **Python:**

Open the terminal and type

```bash
python --version
```

If you get an error that means python is not installed. Install python using [https://www.python.org/downloads/](https://www.python.org/downloads/)

**Git**

Open terminal (powershell for windows) and type git --version. if you get an error that means git is not installed.

Install git using the command 

```bash
winget install --id Git.Git -e --source winget
```

### 1.1 Create a workspace folder

Pick a folder on your machine where you keep projects. Examples:


| OS            | Example path                   |
| ------------- | ------------------------------ |
| Windows       | `C:\Users\YourName\workspaces` |
| macOS / Linux | `~/workspaces`                 |


**IDE terminal** (or any shell) — create the folder if it does not exist:

```bash
mkdir -p ~/workspaces          # macOS / Linux
# Windows PowerShell:
mkdir C:\Users\YourName\workspaces
```

Make a not of this path as you will have to use this path at a number of places

### 1.2 Download the repository

**Option A: Git clone (recommended)**

```bash
cd ~/workspaces                # or cd C:\Users\YourName\workspaces on Windows
git clone https://github.com/singhramandeep/oracleCPQMCP.git oracleCPQMCP
cd oracleCPQMCP
```

**Option B: Download ZIP**

1. Open [https://github.com/singhramandeep/oracleCPQMCP](https://github.com/singhramandeep/oracleCPQMCP)
2. Click **Code → Download ZIP**
3. Extract to `~/workspaces/oracleCPQMCP` (or your chosen folder)
4. In your IDE: **File → Open Folder** → select the `oracleCPQMCP` folder



### 1.3 Open the project in your IDE

**File → Open Folder** → choose the `oracleCPQMCP` folder you just cloned or extracted.

**Recommended:** open the folder in **Google Antigravity**. Cursor and VS Code also work with this repo, but those IDE paths still need testing (see Step 5).

This folder is your **project root** — all commands in later steps run from here.

**Repository layout (key paths):**

```
oracleCPQMCP/                  ← project root (open this folder in your IDE)
├── pyproject.toml             ← Python project file (confirms you are in the right folder)
├── .config/                   ← CPQ credentials (YOU create *.env here)
│   └── .env.example           ← Template (safe to commit)
├── .cursor/
│   ├── mcp.json.example       ← Copy → mcp.json (Windows)
│   └── mcp.json.unix.example  ← Copy → mcp.json (macOS/Linux)
├── scripts/
│   ├── mcp-server.cmd         ← MCP launcher (Windows)
│   └── mcp-server.sh          ← MCP launcher (macOS/Linux)
├── .vscode/
│   ├── mcp.json.example       ← Copy → mcp.json (Windows)
│   └── mcp.json.unix.example  ← Copy → mcp.json (macOS/Linux)
├── .agents/
│   └── mcp_config.example.json  ← Copy for Antigravity (workspace)
├── mcp/oracle_cpq_mcp/        ← MCP server package
└── docs/QUICKSTART.md         ← This file
```

---



## Running commands (IDE terminal)

All setup commands below run in your **IDE integrated terminal** — you do not need a separate PowerShell or Command Prompt window outside the IDE.


| IDE             | Open terminal                 |
| --------------- | ----------------------------- |
| **Cursor**      | `View → Terminal` or `Ctrl+`` |
| **VS Code**     | `View → Terminal` or `Ctrl+`` |
| **Antigravity** | Terminal panel or `Ctrl+``    |


Before each command, confirm you are in the **project root** — the `oracleCPQMCP` folder you opened in Step 1.3. You should see `pyproject.toml` if you list files:

```bash
# macOS / Linux / Git Bash
ls pyproject.toml

# Windows PowerShell
dir pyproject.toml
```

If you are in the wrong folder, change into the project root:

```bash
cd path/to/oracleCPQMCP
```

---



## Step 2 — Create Python environment and install

**IDE terminal** (project root):

```bash
python -m venv .venv
```

This will create a virtual environment for python and will ensure that all the packages are installed in the virtual environment and not at the global system level

Activate the virtual environment:


| Shell (in IDE terminal) | Command                      |
| ----------------------- | ---------------------------- |
| Windows PowerShell      | `.venv\Scripts\Activate.ps1` |
| Windows CMD             | `.venv\Scripts\activate.bat` |
| macOS / Linux           | `source .venv/bin/activate`  |


**Activation note (Windows):** Cursor and VS Code usually open **PowerShell** on Windows. If activation is blocked, run once in the same terminal:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Then retry `.venv\Scripts\Activate.ps1`.

Install the package:

```bash
# 1. Upgrade pip inside the virtual environment
# skip the below step if you just installed python
python -m pip install --upgrade pip
# 2. Install dependencies using --prefer-binary (instructs pip to use available pre-compiled wheels)
#pip install -e ".[dev]"
python -m pip install --prefer-binary -e ".[dev]"
```

---



## Step 3 — Create your CPQ credential profile

Credentials live in **one file per customer**, never in MCP JSON.

### 3.1 Copy the template

**IDE terminal** (project root):


| Shell                    | Command                                           |
| ------------------------ | ------------------------------------------------- |
| Windows PowerShell / CMD | `copy .config\.env.example .config\mycompany.env` |
| macOS / Linux / Git Bash | `cp .config/.env.example .config/mycompany.env`   |


Use any profile id you like (`mycompany`, `acme`, `customer_a`). The filename **without** `.env` becomes `CPQ_CUSTOMER_PROFILE`.

### 3.2 Edit `.config/mycompany.env`

Open the file in the IDE editor and set at minimum:

```env
CUSTOMER_NAME=My Company
DEV_URL=https://your-site-dev.bigmachines.com
TEST_URL=https://your-site-test.bigmachines.com
# PROD_URL=https://your-site.bigmachines.com

DEV_USERNAME=your_integration_user
DEV_PASSWORD=your_dev_password

TEST_USERNAME=your_integration_user
TEST_PASSWORD=your_test_password

DEFAULT_ENVIRONMENT=dev
REST_API_VERSION=v18
READ_ONLY=true
COMPANY_LOGIN_NAME=_host

CUSTOM_DATA_TABLE_NAME=YourDefaultTable
```


| Field                           | What to put                                                                    |
| ------------------------------- | ------------------------------------------------------------------------------ |
| `DEV_URL`                       | CPQ dev base URL — **no trailing slash**                                       |
| `DEV_USERNAME` / `DEV_PASSWORD` | Integration user for dev                                                       |
| `REST_API_VERSION`              | Match your CPQ release (`v15`, `v18`, …)                                       |
| `READ_ONLY`                     | Keep `true` until you intentionally enable writes                              |
| `CUSTOM_DATA_TABLE_NAME`        | A table that exists in dev (for smoke test)                                    |
| `COMMERCE_PROCESS_VAR_NAME`     | Commerce process on your site (for commerce metadata tools; e.g. `oraclecpqo`) |


**Do not commit this file.** It is gitignored.

### 3.3 Optional: multiple customers

Create separate files, for example:

- `.config/mycompany.env`
- `.config/acme.env`

Switch at runtime with `CPQ_CUSTOMER_PROFILE=mycompany` in MCP config.

---



## Step 4 — Smoke test (verify CPQ connectivity)

**IDE terminal** (project root, venv activated):

```bash
oracle-cpq-smoke --profile mycompany --env dev
```

Make sure you replace mycompany witha actual profile you have created

**Expected output:**

- `Profile loaded`
- `Connected in READ-ONLY mode — ...` (if `READ_ONLY=true`)
- Table rows showing **PASS** for:
  - List users
  - List groups
  - List data tables
  - Get table (your `CUSTOM_DATA_TABLE_NAME`)

**If smoke test fails:**


| Symptom                     | Fix                                                    |
| --------------------------- | ------------------------------------------------------ |
| `401 UNAUTHORIZED`          | Check `DEV_USERNAME` / `DEV_PASSWORD`                  |
| `FileNotFoundError` profile | Wrong `--profile` name or missing `.config/<name>.env` |
| Network error               | VPN, URL typo, or CPQ site down                        |
| Table check fails           | Fix `CUSTOM_DATA_TABLE_NAME` spelling                  |


---

If smoke test was successful that means the MCP server standalone test is working. The next steps will configure the MCP in your IDE

## Step 5 — Connect your IDE / LLM client

Each client uses **stdio**: MCP runs `[scripts/mcp-server.cmd](../scripts/mcp-server.cmd)` (Windows) or `[scripts/mcp-server.sh](../scripts/mcp-server.sh)` (macOS/Linux), which starts `python -m oracle_cpq_mcp` from your local `.venv`.  
**Never put CPQ passwords in MCP config** — only profile name and paths.

Set these env vars in MCP config (all clients):


| Variable               | Example          | Purpose                                |
| ---------------------- | ---------------- | -------------------------------------- |
| `CPQ_CUSTOMER_PROFILE` | `mycompany`      | Matches `.config/mycompany.env`        |
| `CPQ_CONFIG_DIR`       | `<repo>/.config` | Folder containing profile `.env` files |




### IDE support status


| IDE                         | Status                             | Notes                                                                                                        |
| --------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Google Antigravity**      | **Recommended** — partially tested | Preferred path for this project. Setup steps below have been exercised in part; report gaps if you hit them. |
| **Cursor**                  | Needs testing                      | Config examples included; end-to-end MCP connect on this repo is not fully validated yet.                    |
| **VS Code (Copilot Agent)** | Needs testing                      | Config examples included; end-to-end MCP connect on this repo is not fully validated yet.                    |


---



## Google Antigravity IDE (recommended)

Use [Google Antigravity](https://antigravity.google/) as the primary client for Oracle CPQ MCP.

**Testing note:** These Antigravity instructions are **partially tested**. Cursor and VS Code instructions in the sections after this one **need testing**.

Antigravity supports:

- **Workspace config** (recommended): `.agents/mcp_config.json` — keeps CPQ setup per project
- **Global config** (optional): `~/.gemini/config/mcp_config.json`



### A.1 Copy the example config

**IDE terminal** (project root):


| Shell                    | Command                                                                              |
| ------------------------ | ------------------------------------------------------------------------------------ |
| Windows PowerShell       | `mkdir .agents -Force; copy .agents\mcp_config.example.json .agents\mcp_config.json` |
| Windows CMD              | `mkdir .agents && copy .agents\mcp_config.example.json .agents\mcp_config.json`      |
| macOS / Linux / Git Bash | `mkdir -p .agents && cp .agents/mcp_config.example.json .agents/mcp_config.json`     |


On macOS/Linux, make the launcher executable once:

```bash
chmod +x scripts/mcp-server.sh
```



### A.2 Edit absolute paths and profile

Antigravity requires **absolute paths** (not `${workspaceFolder}`). Edit `.agents/mcp_config.json`:

```json
{
  "mcpServers": {
    "oracle-cpq": {
      "command": "C:\\Users\\YourName\\workspaces\\oracleCPQMCP\\scripts\\mcp-server.cmd",
      "args": [],
      "cwd": "C:\\Users\\YourName\\workspaces\\oracleCPQMCP",
      "env": {
        "MCP_MODE": "stdio",
        "DISABLE_CONSOLE_OUTPUT": "true",
        "CPQ_CUSTOMER_PROFILE": "mycompany",
        "CPQ_CONFIG_DIR": "C:\\Users\\YourName\\workspaces\\oracleCPQMCP\\.config",
        "CPQ_SCHEMA_INTEGRITY": "1"
      }
    }
  }
}
```

Replace `C:\\Users\\YourName\\workspaces\\oracleCPQMCP` with your real project path. Set `CPQ_CUSTOMER_PROFILE` to your profile id (the `.config/<name>.env` filename without `.env`).

On macOS/Linux use the absolute path to `scripts/mcp-server.sh` instead of `.cmd`.


| Antigravity env var      | Required? | Purpose                                     |
| ------------------------ | --------- | ------------------------------------------- |
| `MCP_MODE`               | **Yes**   | `stdio` transport                           |
| `DISABLE_CONSOLE_OUTPUT` | **Yes**   | Prevents stdout pollution breaking JSON-RPC |
| `CPQ_CUSTOMER_PROFILE`   | **Yes**   | Selects `.config/<profile>.env`             |
| `CPQ_CONFIG_DIR`         | **Yes**   | Absolute path to the `.config` folder       |




### A.3 Connect and verify in Antigravity

1. Open the `oracleCPQMCP` folder in Antigravity (**File → Open Folder**).
2. Ensure Steps 2–4 are done (venv installed, profile created, smoke test passed).
3. Agent panel → **…** → **MCP Servers** → **Manage MCP Servers** → **View raw config** (or edit `.agents/mcp_config.json` directly).
4. Confirm absolute paths and profile name are correct.
5. Restart Antigravity or reload MCP servers.
6. Open Agent chat and ask: *"Discover CPQ tools and list 5 users."*

**Verify:** MCP Servers UI should list `oracle-cpq` as connected with tools available.

Official docs: [Antigravity MCP](https://antigravity.google/docs/mcp/)

---



## Other IDEs (need testing)

The following clients are supported by example configs in this repo, but **setup has not been fully tested** for this project. Prefer **Antigravity** above when possible.

### Cursor (needs testing)

**Config file:** `.cursor/mcp.json` — **you create this locally** (not committed). Use the cross-platform launcher scripts so the same repo works on every OS.

**IDE terminal** (project root) — copy the example for your OS:


| Shell                    | Command                                             |
| ------------------------ | --------------------------------------------------- |
| Windows PowerShell / CMD | `copy .cursor\mcp.json.example .cursor\mcp.json`    |
| macOS / Linux / Git Bash | `cp .cursor/mcp.json.unix.example .cursor/mcp.json` |


On macOS/Linux, make the launcher executable once:

```bash
chmod +x scripts/mcp-server.sh
```

Example `.cursor/mcp.json` (Windows — uses `mcp-server.cmd`):

```json
{
  "mcpServers": {
    "oracle-cpq": {
      "command": "${workspaceFolder}/scripts/mcp-server.cmd",
      "args": [],
      "cwd": "${workspaceFolder}",
      "env": {
        "CPQ_CUSTOMER_PROFILE": "mycompany",
        "CPQ_CONFIG_DIR": "${workspaceFolder}/.config"
      }
    }
  }
}
```

**macOS/Linux** — use `mcp-server.sh` in `command` (see `[.cursor/mcp.json.unix.example](../.cursor/mcp.json.unix.example)`).

**Steps:**

1. Open the `oracleCPQMCP` folder in Cursor (File → Open Folder).
2. Copy the example MCP config (above) to `.cursor/mcp.json`.
3. Edit `.cursor/mcp.json` — set `CPQ_CUSTOMER_PROFILE` to your profile id.
4. Ensure `.venv` exists (Step 2, run in IDE terminal).
5. **Fully quit and restart Cursor** (MCP loads at startup).
6. Open **Agent** mode chat.
7. Ask: *"What can you do in Oracle CPQ? Use discover_tools to list tools by domain (users, groups, datatables, bml, commerce, performance, parts, tasks, configuration)."*

**Verify in Cursor:** Settings → MCP — `oracle-cpq` should show connected with tools listed.

---



### VS Code (GitHub Copilot Agent) (needs testing)

VS Code uses `**servers**` (not `mcpServers`) and requires `"type": "stdio"`.

**Config file:** copy example → local (local file is gitignored).

**IDE terminal** (project root):


| Shell                    | Command                                             |
| ------------------------ | --------------------------------------------------- |
| Windows PowerShell / CMD | `copy .vscode\mcp.json.example .vscode\mcp.json`    |
| macOS / Linux / Git Bash | `cp .vscode/mcp.json.unix.example .vscode/mcp.json` |


On macOS/Linux: `chmod +x scripts/mcp-server.sh`

The example files use `scripts/mcp-server.cmd` (Windows) or `scripts/mcp-server.sh` (Unix) — no hardcoded `.venv/.../python` path.

Edit `.vscode/mcp.json` if needed (profile name, env vars). Example shape:

```json
{
  "servers": {
    "oracle-cpq": {
      "type": "stdio",
      "command": "${workspaceFolder}/scripts/mcp-server.cmd",
      "args": [],
      "cwd": "${workspaceFolder}",
      "env": {
        "CPQ_CUSTOMER_PROFILE": "mycompany",
        "CPQ_CONFIG_DIR": "${workspaceFolder}/.config",
        "CPQ_SCHEMA_INTEGRITY": "1"
      }
    }
  }
}
```

**Steps:**

1. Install [VS Code](https://code.visualstudio.com/) and enable **GitHub Copilot** with Agent mode.
2. Open the `oracleCPQMCP` folder.
3. Select the workspace Python interpreter: `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (Command Palette → *Python: Select Interpreter*).
4. Create `.vscode/mcp.json` from the example (above).
5. Reload VS Code (Command Palette → *Developer: Reload Window*).
6. Open Copilot Chat → switch to **Agent** mode.
7. Ask: *"Show me the first 5 active CPQ users."*

**Alternative:** Command Palette → **MCP: Open Workspace Folder Configuration** to edit the file in UI.

---



## Step 6 — Sample checks in Agent chat

After MCP is connected (preferably in **Antigravity**), paste these prompts into **Agent mode**. You do not need to name CPQ tools or API parameters — the agent will choose the right MCP tools for you. When profile `REFINED_PROMPT` is not `false` (default **true**), every CPQ-related answer (live tools and/or local `data/` cache) should end with **`### Refined prompt (Better token usage)`**: **Title**, **Tags**, **Output format** (chat text / json / excel download; default chat text), **Cached data** (yes/no/mixed), a generic prose prompt with `{{placeholders}}` (including `{{output_format}}`), a **Variables** legend, then a **Tools (for the agent)** list (or `none (local file read only)`).

**Saving refined prompts (MCP tools — do not invent scripts):**
- `AUTO_SAVE_REFINED_PROMPT=false` (default): agent calls `offer_save_refined_prompt` — choose **save once**, **save and always**, or **skip**. “Save and always” writes `AUTO_SAVE_REFINED_PROMPT=true` into the active `.config/<profile>.env` via `set_auto_save_refined_prompt`.
- `AUTO_SAVE_REFINED_PROMPT=true`: agent calls `save_refined_prompt` after every footer (no ask; dedupes by hash).
- Library file: `.config/saved_prompts.json` (gitignored). Override path with `CPQ_SAVED_PROMPTS_PATH`.

**Picking a saved prompt instead of typing:** type **`/OracleCPQ_SavedPrompts`** in Agent chat (or say **use a saved prompt**). The agent calls `start_prompt_picker`: **all titles** / **search** / **by tag** / **by tool**. Disabled prompts are hidden; toggle with `set_saved_prompt_enabled`. Or use the MCP prompt `run_saved_prompt` if your host shows MCP Prompts. **Reload the Oracle CPQ MCP server** after pulling these tools so they appear in the tool list.

**Local data cache (`data/`):** full users/groups/BML/commerce attrs/datatables syncs persist under `data/{profile}/{env}/`. With `LOCAL_DATA_POLICY=ask` (default), the agent checks `list_local_data` / `offer_use_local_data` when a snapshot exists. Say **use cached data** or **fresh data** any time; set `prefer` / `never` via `set_local_data_policy` (or `CPQ_LOCAL_DATA_POLICY`).

Set `REFINED_PROMPT=false` to disable the footer.

### Prompt Studio (local UI for saved prompts)

Browse, favorite, suite, and fill `{{placeholders}}` from `.config/saved_prompts.json` without calling CPQ.

1. Install optional deps (project venv):

```powershell
.\.venv\Scripts\python.exe -m pip install '.[prompt-studio]'
```

2. Run from repo root:

```powershell
.\.venv\Scripts\python.exe -m apps.prompt_studio
```

3. Open [http://127.0.0.1:8765](http://127.0.0.1:8765) (localhost only; no auth in v1).

4. After the agent saves a refined prompt in Cursor, click **Refresh** in Prompt Studio.

Full detail: [`apps/prompt_studio/README.md`](../apps/prompt_studio/README.md) and [`docs/FEATURES.md`](FEATURES.md#prompt-studio-enable-and-run).

### 6.1 Explore what CPQ actions are available

> What can you do in Oracle CPQ? Use discover_tools to list the read-only actions you have access to, grouped by domain (users, groups, datatables, bml, commerce, performance, parts, tasks, configuration).

Note: **tasks** and **configuration** (productFamilies), plus newer datatable create/export and BML extension tools, are implemented but **untested against live CPQ** — see the testing-status table in [README.md](../README.md).



### 6.2 List active users

> Show me the first 5 active CPQ users. I only need their login names for now.



### 6.3 Look up one user in detail

> From that user list, pick one person and show me their full CPQ profile — login, name, email, and status.



### 6.4 List groups

> List the first 5 user groups in CPQ. Include each group's name and description if available.



### 6.5 Data table metadata

> Tell me about the data table called `PricingMatrix` in CPQ — what columns does it have and how many rows?

*(Replace* `PricingMatrix` *with the value of* `CUSTOM_DATA_TABLE_NAME` *in your profile if different.)*

### 6.6 Export users to Excel (optional)

> Export all active CPQ users to an Excel spreadsheet I can download.

You should receive a summary in chat plus an Excel file attachment in clients that support MCP resources.

### 6.7 Safe write check — preview only (no changes)

With `READ_ONLY=true` (default), this validates the workflow without changing anything in CPQ:

> I want to change the first name of user `<login or party id>` to "Test" in CPQ. **Do not apply the change yet** — show me exactly what would be updated and ask for my approval first.

Expected: the agent runs a preflight/dry-run, explains the proposed change, and does **not** modify CPQ data.

### 6.8 BML export (optional, admin)

Requires admin permissions on the CPQ site. The agent downloads the full Commerce BML/BMLT site export as a zip file.

> Download all Commerce BML and BMLT source code from CPQ as a zip file I can save locally.



### 6.9 Commerce metadata (optional)

Requires `COMMERCE_PROCESS_VAR_NAME` in your profile to match a real Commerce process on the site (e.g. `oraclecpqo`). Admin or read access to Commerce metadata may be required.

> List the header document attributes for the default Commerce transaction document in CPQ. Show attribute names and types only — no need for full translation text.

### 6.10 Tasks / async exports (**untested** live)

New tools: `export_datatables` / `export_bml_library_functions` → `get_task` → `download_task_file`. Covered by offline tests only; **not yet verified on a live CPQ site**.

> (When ready to smoke-test) Start a data table export dry-run for a known table, then explain how you would poll the task and download the file — do not apply the write unless READ_ONLY is false and I confirm.

### 6.11 Configuration / productFamilies (**untested** live)

New `configuration` domain (`list_product_families`, scoped attributes/array sets/layouts, `get_layout_cache_attributes`). Covered by offline tests only; **not yet verified on a live CPQ site**.

> (When ready to smoke-test) List product families, then list configuration attributes for the first family using scope=family.

---



## Step 7 — Enabling writes (optional, advanced)

Only when you need create/update/deploy in dev:

1. Set `READ_ONLY=false` in `.config/mycompany.env`.
2. Add to MCP config `env` (host env, not profile file):
  ```json
   "CPQ_CONFIRMATION_SECRET": "<long-random-string>"
  ```
3. Restart IDE.
4. Always: preflight (`dry_run=true`) → user approval → execute with `dry_run=false` + `confirmation_token`.

See [SECURITY.md](../SECURITY.md) and [README.md](../README.md#safe-execution).

---



## Troubleshooting


| Problem                               | Solution                                                                                                                               |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| MCP server not listed                 | Restart IDE completely after config change                                                                                             |
| `ModuleNotFoundError: oracle_cpq_mcp` | In IDE terminal: `pip install -e ".[dev]"` with venv active                                                                            |
| Wrong Python in MCP                   | Use launcher scripts: `scripts/mcp-server.cmd` (Windows) or `scripts/mcp-server.sh` (macOS/Linux); run `pip install -e ".[dev]"` first |
| Tools return `UNAUTHORIZED`           | Fix credentials in `.config/<profile>.env`                                                                                             |
| Antigravity JSON parse error          | Add `MCP_MODE=stdio` and `DISABLE_CONSOLE_OUTPUT=true`                                                                                 |
| Schema integrity startup failure      | Run manifest update (see [SECURITY_TESTING.md](../SECURITY_TESTING.md))                                                                |
| Stale tools after code change         | IDE terminal: `pip install -e ".[dev]"` then restart IDE                                                                               |


---



## Before you commit (git safety checklist)

If you fork or contribute changes, confirm these rules **before** `git add`. For a full pre-commit review (secrets, catalog regen, tests, Prompt Studio), see **[`PRE_COMMIT_REVIEW.md`](PRE_COMMIT_REVIEW.md)**.


| Path                                             | Commit?                          | Why                                   |
| ------------------------------------------------ | -------------------------------- | ------------------------------------- |
| `.config/.env.example`                           | Yes                              | Template only — placeholder passwords |
| `.config/mycompany.env` (or any `*.env` profile) | **Never**                        | Contains real CPQ passwords           |
| `.config/saved_prompts.json`                     | **Never**                        | Local refined-prompt library          |
| `.config/prompt_studio.json`                     | **Never**                        | Prompt Studio favorites/suites        |
| `data/`, `dat/`                                  | **Never**                        | Local CPQ snapshots                   |
| `.cursor/mcp.json`                               | **Never** (copy from `.example`) | Local MCP config — profile name only  |
| `.vscode/mcp.json`                               | **Never** (use `.example`)       | May get local secrets later           |
| `.agents/mcp_config.json`                        | **Never** (use `.example`)       | Antigravity local config              |
| `.venv/`                                         | Never                            | Recreate with `pip install`           |
| `exports/`, `*.xlsx`                             | Never                            | Generated downloads                   |
| `apps/prompt_studio/`                            | Yes                              | Prompt Studio source                  |
| `docs/TOOL_CATALOG.md`, `docs/FEATURES.md`       | Yes                              | Catalog + product docs                |


**IDE terminal** (project root) — verify ignore rules:

```bash
git check-ignore -v .config/mycompany.env .config/saved_prompts.json data/focalpoint
# Expected: matched by .gitignore

git status
# mycompany.env and other *.env profiles must NOT appear as tracked files
```

The repo `[.gitignore](../.gitignore)` blocks `.config/*.env`, saved prompts, Prompt Studio sidecar, `data/`, `.venv/`, exports, and local MCP override files.

---



## Next steps

- [README.md](../README.md) — tool catalog, pagination, configuration reference
- [SECURITY.md](../SECURITY.md) — guardrails and confirmation tokens
- [docs/SETUP.md](SETUP.md) — short setup summary

