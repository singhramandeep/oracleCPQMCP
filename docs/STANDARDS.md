# Oracle CPQ MCP — Tool Authoring Standards

Day-to-day checklist for adding or changing MCP tools. Historical findings live in [`others/AUDIT_REPORT.md`](others/AUDIT_REPORT.md). After any tool change, run the compliance prompt: [`prompts/compliance_check.md`](../prompts/compliance_check.md).

## Non-negotiables

1. **Typed inputs** — Every tool has a `_StrictModel` in [`security/validation.py`](../mcp/oracle_cpq_mcp/security/validation.py) with `extra="forbid"`. Every field uses `Field(..., description="...")`.
2. **Catalog entry** — Add a `ToolSpec` in [`registry/tool_registry.py`](../mcp/oracle_cpq_mcp/registry/tool_registry.py) via `_spec(...)`. Required: clear `description` (pagination / empty / “does not” where relevant), human `title` (defaults from the tool name if omitted), semver `version` (start at `1.0.0`), icons (omit to inherit the domain default), and **`cx_module`** (`cpq` / `service` / `meta` — defaults to `meta` when `domain=="meta"`, else `cpq`; pass `cx_module="service"` for CX Service REST tools). Functional `domain` stays orthogonal to `cx_module`. **Bump `version` whenever you change that tool’s behavior, schema, description, API path, title, icons, or `cx_module`.** Refined-prompt footers may be saved with `offer_save_refined_prompt` / `save_refined_prompt` into `.prompts/saved_prompts.json` (not CPQ). Full collection snapshots may persist under `data/{profile}/{env}/` via `sync_*_local` / auto-persist hooks; honor `LOCAL_DATA_POLICY` and `list_local_data` / `offer_use_local_data` (see server instructions).
3. **Register via wrapper only** — Use `register_tool` from [`tools/_register.py`](../mcp/oracle_cpq_mcp/tools/_register.py). Never bypass sanitize, stamp, or output validation.
4. **CPQClient only** — All CPQ HTTP goes through `CPQClient`. No ad-hoc `httpx` / `requests` in tool handlers. (Exception: IDCS OAuth via `security/fusion_oauth.py` for `mode: fusion` / `get_fusion_access_token`.)
5. **Response envelope** — Handlers return raw/paginated data (or attachment lists). The wrapper supplies `{status, tool, data, ...}` plus `environment`, `customer_id`, `retrieved_at`.
6. **Safe errors** — LLM-facing `details` must not include raw CPQ `body`, `curl`, or credentials (including OAuth client secrets / access tokens).
7. **Pagination / truncation** — Page tools use `enrich_pagination_hint`. Bulk/export tools surface `truncated` / `has_more` / caps to the LLM.
8. **Writes** — Default `dry_run=True`, confirmation token for apply, respect profile `READ_ONLY`.
9. **Tests + manifest** — Add/update unit and contract tests. Regenerate `mcp/oracle_cpq_mcp/security/tool_manifest.json` when the catalog changes. Refresh the formal GitHub tool tables with `python scripts/generate_tool_catalog.py` → [`TOOL_CATALOG.md`](TOOL_CATALOG.md).
10. **Product scope** — No inventing quote totals, pricing, or approval outcomes. Dedicated transaction write tools (e.g. `submit_transaction`) may exist — use them with dry-run/confirmation; still do not invent CPQ results.

### Profile mode (`cpq` vs `fusion`)

- Default `mode: cpq` (or omit): Basic Auth + `/rest/{version}`.
- `mode: fusion`: OAuth client credentials + Bearer + `/cpq/rest/{version}`; per-env `oauth_*` fields required; username/password unused. Sample: [`.config/example_fusion.yaml`](../.config/example_fusion.yaml).
- Agents never edit `oauth_client_id` / `oauth_client_secret` (same rule as passwords). Use MCP `get_fusion_access_token` when a token is needed explicitly.
- Formal catalog tables list both **CPQ REST URL** and **Fusion REST URL** (regenerate with `python scripts/generate_tool_catalog.py`).

## New tool checklist

Copy [`templates/NEW_TOOL.md`](templates/NEW_TOOL.md) and [`templates/tool_scaffold.py.example`](templates/tool_scaffold.py.example).

## Prefer MCP and shared CLIs (no one-off scripts)

For customer/site work in any IDE:

- **CPQ data** — Oracle CPQ MCP tools only (`list_*`, `get_*`, `sync_*_local`, `load_local_data`, …). Never ad-hoc REST with profile credentials.
- **Tabular / branded exports** — `export_response_excel` / `export_response_word` (and post-response export policy). Do not write new `tmp/.../write_*.py` helpers when MCP export already applies.
- **Scratch** — intermediate JSON/MD under `tmp/{profile}/{env}/` only when a tool cannot express the step; reuse `oracle_cpq_mcp.exporters` if you must script locally.
- **Maintainer tasks** — installable CLI after `pip install -e .`:

```bash
oracle-cpq migrate-yaml <id>
oracle-cpq lint-schemas
oracle-cpq generate-tool-catalog
# wrappers still work: python scripts/lint_tool_schemas.py …
```

`utilities/` one-offs (`lookup_user`, email compares) are optional; prefer MCP `list_users` / `get_user` in the IDE.

## Automated gates

```bash
# Schema lint (Field descriptions, catalog ↔ input model parity)
oracle-cpq lint-schemas
# or: python scripts/lint_tool_schemas.py

# Formal per-tool catalog for GitHub (docs/TOOL_CATALOG.md)
oracle-cpq generate-tool-catalog
# or: python scripts/generate_tool_catalog.py

# Unit + contract + offline evals (skip live sandbox)
pytest tests/ -q -m "not live_eval"
```

Offline known-answer cases: [`tests/evals/cases.json`](../tests/evals/cases.json).

Optional pre-commit: see [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) (`pip install pre-commit && pre-commit install`).

### Live coverage note

Passing offline tests does **not** mean a tool has been smoke-tested on a customer CPQ site. Scope C additions (tasks, configuration/productFamilies, datatable create/export, BML extensions) are documented as **untested (live)** in [`README.md`](../README.md#testing-status-live-cpq) until Focalpoint (or another site) verification is done.

### Live eval (optional)

```bash
# Requires CPQ profile credentials and a sandbox site
set CPQ_LIVE_EVAL=1
set CPQ_CUSTOMER_PROFILE=focalpoint
pytest tests/evals/test_eval_live.py -m live_eval -q
```

## Related

- Portable agent entry: [`AGENTS.md`](../AGENTS.md) (all IDEs)
- MCP instructions SSOT: [`prompts/instructions.py`](../mcp/oracle_cpq_mcp/prompts/instructions.py) (`build_server_instructions`)
- Template: [`templates/NEW_TOOL.md`](templates/NEW_TOOL.md)
- Compliance prompt: [`prompts/compliance_check.md`](../prompts/compliance_check.md)
- Cursor mirrors (Cursor only): [`.cursor/rules/`](../.cursor/rules/)
