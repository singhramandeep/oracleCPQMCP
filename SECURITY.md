# Security Architecture

Oracle CPQ MCP implements **server-side guardrails** around every tool. The LLM is not trusted to enforce security policy.

## Trust boundaries

```
Cursor (trusted host) → stdio → MCP security pipeline → CPQ tools → Oracle CPQ REST API
```

- **Stdio mode:** Authentication is implicit — the host process (Cursor) is the trust boundary. No MCP bearer tokens are validated (deferred for HTTP/OAuth phase).
- **Oracle CPQ:** Integration-user Basic Auth; CPQ RBAC is authoritative for business rules.

## Controls implemented

| Control | Module | Behavior |
|---------|--------|----------|
| Tool risk classification | `registry/tool_registry.py`, `security/policy.py` | READ_ONLY, PRIVILEGED, HIGH_RISK_WRITE, DESTRUCTIVE |
| Deny-by-default authorization | `security/authorization.py` | Unknown tools denied; prod blocked unless `CPQ_ALLOW_PROD=1` |
| READ_ONLY gate | `core/cpq_client.py`, `core/preflight.py` | Blocks mutating HTTP + write execution |
| Strict input validation | `security/validation.py` | Pydantic `extra=forbid`, bounded CPQ identifiers |
| Blocked security args | `security/authorization.py` | Rejects `environment`, `tenant_id`, `credentials`, etc. |
| HMAC confirmation tokens | `security/confirmation.py` | Write ops bound to `{tool, args_hash, customer, env}` |
| Replay protection | `security/replay.py` | Duplicate writes within window rejected |
| Rate limiting | `security/rate_limit.py` | Per-tool sliding window |
| Session tool cap | `security/context.py` | `CPQ_MAX_TOOL_CALLS` per session |
| Output redaction | `security/sanitization.py` | Recursive sensitive-field redaction |
| Schema integrity | `security/schema_integrity.py` | SHA-256 manifest at startup |
| Structured errors | `core/errors.py` | No stack traces or secrets in tool responses |
| Audit logging | `security/audit.py` | JSON events to stderr (no secrets) |

## Write operation flow

1. `dry_run=true` (default) → preflight only; response includes `confirmation_token` when secret configured.
2. User approves → agent calls with `dry_run=false` + `confirmation_token`.
3. Pipeline validates token, checks replay/rate limits, executes via CPQClient.

## Configuration

See README **MCP host security environment variables**. Set `CPQ_CONFIRMATION_SECRET` when `READ_ONLY=false`.

## Secret handling

- Credentials in `.config/*.env` (gitignored)
- Never log passwords, tokens, or Authorization headers
- Confirmation secret is host env only — not exposed to LLM via tool responses

## Incident response

1. Rotate CPQ integration user password and `CPQ_CONFIRMATION_SECRET`.
2. Set `READ_ONLY=true` to halt writes immediately.
3. Review audit logs (`oracle_cpq_mcp.audit` logger) for `request_id` / `trace_id`.

## Residual risks (stdio scope)

- Host process compromise bypasses MCP layer
- No per-user MCP identity until HTTP/OAuth phase
- Resource-level CPQ authorization depends on integration user permissions

See [THREAT_MODEL.md](THREAT_MODEL.md) and [SECURITY_TESTING.md](SECURITY_TESTING.md).
