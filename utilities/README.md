# Utilities

Standalone scripts and dev tools that use the Oracle CPQ MCP Python package but are **not** part of the MCP server runtime.

Install the package first — **IDE terminal** (repo root, `` Ctrl+` ``):

```bash
pip install -e ".[dev]"
```

## Scripts

| Script | Purpose |
|--------|---------|
| `smoke.py` | Connectivity smoke test (also available as `oracle-cpq-smoke`) |
| `lookup_user.py` | Look up a CPQ user by login |
| `count_users_by_email.py` | Count users matching an email substring |
| `compare_users_by_email.py` | Compare users across dev/test by email |

## Examples

**IDE terminal** (repo root, venv activated):

```bash
oracle-cpq-smoke --profile mycompany --env dev
python utilities/lookup_user.py hmohammed
python utilities/count_users_by_email.py "@example.com"
python utilities/compare_users_by_email.py
```

Set `CPQ_CUSTOMER_PROFILE`, `CPQ_ENVIRONMENT`, and `CPQ_CONFIG_DIR` as documented in the root README.
