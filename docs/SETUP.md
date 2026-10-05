# Setup — Quick guide

Eight steps from install to a working MCP connection. For multi-OS shells, dual MCP, field-by-field profiles, and troubleshooting, use the **[Full setup guide](QUICKSTART.md)**.

**Already have an older checkout?** Do not re-run this first-time path — follow **[UPGRADE.md](UPGRADE.md)** (`git pull`, reinstall into the same venv, reload MCP).

```mermaid
flowchart TD
  s1[Step1_Prerequisites]
  s2[Step2_Workspace_and_clone]
  s3[Step3_Activate_venv]
  s4[Step4_pip_dev]
  s5[Step5_Prompt_Studio]
  s6[Step6_Configure_YAML]
  s7[Step7_Connect_IDE_MCP]
  s8[Step8_Test]
  s1 --> s2 --> s3 --> s4 --> s5 --> s6 --> s7 --> s8
  s7 --> antigravity[Antigravity]
  s7 --> cursor[Cursor]
  s7 --> vscode[VS_Code]
```

Open the **IDE integrated terminal** (`` Ctrl+` ``) and run commands from the **repository root** (`pyproject.toml` present).

---

## Step 1 — Prerequisites

Install in this order (each item has a download link):

1. **IDE** — pick one:
   - [Google Antigravity](https://antigravity.google/) (recommended)
   - [Cursor](https://cursor.com/)
   - [VS Code](https://code.visualstudio.com/)
2. **Python 3.11+** — [python.org/downloads](https://www.python.org/downloads/)
3. **Node.js LTS** (includes npm) — [nodejs.org](https://nodejs.org/)
4. **Git** — [git-scm.com/downloads](https://git-scm.com/downloads/)
5. **Mermaid CLI (`mmdc`)** — after Node is installed:

```bash
npm install -g @mermaid-js/mermaid-cli
```

Package page: [npmjs.com/package/@mermaid-js/mermaid-cli](https://www.npmjs.com/package/@mermaid-js/mermaid-cli)

**Verify:**

```bash
python --version
node --version
git --version
mmdc --version
```

Other shells / OS-specific install notes → [Full setup guide](QUICKSTART.md).

---

## Step 2 — Workspace folder, download code, open in IDE

1. Create a workspace directory (example: `C:\Users\YourName\workspaces` or `~/workspaces`).
2. Clone the repo (or download ZIP from GitHub):

```bash
cd ~/workspaces   # or your Windows workspaces path
git clone https://github.com/singhramandeep/oracleCPQMCP.git oracleCPQMCP
cd oracleCPQMCP
```

Repo: [github.com/singhramandeep/oracleCPQMCP](https://github.com/singhramandeep/oracleCPQMCP)

3. In your IDE: **File → Open Folder** → select the `oracleCPQMCP` project root (must contain `pyproject.toml`).

---

## Step 3 — Activate the virtual environment

```bash
python -m venv .venv
```

**Windows PowerShell** (typical IDE terminal on Windows):

```powershell
.venv\Scripts\Activate.ps1
```

If activation is blocked: `Set-ExecutionPolicy -Scope Process Bypass`, then retry. Other shells / macOS / Linux → [Full setup guide](QUICKSTART.md#step-2--create-python-environment-and-install).

---

## Step 4 — Install package (`pip` editable with `.dev`)

```bash
pip install -e ".[dev]"
```

Extras are defined in `pyproject.toml`. Pip troubleshooting → [Full setup guide](QUICKSTART.md#step-2--create-python-environment-and-install).

---

## Step 5 — Install and run Prompt Studio

Prompt Studio is a local UI for saved refined prompts and DEBUG API logs (does **not** call Oracle CPQ). Use the **project venv** from Steps 3–4.

1. **Install** (repo root, venv active):

```bash
pip install -e ".[prompt-studio]"
```

2. **Run** (leave this terminal open while using Studio):

| Shell | Command |
|-------|---------|
| Windows (venv active) | `python -m apps.prompt_studio` |
| Windows without activate | `.\.venv\Scripts\python.exe -m apps.prompt_studio` |
| macOS / Linux (venv active) | `python -m apps.prompt_studio` |
| macOS / Linux without activate | `./.venv/bin/python -m apps.prompt_studio` |

3. **Open** [http://127.0.0.1:8765](http://127.0.0.1:8765) and confirm the header version badge (app **0.4.3+**).
4. **Later:** MCP tool `ensure_prompt_studio` can auto-start Studio when it is down; a manual start once during setup is still recommended. To restart a live process: `python -m apps.prompt_studio restart`, or `.\scripts\restart-prompt-studio.cmd` (Windows) / `./scripts/restart-prompt-studio.sh` (macOS/Linux), then hard-refresh the browser (**Ctrl+F5**).

Deep detail → [Full setup guide — Prompt Studio](QUICKSTART.md#prompt-studio-local-ui-for-saved-prompts) · [FEATURES — enable and run](FEATURES.md#prompt-studio-enable-and-run) · [`apps/prompt_studio/README.md`](../apps/prompt_studio/README.md).

---

## Step 6 — Configure the YAML profile

Copy the template and name it after your customer id:

| Shell | Command |
|-------|---------|
| Windows PowerShell / CMD | `copy .config\example.yaml .config\mycompany.yaml` |
| macOS / Linux / Git Bash | `cp .config/example.yaml .config/mycompany.yaml` |

Edit `.config/mycompany.yaml` — set CPQ URL and credentials under `environments.dev` (you own passwords; never commit this file). The filename without `.yaml` is `CPQ_CUSTOMER_PROFILE`.

Top-level `version` is the profile **format** version (currently **1.06**). Bump it when you copy a newer template so you can tell at a glance whether a customer file is up to date.

**One YAML layout** for both modes (see [`.config/example.yaml`](../.config/example.yaml) and [`.config/example_fusion.yaml`](../.config/example_fusion.yaml)):

- Nested per-environment `cpq:` and/or `cx:` blocks (each with its own `url` and `auth: basic|bearer`)
- Shared flags (`frugal_mode`, `read_only`, `local_data_policy`, …) and catalog sections
- Per product connection:
  - `auth: basic` (default) → `credentials` (username/password)
  - `auth: bearer` → `oauth_token_url` / `oauth_client_id` / `oauth_client_secret` / `oauth_scope`
  - CPQ `hosted: standalone` → `/rest/{version}`; `hosted: fusion` → `/cpq/rest/{version}` (independent of Basic vs Bearer)
  - CX `modules` required when `cx.enabled: true`. **Sales** and **PRM** register product tools; Adaptive Search discovery/suggest registers for any enabled module. Top-level CX `list_*` use Adaptive Search (`searchResources`); `get_*` / children / LOVs use ADF (`resources`). `Service`, `Field Service`, `Subscription`, `Incentive Compensation` are reserved names only.
  - Optional `frugal_mode: true` shortens MCP agent instructions; host override `CPQ_FRUGAL_MODE`
- Legacy flat `environments.dev.url` + `credentials` / `oauth_*` still load (migrated into `cpq:`)

```mermaid
flowchart LR
  yaml[profile_YAML]
  cpqBlk[environments.env.cpq]
  cxBlk[environments.env.cx]
  yaml --> cpqBlk
  yaml --> cxBlk
  cpqBlk --> cpqTools[CPQ_REST_tools]
  cxBlk -->|"any module"| asTools[adaptive_search_tools]
  cxBlk -->|"modules Sales"| sales[sales_tools]
  cxBlk -->|"modules PRM"| prm[prm_tools]
```

**Fusion-hosted CPQ:** copy [`.config/example_fusion.yaml`](../.config/example_fusion.yaml), set `cpq.hosted: fusion` and `cpq.auth: bearer`, and fill oauth fields. Agents must never edit OAuth secrets. `CPQClient` uses `/cpq/rest/{version}` when `hosted: fusion` and Bearer when `auth: bearer` (Basic + `/cpq/rest` is also valid).

Field-by-field tour and `.env` migration → [Full setup guide](QUICKSTART.md#step-3--create-your-cpq-credential-profile) · [FAQ](FAQ.md#how-do-i-migrate-from-a-legacy-env-to-yaml).

---

## Step 7 — Connect the IDE (MCP)

Never put CPQ passwords in MCP JSON — only profile name and paths. Dual env (dev+test) examples → [Full setup guide](QUICKSTART.md#step-5--connect-your-ide--llm-client).

### Rules across IDEs

**Connecting Oracle CPQ MCP is how agents get runtime rules** (refined prompts, exports, document templates, credentials, scratch files, knowledge, aliases). Those instructions are built by `build_server_instructions` and delivered to **Antigravity, Cursor, and VS Code** the same way.

- Do **not** copy [`.cursor/rules/`](../.cursor/rules/) into Antigravity or VS Code — those hosts do not load Cursor `.mdc` files.
- Portable overview: root [`AGENTS.md`](../AGENTS.md). Tool-authoring checklist: [`STANDARDS.md`](STANDARDS.md).
- After changing MCP instruction text or profile flags that feed it, **reload / restart** the Oracle CPQ MCP server in your IDE.

### 7a. Google Antigravity

1. Copy [`.agents/mcp_config.example.json`](../.agents/mcp_config.example.json) → `.agents/mcp_config.json`.
2. Set **absolute** paths for `command`, `cwd`, and `CPQ_CONFIG_DIR`; set `CPQ_CUSTOMER_PROFILE` to your profile id.
3. Required env: `MCP_MODE=stdio`, `DISABLE_CONSOLE_OUTPUT=true`, `CPQ_CUSTOMER_PROFILE`, `CPQ_CONFIG_DIR`.
4. Reload MCP / restart Antigravity. Verify under MCP Servers that `oracle-cpq` is connected.

Docs: [Antigravity](https://antigravity.google/) · [Antigravity MCP](https://antigravity.google/docs/mcp/) · detail: [Full setup guide — Antigravity](QUICKSTART.md#google-antigravity-ide-recommended).

### 7b. Cursor

1. Copy [`.cursor/mcp.json.example`](../.cursor/mcp.json.example) (Windows) or [`.cursor/mcp.json.unix.example`](../.cursor/mcp.json.unix.example) (macOS/Linux) → `.cursor/mcp.json`.
2. Set `CPQ_CUSTOMER_PROFILE` to your profile id.
3. Fully quit and restart Cursor. Check **Settings → MCP** for `oracle-cpq`.

Docs: [Cursor](https://cursor.com/) · detail: [Full setup guide — Cursor](QUICKSTART.md#cursor-needs-testing).

### 7c. VS Code (Copilot Agent)

#### Sign in to GitHub Copilot

1. Install the **GitHub Copilot** and **GitHub Copilot Chat** extensions (Extensions view → search “GitHub Copilot” → Install). Official setup: [VS Code Copilot](https://code.visualstudio.com/docs/copilot/setup).
2. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) → **GitHub Copilot: Sign In** (or use the Accounts menu → Sign in to GitHub).
3. Complete browser OAuth. Confirm the status bar / Copilot icon shows signed in (an active Copilot subscription is required).
4. Open the **Chat** view and select **Agent** mode (required for MCP tools).

#### Connect Oracle CPQ MCP

1. Copy [`.vscode/mcp.json.example`](../.vscode/mcp.json.example) (Windows) or [`.vscode/mcp.json.unix.example`](../.vscode/mcp.json.unix.example) → `.vscode/mcp.json`.
2. VS Code uses `"servers"` (not `mcpServers`) and requires `"type": "stdio"`.
3. Set `CPQ_CUSTOMER_PROFILE`. Reload window (**Developer: Reload Window**). Confirm the MCP server is connected, then use Copilot Chat → **Agent** mode.

Docs: [VS Code](https://code.visualstudio.com/) · detail: [Full setup guide — VS Code](QUICKSTART.md#vs-code-github-copilot-agent-needs-testing).

---

## Step 8 — Test

**Smoke (IDE terminal, venv active):**

```bash
oracle-cpq-smoke --profile mycompany --env dev
```

**Agent chat:** *“Discover CPQ tools and list 5 users.”* If CX is enabled: *“Discover tools with cx_module sales”*, *“List Adaptive Search entities, then list accounts”*, or *“List partners and resolve status codes with list_partner_lov.”*

Failures / DEBUG logs → [Full setup guide](QUICKSTART.md#step-4--smoke-test-verify-cpq-connectivity) · [FAQ](FAQ.md).
