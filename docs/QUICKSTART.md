# Quickstart — Download, Configure, and Connect

Step-by-step guide to clone the Oracle CPQ MCP server, add your CPQ credentials, verify connectivity, and connect **Cursor**, **VS Code**, or **Google Antigravity**.

---

## Running commands (IDE terminal)

All setup commands below are meant to run in your **IDE integrated terminal** — you do not need a separate PowerShell or Command Prompt window outside the IDE.


| IDE             | Open terminal                 |
| --------------- | ----------------------------- |
| **Cursor**      | `View → Terminal` or `Ctrl+`` |
| **VS Code**     | `View → Terminal` or `Ctrl+`` |
| **Antigravity** | Terminal panel or `Ctrl+``    |


Before running commands, confirm the terminal cwd is the **repository root** (the folder that contains `pyproject.toml`). If not:

```bash
cd path/to/oracleCPQMCP
```

**Activation note (Windows):** Cursor and VS Code usually open **PowerShell** on Windows. If activation is blocked, run once in the same terminal:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

Then retry `.venv\Scripts\Activate.ps1`.

---

## Before you commit (git safety checklist)

If you are initializing git for the first time, confirm these rules **before** `git add`:


| Path                                             | Commit?                    | Why                                   |
| ------------------------------------------------ | -------------------------- | ------------------------------------- |
| `.config/.env.example`                           | Yes                        | Template only — placeholder passwords |
| `.config/mycompany.env` (or any `*.env` profile) | **Never**                  | Contains real CPQ passwords           |
| `.cursor/mcp.json`                               | **Never** (copy from `.example`) | Local MCP config — profile name only |
| `.vscode/mcp.json`                               | **Never** (use `.example`) | May get local secrets later           |
| `.agents/mcp_config.json`                        | **Never** (use `.example`) | Antigravity local config              |
| `.venv/`                                         | Never                      | Recreate with `pip install`           |
| `exports/`, `*.xlsx`                             | Never                      | Generated downloads                   |


**IDE terminal** (repo root) — verify ignore rules:

```bash
git check-ignore -v .config/mycompany.env
# Expected: .gitignore:... .config/*.env

