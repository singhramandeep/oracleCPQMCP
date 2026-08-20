# Oracle CPQ MCP — Technical & Correctness Audit Report

**Date:** 2026-08-20  
**Scope:** Full codebase audit per [`prompts/audit.md`](../../prompts/audit.md)  
**Server version:** 0.1.0 (`mcp/oracle_cpq_mcp/__init__.py`)  
**Tools audited:** 19 (Users, Groups, Data Tables, BML, Commerce metadata, discovery)

**Important scope note:** This MCP server exposes **admin/config REST APIs** (users, groups, datatables, BML export, commerce document metadata). It does **not** expose live **quotes, transactions, pricing, or approval** APIs. Business Q&A in those domains must not be answered from this server without new tools.

Research sources: [Audit MCP tools and errors](89b80c97-1de8-45f8-87d0-76fd71815500), [Audit security and observability](202b0581-78c0-4466-b7ec-04c0980b7321).

---

## 1. EXECUTIVE SUMMARY

**Overall:** Error wrapping, dry-run/confirmation for writes, strict Pydantic inputs, and paginated-list hints are solid for an **admin/config** MCP. Hallucination risk remains **high** for business-critical answers because most success envelopes omit **environment** and **freshness**, bulk paths can **truncate silently**, and there are **no quote/pricing tools** while nothing instructs the model not to invent those facts.

**Top 5 risks (by severity):**

1. **P0 — Missing environment / as-of on read responses** — ~~`build_ok_envelope` returned only `status`, `tool`, `data`~~ **Addressed (2026-08-20):** `stamp_response_context` adds `environment`, `customer_id`, `retrieved_at` on every LLM-facing envelope (`core/responses.py`, `tools/_register.py`).
2. **P0 — No quote/pricing/approval tools + weak grounding** — `server.py` instructions (L33–43) cover writes/errors but do not forbid answering from training data. Operators may expect commercial Q&A this server cannot ground. *(Not in this fix pass.)*
3. **P0 — Error payloads skip sanitization** — ~~error early-return skipped redaction~~ **Addressed (2026-08-20):** errors are redacted; LLM `details` omit `response`/`curl` (`security/sanitization.py`, `core/errors.py`).
4. **P1 — Silent truncation on bulk export** — ~~`iterate_collection` capped with log only~~ **Addressed (2026-08-20):** returns `CollectionFetchResult`; `export_users_excel` surfaces `truncated`/`has_more`/`max_rows`/`row_count`.
5. **P1 — Commerce metadata may be incomplete** — ~~no pagination~~ **Addressed (2026-08-20):** commerce tools accept `limit`/`offset` and use `enrich_pagination_hint`.

**Safe to connect to production CPQ today?** **No** for write-enabled or accuracy-sensitive production use. **Conditional yes** for **read-only dev/test** exploration with operator awareness: use `READ_ONLY=true`, do not treat answers as quote/pricing truth, and fix P0 grounding/redaction before broader rollout.

---

## 2. MCP PROTOCOL CORRECTNESS

### Tool input schemas

| Assessment | Location | Detail |
|------------|----------|--------|
| **Strong** | `security/validation.py` L17–18 | Pydantic `extra="forbid"` on input models |
| **Strong** | `security/validation.py` L14, L49+ | CPQ ID pattern `^[A-Za-z0-9_-]+$` |
| **Weak** | `validation.py` L61, L91 | `patch_body` / `group_body` as `dict[str, Any]` — only non-empty / `variableName` checks |
| **Weak** | `validation.py` L25 | `q_expr` free-form up to 2000 chars → LLM-controlled CPQ query string |

### Tool descriptions

| Assessment | Location | Detail |
|------------|----------|--------|
| **Adequate** | `registry/tool_registry.py` | Paginated tools mention `hasMore` and next offset (e.g. L109–113, L219–221) |
| **Gap** | `tool_registry.py` | Few descriptions state empty-result semantics, units/formats, or explicit “does not” clauses |
| **Good** | `tool_registry.py` L26–30 | Write tools append dry-run/confirmation suffix |

**Overlapping tools (LLM mis-selection risk):**

| Pair | Issue |
|------|--------|
| `get_commerce_attributes` vs `get_line_attributes` (L288–335) | Same API path pattern; differs only by default `doc_var_name` |
| `get_commerce_actions` vs `get_line_actions` (L304–350) | Same |
| `get_user_groups` vs `list_group_users` (L139–200) | Both user↔group; direction not sharply contrasted in descriptions |
| `list_users` vs `export_users_excel` (L105–127) | Export omits 10,000-row cap / truncation in description |

