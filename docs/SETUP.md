# Setup — Short summary

For the **full step-by-step guide** (download, credentials, Cursor / VS Code / Antigravity, sample checks), see **[QUICKSTART.md](QUICKSTART.md)**.

Open the **IDE integrated terminal** first (`View → Terminal` or `` Ctrl+` ``) and run all commands from the **repository root**.

## Install

**IDE terminal** (repo root):

```bash
python -m venv .venv
```

Activate:

| Shell | Command |
|-------|---------|
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows CMD | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

Then:

```bash
pip install -e ".[dev]"
```

### Optional — Mermaid CLI (Word diagrams)

Word exports with Mermaid need local `mmdc` (Node.js / npm):

```bash
npm i -g @mermaid-js/mermaid-cli
mmdc --version
```

Without `mmdc`, Word still builds but diagrams appear as raw Mermaid text. Details: [QUICKSTART — Step 2.1](QUICKSTART.md#21-optional--mermaid-cli-for-word-diagrams).

### Optional — Prompt Studio

```bash
pip install -e ".[prompt-studio]"
python -m apps.prompt_studio            # start → http://127.0.0.1:8765
python -m apps.prompt_studio restart    # stop + start (one command)
```

Or: `.\scripts\restart-prompt-studio.cmd` / `./scripts/restart-prompt-studio.sh`. See [QUICKSTART — Restart Prompt Studio](QUICKSTART.md#restart-prompt-studio-one-command).

## Configure

**Preferred — unified YAML** (IDE terminal, repo root):

| Shell | Command |
|-------|---------|
| Windows PowerShell / CMD | `copy .config\.profile.yaml.example .config\mycompany.yaml` |
| macOS / Linux / Git Bash | `cp .config/.profile.yaml.example .config/mycompany.yaml` |

Edit `.config/mycompany.yaml` with your CPQ URLs and credentials.

**Migrate an existing `.env`:**

```bash
python scripts/migrate_profile_yaml.py mycompany --dry-run
python scripts/migrate_profile_yaml.py mycompany
```

Detailed steps: [FAQ — migrate `.env` → `.yaml`](FAQ.md#how-do-i-migrate-from-a-legacy-env-to-yaml). Legacy `.env` profiles still work if no `.yaml` exists for that id.

## Verify

**IDE terminal** (venv activated):

```bash
oracle-cpq-smoke --profile mycompany --env dev
```

## Connect IDE

| IDE | Config |
|-----|--------|
| Cursor | Edit [`.cursor/mcp.json`](../.cursor/mcp.json) |
| VS Code | Copy [`.vscode/mcp.json.example`](../.vscode/mcp.json.example) → `.vscode/mcp.json` |
| Antigravity | Copy [`.agents/mcp_config.example.json`](../.agents/mcp_config.example.json) → `.agents/mcp_config.json` |

Restart the IDE after MCP config changes. Use **Agent mode** to call tools.

## Tests

**IDE terminal** (venv activated):

```bash
pytest
```
