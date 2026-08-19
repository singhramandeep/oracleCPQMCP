@echo off
REM Cross-platform MCP entrypoint for Windows (Cursor, VS Code, Antigravity).
setlocal

set "ROOT=%~dp0.."
set "PY=%ROOT%\.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo Oracle CPQ MCP: missing virtualenv at %ROOT%\.venv >&2
  echo Run from repo root: python -m venv .venv ^&^& .venv\Scripts\Activate.ps1 ^&^& pip install -e ".[dev]" >&2
  exit /b 1
)

cd /d "%ROOT%"
"%PY%" -m oracle_cpq_mcp