### Resources vs Tools

Everything is a **Tool**. No MCP **Resources** for cacheable catalog/metadata (`server.py` registers tools only). Static commerce/datatable metadata would fit Resources; not modeled.

### Transport

- **Stdio only:** `server.py` L95–97 `mcp.run()`
- **Auth:** `security/auth.py` L17–21 — `StdioTrustedHostAuth` always trusts host; **not safe** if HTTP transport is added without real auth

### Response shape

- Success envelope: `{status, tool, data, pagination?}` via `wrap_tool_success` (`core/responses.py` L93–113)
- Error envelope: `{status:error, code, message, hint?, details?}` (`core/errors.py` L47–64)
- Declared MCP `output_schema` is loose: `required: ["status"]`, `additionalProperties: true` (`schemas/tool_outputs.py` L87–91)
- Post-execution validation: `core/output_validation.py` + `_register.py` L166–172

### Pagination

- **Page tools:** `enrich_pagination_hint` (`core/pagination.py` L60–74) adds `pagination.nextOffset` / `suggestedNextCall` when `hasMore`
- **Bulk:** `iterate_collection` truncates at `max_items` with log warning only (L120–127) — **not** returned to LLM

---

## 3. HALLUCINATION & ACCURACY RISK AUDIT

### a) Silent failure modes

| Location | What's wrong | Why it matters (LLM-facing CPQ) | Fix | Priority |
|----------|--------------|----------------------------------|-----|----------|
| `pagination.py` L120–127 | Truncation at `max_items` logged only | Export/list looks complete | Return `truncated`, `hasMore`, `max_items` in envelope | P1 |
| `exporters/users_excel.py` + `tools/users.py` L120–128 | 10k cap via `iterate_collection`; summary prose only | “Exported N users” misread as full census | Structured truncation flags in lead envelope | P1 |
| `core/bml_fetchers.py` L63–75 | Bad detail payloads skipped with warning | Incomplete util library presented as full | Fail or return `skipped`/`errors` list | P1 |
| `tools/bml.py` L51 | `truncated = len(functions) >= 1000` heuristic | False positives/negatives on completeness | Use pagination meta from `iterate_collection` | P2 |
| `core/preflight.py` L127–128 | Token issuance exceptions swallowed in `attach_confirmation_to_response` | `preflight_ok` without token → LLM thinks ready to execute | Surface `CONFIRMATION_INVALID` / fail preflight | P1 |
| `cpq_client.py` L173–174 | 204/empty → `None` | Ambiguous vs error until output validation | Explicit empty-success shape | P2 |
| Empty `items:[]` on 200 | Passed through as success | Correct if API healthy; descriptions don't say “empty ≠ error” | Document in tool descriptions | P2 |

**Not silent (good):** HTTP 4xx/5xx → `CPQAPIError` → structured error via `_register.py` L180–182.

### b) Data fidelity

| Finding | Evidence | Priority |
|---------|----------|----------|
| Environment not in most responses | `build_ok_envelope` L49–56; env only in some messages/BML JSON | P0 |
| No `retrieved_at` / as-of | No timestamp in tool envelopes; audit timestamp server-side only (`security/audit.py` L38) | P0 |
| LLM cannot request env | Blocked kwargs (`security/authorization.py` L10–25) — increases need to echo env in responses | — |
| Excel display coercion | `exporters/users_excel.py` L32–41 prefers `displayValue` over raw | P2 |
| BML JSON field reshaping | `core/bml_fetchers.py` L76–87 | P2 |

### c) Prompt-level grounding

`server.py` instructions (L33–43): write safety + error shape. **Missing:**

- Only state facts returned by tool calls
- Say “not found” / “unable to retrieve” instead of inferring
- Do not answer quotes/pricing/approvals from general knowledge
- Always cite environment and retrieval time

### d) Identifier safety

- Strict ID validation before CPQ (`validation.py` L14, L49–50) — good
- 404 → `NOT_FOUND` with hints (`core/errors.py` L103–104) — no fuzzy match — good
- Wrong but existing `party_number` returns wrong user (inherent); update preflight shows `current_user` (`preflight.py` L247–248) — mitigates writes

### e) Tool-call discipline

No generic “explain CPQ” tool — good. **Gap:** absence of quote/pricing tools does not stop LLM from answering from memory.

### Tool hallucination risk table

