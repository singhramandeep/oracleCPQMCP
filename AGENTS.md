# Agent instructions (all IDEs)

This repo is used from **Google Antigravity**, **Cursor**, **VS Code Copilot**, and other MCP clients.

## Authoritative runtime rules

When the **Oracle CPQ MCP** server is connected, its **MCP server instructions** (built by `build_server_instructions` in `mcp/oracle_cpq_mcp/prompts/instructions.py`) are the **single source of truth** for agent behavior:

- Refined-prompt gate, turn metrics (Elapsed / Tokens), local-data policy, post-response export, Prompt Studio
- Document branding from `.config/template/` (Word / Excel / PowerPoint)
- Knowledge base and property aliases
- Write safety (dry-run, confirmation tokens, read-only)

Do **not** rely on [`.cursor/rules/`](.cursor/rules/) alone — those files are **Cursor convenience mirrors**. Antigravity and other IDEs do **not** load them.

Identify the active model when the host surfaces it; do not invent model names.

## After changing instructions

Reload or restart the Oracle CPQ MCP server in your IDE so agents pick up new instruction text.

## Where to look

| Resource | Purpose |
|----------|---------|
| MCP server instructions | Runtime agent policy (all IDEs) |
| [`docs/STANDARDS.md`](docs/STANDARDS.md) | Tool authoring checklist |
| [`.config/template/README.md`](.config/template/README.md) | Branded Word/Excel/PPT templates |
| [`.agents/mcp_config.example.json`](.agents/mcp_config.example.json) | Antigravity MCP config |
| [`.cursor/mcp.json.example`](.cursor/mcp.json.example) | Cursor MCP config |
| [`.vscode/mcp.json.example`](.vscode/mcp.json.example) | VS Code MCP config |
| [`.cursor/rules/`](.cursor/rules/) | Cursor-only mirrors / file-glob checklists |

## Short rules

1. Honor MCP instructions for CPQ work; connect MCP before expecting refined prompts, exports, or branded docs.
2. Create Word/Excel/PPT by **cloning** `.config/template/` packages when valid (exact names: `Word Template.docx`, `Excel Template.xlsx`, `PowerPoint Template.pptx`). Preserve header/footer/logo by clearing body only; use **Title / Heading 1 / Heading 2 / Heading 3 / Normal**. Treat `.config/template/` as read-only — never write or “fix” files there; write outputs under `data/{profile}/{env}/exports/`. MCP exporters use `oracle_cpq_mcp.exporters.branded_documents`. For analytical Word exports (audits, pass/fail, flows, comparisons, rankings, share breakdowns), pass **1–3 Mermaid diagrams** on `export_response_word` via `diagrams` (local `mmdc`; never public Kroki/mermaid.ink) without waiting for the user to ask — choose **flowchart/graph** for flows, **pie** for shares of a whole, **xychart-beta** bar/line for numeric comparisons. Pictographs only via optional local PNG `image_path` under `tmp/`. Structure `notes` with `##` / bullets — not one dense paragraph. Skip diagrams for trivial lists or pure errors.
3. Never edit profile `username` / `password` (or `*_USERNAME` / `*_PASSWORD`), or Fusion `oauth_client_id` / `oauth_client_secret`, in `.config/*.yaml` / `.env` — user owns credentials; report 401s without “fixing” them. Fusion profiles (`mode: fusion`) use Bearer + `/cpq/rest/{version}` via MCP/`CPQClient` automatically — do not invent alternate REST paths.
4. Use only Oracle CPQ MCP tools for live CPQ access — never call CPQ REST with profile credentials via curl/httpx/scripts.
5. Prefer MCP tools over new one-off Python for engagement work: CPQ reads/writes, `sync_*_local` / `load_local_data`, and branded exports via `export_response_excel` / `export_response_word`. Do **not** invent `tmp/.../write_*.py` when an MCP tool already covers the task. Scratch JSON/MD under `tmp/{profile}/{env}/` only when MCP cannot express the step; list paths under **Scratch files** when created. Maintainer CLIs live in `oracle-cpq` (`migrate-yaml`, `lint-schemas`, `generate-tool-catalog`) — reuse those instead of new scripts.
6. For contributing tools, follow `docs/STANDARDS.md` (not IDE-specific rule files).
