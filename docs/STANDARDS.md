# Oracle CPQ MCP — Tool Authoring Standards

Day-to-day checklist for adding or changing MCP tools. Historical findings live in [`others/AUDIT_REPORT.md`](others/AUDIT_REPORT.md). After any tool change, run the compliance prompt: [`prompts/compliance_check.md`](../prompts/compliance_check.md).

## Non-negotiables

1. **Typed inputs** — Every tool has a `_StrictModel` in [`security/validation.py`](../mcp/oracle_cpq_mcp/security/validation.py) with `extra="forbid"`. Every field uses `Field(..., description="...")`.
2. **Catalog entry** — Add a `ToolSpec` in [`registry/tool_registry.py`](../mcp/oracle_cpq_mcp/registry/tool_registry.py). Descriptions must cover pagination / empty results / “does not” scope where relevant.
3. **Register via wrapper only** — Use `register_tool` from [`tools/_register.py`](../mcp/oracle_cpq_mcp/tools/_register.py). Never bypass sanitize, stamp, or output validation.
4. **CPQClient only** — All CPQ HTTP goes through `CPQClient`. No ad-hoc `httpx` / `requests` in tool handlers.
5. **Response envelope** — Handlers return raw/paginated data (or attachment lists). The wrapper supplies `{status, tool, data, ...}` plus `environment`, `customer_id`, `retrieved_at`.
6. **Safe errors** — LLM-facing `details` must not include raw CPQ `body`, `curl`, or credentials.
7. **Pagination / truncation** — Page tools use `enrich_pagination_hint`. Bulk/export tools surface `truncated` / `has_more` / caps to the LLM.
8. **Writes** — Default `dry_run=True`, confirmation token for apply, respect profile `READ_ONLY`.
9. **Tests + manifest** — Add/update unit and contract tests. Regenerate `mcp/oracle_cpq_mcp/tool_manifest.json` when the catalog changes.
10. **Product scope** — No quotes, pricing, or approvals unless new tools exist. Do not invent those answers.

## New tool checklist

Copy [`templates/NEW_TOOL.md`](templates/NEW_TOOL.md) and [`templates/tool_scaffold.py.example`](templates/tool_scaffold.py.example).

## Automated gates

```bash
# Schema lint (Field descriptions, catalog ↔ input model parity)
python scripts/lint_tool_schemas.py

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

- Template: [`templates/NEW_TOOL.md`](templates/NEW_TOOL.md)
- Compliance prompt: [`prompts/compliance_check.md`](../prompts/compliance_check.md)
- Cursor rules: [`.cursor/rules/`](../.cursor/rules/)