| Tool | Risk | Specific fix |
|------|------|--------------|
| `list_users` | Med | Add env + `retrieved_at`; document empty `items` |
| `export_users_excel` | **High** | Surface truncation; structured env fields |
| `get_user` | Med | Env/as-of; 404 = not found, don't invent |
| `get_user_groups` | Med | Disambiguate vs `list_group_users` |
| `update_user` | Med | Env in write envelopes; keep dry-run default |
| `list_groups` | Med | Env/as-of; note company from profile |
| `get_group` | Med | Env/as-of |
| `list_group_users` | Med | Disambiguate description |
| `create_group` | Med | Env in preflight/success |
| `list_datatables` | Med | Env/as-of |
| `get_datatable` | Med | Env/as-of |
| `get_datatable_rows` | Med | Empty page clarity |
| `deploy_datatables` | Med–High | Env in destructive confirmations |
| `get_all_bml_code` | **High** (json) / Med (zip) | Fix skip/truncation signaling |
| `get_commerce_attributes` | **High** | Pagination if API pages; env/as-of; disambiguate vs line |
| `get_commerce_actions` | **High** | Same |
| `get_line_attributes` | **High** | Same |
| `get_line_actions` | **High** | Same |
| `discover_tools` | Low–Med | `hasMore` when catalog truncated |

---

## 4. SECURITY & AUTH AUDIT

| Topic | Finding | Location | Priority |
|-------|---------|----------|----------|
| Credentials in LLM output | Error path skips sanitization; raw CPQ `details.response` | `sanitization.py` L67–69, `errors.py` L222–246 | P0 |
| Credentials in logs | Full CPQ error bodies logged | `cpq_client.py` L155–158 | P1 |
| Basic Auth | No OAuth; no retry-on-401 | `cpq_client.py` L113–171 | P1 (resilience) |
| Write guardrails | dry_run default, HMAC confirmation, replay, READ_ONLY, prod gate | `preflight.py`, `confirmation.py`, `_register.py`, `authorization.py` L54–71 | OK |
| Confirmation secret unset | Tokens not attached silently; writes fail closed but confusing | `preflight.py` L121–122, `confirmation.py` L47–50 | P1 |
| MCP transport auth | Stdio trusted host only | `security/auth.py` L17–21 | OK for stdio; P0 if HTTP added |
| Injection | `q_expr` passthrough to CPQ query | `core/users_filters.py` L26–27, `validation.py` L25 | P2 |
| Rate limits | In-process sliding window works | `security/rate_limit.py` L21–45 | OK |
| Rate limit env knobs | `CPQ_READ_CALLS_PER_MINUTE` etc. loaded but unused | `settings.py` L45–49 vs `policy.py` L25–32 | P2 |
| Session call cap | `CPQ_MAX_TOOL_CALLS` via ContextVar may not accumulate across async calls | `context.py` L51–54, `_register.py` L108–116 | P1 |
| Multi-env | Single profile at startup; kwargs env blocked — good | `server.py` L85, `authorization.py` L10–25 | OK |
| Schema integrity | Missing manifest fails open (warning only) | `security/schema_integrity.py` L63–68 | P2 |

---

## 5. ERROR HANDLING & RESILIENCE

| Topic | Assessment | Location |
|-------|------------|----------|
| Consistent error shape | Yes for exceptions → structured envelope | `errors.py`, `_register.py` |
| Errors omit `tool` / `environment` | Unlike success envelopes | `errors.py` L47–64 |
| Timeout | 60s default, no per-tool override | `cpq_client.py` L18, L115 |
| Retries | None for 429/5xx/network | `cpq_client.py` entire client |
| CPQ down | `NETWORK_ERROR` with hint | `cpq_client.py` L122–137 |
| Output validation failure | Opaque `INTERNAL_ERROR` to LLM (by design) | `_register.py` L166–172 |
| Connection pooling | New `httpx.Client` per request | `cpq_client.py` L113–120 |

---

## 6. CODE QUALITY & MAINTAINABILITY

| Topic | Assessment |
|-------|------------|
| Separation of concerns | Clear: `CPQClient` / tools / `_register` pipeline / FastMCP |
| Input typing | Strong Pydantic models |
| CPQ payload typing | Mostly `dict[str, Any]` — expected for REST passthrough |
| Config | Externalized `.config/<customer>.env` (`core/config.py`) |
| Tests | ~204 tests; gaps on error sanitization, audit events, session cap, truncation flags |
| Policy bug smell | `ToolPolicy.idempotent=spec.operation == "write"` inverts MCP `idempotentHint` | `security/policy.py` L45 vs `tool_registry.py` L390 |

