# MCP Server Package

This folder contains the **Oracle CPQ MCP server** — the installable Python package consumed by Cursor, VS Code MCP extensions, and `python -m oracle_cpq_mcp`.

```
oracle_cpq_mcp/
  core/        # Config, CPQClient, errors, pagination, filters
  registry/    # Tool catalog and discovery metadata
  tools/       # MCP tool handlers
  exporters/   # Excel helpers for MCP tools
  server.py    # FastMCP entrypoint
```

Non-MCP scripts live in [`../utilities/`](../utilities/).

Install from the repository root — **IDE terminal** (`` Ctrl+` ``):

```bash
pip install -e ".[dev]"
python -m oracle_cpq_mcp
```
