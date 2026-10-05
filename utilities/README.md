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
| `fusion_oauth_token.py` | Standalone IDCS/Fusion OAuth **client_credentials** token (same helper MCP/`CPQClient` use when CPQ `auth: bearer`) |
| `stub_fusion_oauth_token.py` | Mock-only OAuth path check (no live IDCS) |
| `stub_fusion_get_transaction.py` | Live: OAuth token then Bearer **GET** Fusion transaction (`/cpq/rest/v19/…`) |

## Examples

**IDE terminal** (repo root, venv activated):

```bash
oracle-cpq-smoke --profile mycompany --env dev
python utilities/lookup_user.py myuser
python utilities/count_users_by_email.py "@example.com"
python utilities/compare_users_by_email.py
```

### Fusion OAuth token (standalone)

Obtains an Oracle IDCS access token via OAuth 2.0 client credentials. Thin CLI around `oracle_cpq_mcp.security.fusion_oauth` — the **same** helper MCP `get_fusion_access_token` and `CPQClient` use when nested `cpq.auth: bearer`. Prefer MCP tools for engagement work; use this CLI only for local debugging. Fusion CX REST uses `CXClient` (not this script).

```bash
python utilities/fusion_oauth_token.py \
  --token-url "https://idcs-….identity.oraclecloud.com/oauth2/v1/token" \
  --client-id "YOUR_CLIENT_ID" \
  --client-secret "YOUR_CLIENT_SECRET" \
  --scope "urn:opc:resource:fusion:YOUR_ENV:cpq/"
```

Env fallbacks: `FUSION_OAUTH_TOKEN_URL`, `FUSION_OAUTH_CLIENT_ID`, `FUSION_OAUTH_CLIENT_SECRET`, `FUSION_OAUTH_SCOPE`.  
Add `--json` to print `access_token` / `token_type` / `expires_in` / `scope`. Never commit real client secrets.

### Fusion Get Transaction stub (live Bearer)

Obtains a token with the same OAuth env/flags, then **GET**s the Postman-style Fusion URL  
`{base}/cpq/rest/v19/commerceDocumentsOraclecpqoTransaction/{id}` with `Authorization: Bearer …`.

```bash
python utilities/stub_fusion_get_transaction.py
# optional overrides:
#   --transaction-id REPLACE_TRANSACTION_ID
#   --base-url https://example-fusion-dev.fa.ocs.oraclecloud.com
#   --transaction-url "https://…/cpq/rest/v19/commerceDocumentsOraclecpqoTransaction/…"
#   --print-body
```

Defaults are placeholders only — override `--base-url` / `--transaction-id` (and OAuth env/flags) for a real site.

Set `CPQ_CUSTOMER_PROFILE`, `CPQ_ENVIRONMENT`, and `CPQ_CONFIG_DIR` as documented in the root README.
