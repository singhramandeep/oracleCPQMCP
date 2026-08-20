# Compliance check (post-change)

Use this **after any tool add/change**. Diff against [`docs/STANDARDS.md`](../docs/STANDARDS.md) only — do **not** re-run the full audit.

## Instructions

1. Inspect the current git diff (staged + unstaged) for tool-related paths:
   - `mcp/oracle_cpq_mcp/tools/**`
   - `mcp/oracle_cpq_mcp/registry/**`
   - `mcp/oracle_cpq_mcp/security/validation.py`
   - `mcp/oracle_cpq_mcp/schemas/**`
   - `mcp/oracle_cpq_mcp/core/responses.py`, `errors.py`, `pagination.py`
   - `tests/**` related to tools
2. Check each changed or new tool against the checklist below.
3. Reply with **Pass** or **Fail**. On Fail, list findings as `path:line — issue` only. No long prose.

## Checklist

- [ ] `TOOL_CATALOG` entry with clear description (pagination / empty / “does not” if needed)
- [ ] `_StrictModel` in `validation.py` with **every** field `Field(..., description="...")`
- [ ] Entry in `TOOL_INPUT_MODELS` matching catalog name
- [ ] Registered only via `register_tool` (no bypass of sanitize / stamp / output validate)
- [ ] All CPQ HTTP via `CPQClient` only
- [ ] Handler does not hand-roll success envelopes that skip wrapper stamping
- [ ] Errors do not expose raw `body` / `curl` / credentials to the LLM
- [ ] Paginated reads use `enrich_pagination_hint`; bulk paths surface truncation
- [ ] Writes: `dry_run` default + confirmation; `READ_ONLY` respected
- [ ] Tests updated (unit and/or contract); schema lint still passes
- [ ] `tool_manifest.json` regenerated if catalog changed
- [ ] Out of scope (quotes/pricing/approvals) not claimed without tools

## Suggested local commands

```bash
python scripts/lint_tool_schemas.py
pytest tests/test_schema_lint.py tests/test_tool_contracts.py -q
```
