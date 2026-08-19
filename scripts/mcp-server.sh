#!/usr/bin/env bash
# Cross-platform MCP entrypoint for macOS/Linux (Cursor, VS Code, Antigravity).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "Oracle CPQ MCP: missing virtualenv at $ROOT/.venv" >&2
  echo "Run from repo root: python3 -m venv .venv && source .venv/bin/activate && pip install -e \".[dev]\"" >&2
  exit 1
fi

cd "$ROOT"
exec "$PY" -m oracle_cpq_mcp