git status
# mycompany.env and other *.env profiles must NOT appear as tracked files
```

The repo `[.gitignore](../.gitignore)` blocks `.config/*.env`, `.venv/`, exports, and local MCP override files.

---

## What you need


| Requirement       | Details                                                |
| ----------------- | ------------------------------------------------------ |
| Python            | 3.11 or newer                                          |
| Oracle CPQ access | REST API enabled; integration user with Basic Auth     |
| Network           | VPN if your CPQ site requires it                       |
| IDE               | Cursor, VS Code (Copilot Agent), or Google Antigravity |


---

## Step 1 — Download the repository

### Option A: Git clone

**IDE terminal** (or any shell):

```bash
cd ~/workspaces          # or C:\Users\YourName\workspaces on Windows
git clone <your-repo-url> oracleCPQMCP
cd oracleCPQMCP
```

### Option B: Download ZIP

1. Download the repository ZIP from your Git host.
2. Extract to a folder (e.g. `~/workspaces/oracleCPQMCP`).
3. In your IDE: **File → Open Folder** → select `oracleCPQMCP`.

**Repository layout (key paths):**

```
oracleCPQMCP/
├── .config/                 ← CPQ credentials (YOU create *.env here)
│   └── .env.example         ← Template (safe to commit)
├── .cursor/
│   ├── mcp.json.example         ← Copy → mcp.json (Windows)
│   └── mcp.json.unix.example  ← Copy → mcp.json (macOS/Linux)
├── scripts/
│   ├── mcp-server.cmd       ← MCP launcher (Windows)
│   └── mcp-server.sh        ← MCP launcher (macOS/Linux)
├── .vscode/
│   ├── mcp.json.example         ← Copy → mcp.json (Windows)
│   └── mcp.json.unix.example  ← Copy → mcp.json (macOS/Linux)
├── .agents/
│   └── mcp_config.example.json  ← Copy for Antigravity (workspace)
├── mcp/oracle_cpq_mcp/      ← MCP server package
├── docs/QUICKSTART.md       ← This file
└── pyproject.toml
```

---

## Step 2 — Create Python environment and install

**IDE terminal** (repo root):

```bash
python -m venv .venv
```

Activate the virtual environment:


| Shell (in IDE terminal) | Command |
| ----------------------- | ------- |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows CMD | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |


Install the package:

```bash
pip install -e ".[dev]"
```

Confirm the package installed:

```bash
python -m oracle_cpq_mcp --help
# Or:
python -c "import oracle_cpq_mcp; print('OK')"
```

---

## Step 3 — Create your CPQ credential profile

Credentials live in **one file per customer**, never in MCP JSON.

### 3.1 Copy the template

**IDE terminal** (repo root):


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


| Field                           | What to put                                       |
| ------------------------------- | ------------------------------------------------- |
| `DEV_URL`                       | CPQ dev base URL — **no trailing slash**          |
| `DEV_USERNAME` / `DEV_PASSWORD` | Integration user for dev                          |
| `REST_API_VERSION`              | Match your CPQ release (`v15`, `v18`, …)          |
| `READ_ONLY`                     | Keep `true` until you intentionally enable writes |
| `CUSTOM_DATA_TABLE_NAME`        | A table that exists in dev (for smoke test)       |
| `COMMERCE_PROCESS_VAR_NAME`     | Commerce process on your site (for commerce metadata tools; e.g. `oraclecpqo`) |


**Do not commit this file.** It is gitignored.

### 3.3 Optional: multiple customers

Create separate files, for example:

- `.config/mycompany.env`
- `.config/acme.env`

Switch at runtime with `CPQ_CUSTOMER_PROFILE=mycompany` in MCP config.

---

## Step 4 — Smoke test (verify CPQ connectivity)

**IDE terminal** (repo root, venv activated):

```bash
oracle-cpq-smoke --profile mycompany --env dev
```

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

## Step 5 — Connect your IDE / LLM client

Each client uses **stdio**: MCP runs [`scripts/mcp-server.cmd`](../scripts/mcp-server.cmd) (Windows) or [`scripts/mcp-server.sh`](../scripts/mcp-server.sh) (macOS/Linux), which starts `python -m oracle_cpq_mcp` from your local `.venv`.  
**Never put CPQ passwords in MCP config** — only profile name and paths.

Set these env vars in MCP config (all clients):


| Variable               | Example          | Purpose                                |
| ---------------------- | ---------------- | -------------------------------------- |
| `CPQ_CUSTOMER_PROFILE` | `mycompany`      | Matches `.config/mycompany.env`        |
| `CPQ_CONFIG_DIR`       | `<repo>/.config` | Folder containing profile `.env` files |


---

### Cursor

**Config file:** `.cursor/mcp.json` — **you create this locally** (not committed). Use the cross-platform launcher scripts so the same repo works on every OS.

**IDE terminal** (repo root) — copy the example for your OS:

| Shell | Command |
| ----- | ------- |
| Windows PowerShell / CMD | `copy .cursor\mcp.json.example .cursor\mcp.json` |
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

**macOS/Linux** — use `mcp-server.sh` in `command` (see [`.cursor/mcp.json.unix.example`](../.cursor/mcp.json.unix.example)).

**Steps:**

1. Open the `oracleCPQMCP` folder in Cursor (File → Open Folder).
2. Copy the example MCP config (above) to `.cursor/mcp.json`.
3. Edit `.cursor/mcp.json` — set `CPQ_CUSTOMER_PROFILE` to your profile id.
4. Ensure `.venv` exists (Step 2, run in IDE terminal).
5. **Fully quit and restart Cursor** (MCP loads at startup).
6. Open **Agent** mode chat.
7. Ask: *"What can you do in Oracle CPQ for users, groups, data tables, BML, and commerce metadata?"*

**Verify in Cursor:** Settings → MCP — `oracle-cpq` should show connected with tools listed.

---

### VS Code (GitHub Copilot Agent)

VS Code uses `**servers**` (not `mcpServers`) and requires `"type": "stdio"`.

**Config file:** copy example → local (local file is gitignored).

**IDE terminal** (repo root):

| Shell | Command |
| ----- | ------- |
| Windows PowerShell / CMD | `copy .vscode\mcp.json.example .vscode\mcp.json` |
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

### Google Antigravity

Antigravity supports workspace-level config at `.agents/mcp_config.json` or global `~/.gemini/config/mcp_config.json`.

**Recommended:** workspace config (keeps CPQ setup per project).

**IDE terminal** (repo root):


| Shell                    | Command                                                                              |
| ------------------------ | ------------------------------------------------------------------------------------ |
| Windows PowerShell       | `mkdir .agents -Force; copy .agents\mcp_config.example.json .agents\mcp_config.json` |
| Windows CMD              | `mkdir .agents && copy .agents\mcp_config.example.json .agents\mcp_config.json`      |
| macOS / Linux / Git Bash | `mkdir -p .agents && cp .agents/mcp_config.example.json .agents/mcp_config.json`     |


Edit `.agents/mcp_config.json` — use **absolute paths** (Antigravity requires them):

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

On macOS/Linux use absolute path to `scripts/mcp-server.sh` instead of `.cmd`.


| Antigravity env var      | Required? | Purpose                                     |
| ------------------------ | --------- | ------------------------------------------- |
| `MCP_MODE`               | **Yes**   | `stdio` transport                           |
| `DISABLE_CONSOLE_OUTPUT` | **Yes**   | Prevents stdout pollution breaking JSON-RPC |


**Steps:**

1. Open the repo folder in Antigravity.
2. Agent panel → **…** → **MCP Servers** → **Manage MCP Servers** → **View raw config** (or edit `.agents/mcp_config.json` directly).
3. Paste/adjust config with your absolute paths.
4. Restart Antigravity or reload MCP servers.
5. In Agent chat: *"Discover CPQ tools and list 5 users."*

Docs: [Antigravity MCP](https://antigravity.google/docs/mcp/)

---

## Step 6 — Sample checks in Agent chat

After MCP is connected, paste these prompts into **Agent mode**. You do not need to name CPQ tools or API parameters — the agent will choose the right MCP tools for you.

### 6.1 Explore what CPQ actions are available

> What can you do in Oracle CPQ for users, groups, data tables, BML, and commerce metadata? Use discover_tools to list the read-only actions you have access to, grouped by domain.

### 6.2 List active users

> Show me the first 5 active CPQ users. I only need their login names for now.

### 6.3 Look up one user in detail

> From that user list, pick one person and show me their full CPQ profile — login, name, email, and status.

### 6.4 List groups

> List the first 5 user groups in CPQ. Include each group's name and description if available.

### 6.5 Data table metadata

> Tell me about the data table called `PricingMatrix` in CPQ — what columns does it have and how many rows?

*(Replace `PricingMatrix` with the value of `CUSTOM_DATA_TABLE_NAME` in your profile if different.)*

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


| Problem                               | Solution                                                                                    |
| ------------------------------------- | ------------------------------------------------------------------------------------------- |
| MCP server not listed                 | Restart IDE completely after config change                                                  |
| `ModuleNotFoundError: oracle_cpq_mcp` | In IDE terminal: `pip install -e ".[dev]"` with venv active                                 |
| Wrong Python in MCP                   | Use launcher scripts: `scripts/mcp-server.cmd` (Windows) or `scripts/mcp-server.sh` (macOS/Linux); run `pip install -e ".[dev]"` first |
| Tools return `UNAUTHORIZED`           | Fix credentials in `.config/<profile>.env`                                                  |
| Antigravity JSON parse error          | Add `MCP_MODE=stdio` and `DISABLE_CONSOLE_OUTPUT=true`                                      |
| Schema integrity startup failure      | Run manifest update (see [SECURITY_TESTING.md](../SECURITY_TESTING.md))                     |
| Stale tools after code change         | IDE terminal: `pip install -e ".[dev]"` then restart IDE                                    |


---

## Next steps

- [README.md](../README.md) — tool catalog, pagination, configuration reference
- [SECURITY.md](../SECURITY.md) — guardrails and confirmation tokens
- [docs/SETUP.md](SETUP.md) — short setup summary

