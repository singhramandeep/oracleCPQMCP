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

## Configure

**IDE terminal** (repo root):

| Shell | Command |
|-------|---------|
| Windows PowerShell / CMD | `copy .config\.env.example .config\mycompany.env` |
| macOS / Linux / Git Bash | `cp .config/.env.example .config/mycompany.env` |

Edit `.config/mycompany.env` with your CPQ URLs and credentials.

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
