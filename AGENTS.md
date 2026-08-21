# AGENTS.md

## Cursor Cloud specific instructions

This repo is a **Python stdio MCP server** for Oracle CPQ (`python -m oracle_cpq_mcp`). There is no web UI, database, or long-running service to boot — the "service" is a JSON-RPC-over-stdio process that an MCP client spawns on demand.

### Environment / running commands
- Dependencies are installed into a project virtualenv at `.venv` by the startup update script. Activate it first: `source .venv/bin/activate` (or prefix commands with `.venv/bin/`).
- Test/build/run commands are documented in [README.md](README.md), [docs/QUICKSTART.md](docs/QUICKSTART.md), [docs/SETUP.md](docs/SETUP.md), and [SECURITY_TESTING.md](SECURITY_TESTING.md). Prefer those.
- Package is installed editable (`pip install -e`), so source edits are picked up without reinstalling. Reinstall only when dependencies or entry points change.

### Tests / lint
- Tests: `PYTHONPATH=mcp CPQ_SCHEMA_INTEGRITY=1 pytest tests/ -q`. The `PYTHONPATH=mcp` and `CPQ_SCHEMA_INTEGRITY=1` env vars match CI (`.github/workflows/security.yml`); without `PYTHONPATH=mcp` imports of `oracle_cpq_mcp` fail. Tests mock all CPQ HTTP calls via `respx`, so **no real Oracle CPQ credentials are needed** to run them.
- Security lint (same as CI): `bandit -r mcp/oracle_cpq_mcp -ll -q` and `pip-audit`.
- After intentional tool-catalog changes, regenerate `mcp/oracle_cpq_mcp/security/tool_manifest.json` (see [SECURITY_TESTING.md](SECURITY_TESTING.md)); otherwise schema-integrity checks/tests fail.

### Running the MCP server locally (no real CPQ needed for startup)
- The server calls `load_profile()` at import time, so it will not start without a credential profile at `.config/<profile>.env` (gitignored). Create a local dummy one from the template to let the server boot and enumerate tools:
  `cp .config/.env.example .config/mycompany.env` (dummy URLs/credentials are fine for startup + `discover_tools`).
- Start it as an MCP client would: spawn `python -m oracle_cpq_mcp` over stdio with env `CPQ_CUSTOMER_PROFILE=mycompany`, `CPQ_CONFIG_DIR=<repo>/.config`, `CPQ_SCHEMA_INTEGRITY=1`. On handshake it exposes **14 tools**; `discover_tools` runs fully offline.
- **Tools that call Oracle CPQ (`list_users`, `get_datatable`, the `oracle-cpq-smoke` CLI, etc.) require real CPQ credentials and network/VPN access to a `*.bigmachines.com` site**, which are not available in the cloud VM. Expect those specific calls to fail with connection errors; that is not an environment misconfiguration.