---

## 7. OBSERVABILITY

| Topic | Assessment | Location |
|-------|------------|----------|
| Audit events | tool, customer, env, duration, error_code, args_hash | `security/audit.py` L37–55 |
| Audit gaps | No CPQ HTTP status/path; no response size; args_hash only | `audit.py` |
| Actor | Hard-coded `stdio_host` | `security/context.py` L26, L38 |
| Health/metrics | None — stdio process only | `server.py` L95–97 |
| Wrong-answer forensics | Hard without env/as-of on payload LLM saw | `responses.py` |

---

## 8. PRIORITIZED ACTION PLAN

### P0 (blocks safe production / accurate LLM use)

| Item | Location | Effort |
|------|----------|--------|
| Redact/sanitize **error** tool payloads same as success | `security/sanitization.py` L67–69 | S |
| Strip or redact `details.response` / curl username from LLM errors | `core/errors.py` L222–246 | S |
| Add `environment`, `customer_id`, `retrieved_at` to every success/error envelope | `core/responses.py`, `_register.py` | S |
| Grounding instructions: forbid inventing quotes/pricing; only state tool facts | `server.py`, `tool_registry.py` | S |
| Document scope: no quote/pricing APIs | `README.md`, `docs/QUICKSTART.md` | S |

### P1 (fix before broader use)

| Item | Location | Effort |
|------|----------|--------|
| Surface truncation on export / `iterate_collection` | `pagination.py`, `users_excel.py`, `users.py` | S–M |
| BML skipped payloads / truncation flags | `bml_fetchers.py`, `bml.py` | S |
| Don't swallow confirmation token failures | `preflight.py` L127–128 | S |
| Require `CPQ_CONFIRMATION_SECRET` when `READ_ONLY=false` | `server.py` / `settings.py` | S |
| Commerce pagination + hints if API paginates | `tools/commerce.py`, `validation.py` | M |
| Fix session call cap (process-global vs ContextVar) | `context.py`, `_register.py` | S |
| Tests for error sanitization, truncation communication | `tests/` | M |

### P2 (should fix soon)

| Item | Location | Effort |
|------|----------|--------|
| Disambiguate commerce/line and user-group descriptions | `tool_registry.py` | S |
| Retry with backoff for GET 5xx/network | `cpq_client.py` | M |
| Wire rate-limit env knobs or remove dead vars | `settings.py`, `policy.py` | S |
| Fail-closed schema integrity when manifest missing | `schema_integrity.py` | S |
| Tighten output schemas beyond `required:[status]` | `schemas/tool_outputs.py` | M |
| Avoid logging raw CPQ error bodies | `cpq_client.py` L155–158 | S |
| `discover_tools` hasMore when catalog truncated | `tool_registry.py` | S |

### P3 (nice to have)

| Item | Location | Effort |
|------|----------|--------|
| MCP Resources for catalog/metadata | new module | L |
| Health/metrics for ops monitoring | server / wrapper | M |
| Eval/regression Q&A against CPQ sandbox | `tests/` | L |
| Typed CPQ DTOs for common responses | `core/` | L |
| HTTP OAuth if non-stdio deploy | `security/auth.py` | L |

---

## 9. GENERAL IMPROVEMENT IDEAS

- **Cache** commerce attributes/actions and datatable metadata with explicit `cache_as_of` — reduces API load and forces freshness labeling.
- **Merge** commerce tools (`get_document_attributes(doc_kind=main|line)`) to reduce LLM mis-selection.
- **Return** `{summary, raw}` for large collections so the model cites counts/`hasMore` before dumping items.
- **Multi-env:** keep host-controlled env, but always stamp responses; optional compare tools for dev vs test.
- **Accuracy eval set:** fixed party numbers, known empty lists, forced 404s, truncated export — catch grounding regressions in CI.
- **Confidence/freshness field:** e.g. `{freshness: {retrieved_at, environment, truncated: false}}` on every data response.

---

## Appendix: What this server can and cannot answer

| Can ground (with fixes above) | Cannot ground today |
|------------------------------|---------------------|
| User/group membership, profiles | Live quote totals, line pricing, discounts |
| Data table schema and rows | Approval workflow state on transactions |
| BML source export | Product configuration BOM logic |
| Commerce document attribute/action **metadata** | Real-time commerce **instance** data |

For commercial Q&A, add dedicated quote/transaction MCP tools or integrate a separate pricing API — do not rely on the LLM's Oracle CPQ training data.
