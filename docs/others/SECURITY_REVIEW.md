# Security Review Report

## Executive summary

Server-side guardrails were added to the stdio Oracle CPQ MCP server: centralized tool policies, strict input validation, HMAC confirmation tokens for writes, rate limiting, replay protection, output redaction, schema integrity verification, and structured audit logging.

## Findings addressed

| ID | Severity | Category | Location | Fix | Test |
|----|----------|----------|----------|-----|------|
| SEC-001 | HIGH | Authorization | Write tools | LLM could set `confirmed=true` without binding | HMAC `confirmation_token` in `security/confirmation.py` | `test_confirmation.py` |
| SEC-002 | HIGH | Policy | No central registry | Scattered read/write flags only | `TOOL_POLICIES` + `ToolSpec.risk` | `test_policy.py` |
| SEC-003 | MEDIUM | Input validation | Tool handlers | Weak type hints only | Pydantic `extra=forbid` models | `test_validation.py` |
| SEC-004 | MEDIUM | Environment | Config | Prod accessible via env | `CPQ_ALLOW_PROD` fail-closed | `test_policy.py` |
| SEC-005 | MEDIUM | Abuse | No rate limits | Agentic loops unbounded | Rate limit + session cap | `test_rate_limit.py` |
| SEC-006 | MEDIUM | Replay | Write tools | Duplicate execution | Replay store | `test_replay.py` |
| SEC-007 | MEDIUM | Disclosure | API responses | Password fields in output | `sanitization.py` | `test_sanitization.py` |
| SEC-008 | MEDIUM | Tool poisoning | Tool catalog | Silent schema changes | `tool_manifest.json` hash | `test_schema_integrity.py` |
| SEC-009 | LOW | Audit | Logging | No structured security events | `audit.py` JSON logs | Manual verification |

## Residual risk

- Stdio trust boundary: compromised Cursor host bypasses MCP controls
- No MCP user identity (deferred to HTTP/OAuth phase)
- CPQ integration user permissions are the resource-level authorization boundary

## Recommendations (future)

1. HTTP transport with OAuth 2.1 per MCP authorization spec
2. OCI Vault for credential storage in production
3. Per-resource authorization beyond integration-user scope
