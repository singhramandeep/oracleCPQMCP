# Agent instructions (all IDEs)

This repo is used from **Google Antigravity**, **Cursor**, **VS Code Copilot**, and other MCP clients.

## Authoritative runtime rules

When **Oracle CPQ MCP** is connected, **MCP server instructions** (`build_server_instructions` in `mcp/oracle_cpq_mcp/prompts/instructions.py`) are the **single source of truth** for agent behavior (refined prompt, export, templates, credentials, local data, Prompt Studio).

Do **not** rely on [`.cursor/rules/`](.cursor/rules/) alone — Cursor mirrors only. Identify the active model when the host surfaces it.

## After changing instructions

Reload/restart Oracle CPQ MCP so agents pick up new text.

### How to edit agent rules

1. **Runtime policy** — [`mcp/oracle_cpq_mcp/prompts/instructions.py`](mcp/oracle_cpq_mcp/prompts/instructions.py)
2. **This file** — short engagement notes
3. **Tool authoring** — [`docs/STANDARDS.md`](docs/STANDARDS.md)
4. **Cursor mirrors last** — [`.cursor/rules/`](.cursor/rules/)

| IDE | Example → live config |
|-----|------------------------|
| Antigravity | [`.agents/mcp_config.example.json`](.agents/mcp_config.example.json) → `.agents/mcp_config.json` |
| Cursor | [`.cursor/mcp.json.example`](.cursor/mcp.json.example) → `.cursor/mcp.json` |
| VS Code | [`.vscode/mcp.json.example`](.vscode/mcp.json.example) → `.vscode/mcp.json` |

Setup: [`docs/SETUP.md` — Step 7](docs/SETUP.md#step-7--connect-the-ide-mcp).

## Short rules

1. Honor MCP instructions for CPQ work; connect MCP before refined prompts, exports, or branded docs.
2. Clone `.config/template/` (`Word Template.docx` / `Excel Template.xlsx` / `PowerPoint Template.pptx`) for Office; template dir is read-only; write under `data/{profile}/{env}/exports/`. Details (Mermaid, styles) live in MCP `DOCUMENT_TEMPLATES`.
3. Never edit profile credentials or Fusion OAuth secrets — report 401s only. Live CPQ and Fusion CX only via MCP tools (`CPQClient` / `CXClient`).
4. Prefer MCP tools over one-off scripts; scratch under `tmp/{profile}/{env}/`. Tool authoring: `docs/STANDARDS.md`. CX top-level `list_*` use Adaptive Search JSON `q`/`keywords` (not ADF SCIM); discovery via `list_adaptive_search_*` — never Adaptive Search for CPQ.
5. Profile `frugal_mode: true` (or `CPQ_FRUGAL_MODE`) shortens MCP instructions and disables refined footer, auto-export, and Prompt Studio ensure.
