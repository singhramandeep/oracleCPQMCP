# New tool checklist

Copy [`tool_scaffold.py.example`](tool_scaffold.py.example) pieces into the real modules. Do not import the example file.

## Steps

1. [ ] Add `ToolSpec` to `TOOL_CATALOG` in `mcp/oracle_cpq_mcp/registry/tool_registry.py` via `_spec(...)` with `description`, `title` (or accept name-derived default), `version="1.0.0"` (bump on later changes), and optional `icons` (else domain default)
2. [ ] Add `_StrictModel` subclass in `mcp/oracle_cpq_mcp/security/validation.py` — every field has `Field(..., description="...")`
3. [ ] Register the model in `TOOL_INPUT_MODELS`
4. [ ] Implement handler in `mcp/oracle_cpq_mcp/tools/<domain>.py` (or new domain module)
5. [ ] Call only `client.get` / `client.post` / `client.patch` / etc. via `CPQClient`
6. [ ] Return raw CPQ JSON or paginated payload (`enrich_pagination_hint` when applicable) — **do not** wrap the success envelope yourself
7. [ ] Set `fn.__doc__ = TOOL_CATALOG["name"].description` and `register_tool(mcp, fn, "name")`
8. [ ] Wire `register_<domain>_tools` from `server.py` if new domain
9. [ ] Add unit tests + ensure contract tests still cover the catalog name
10. [ ] Run `python scripts/lint_tool_schemas.py` and `pytest tests/ -q -m "not live_eval"`
11. [ ] Regenerate `tool_manifest.json` if catalog changed (`python -c "from oracle_cpq_mcp.security.schema_integrity import write_manifest_file; write_manifest_file()"` with `PYTHONPATH=mcp`)
12. [ ] Paste [`prompts/compliance_check.md`](../../prompts/compliance_check.md) into Cursor

When **changing** an existing tool: bump that tool’s `version` in `_spec(...)` before regenerating the manifest — lint fails if the definition hash changed and the version did not.
## Non-negotiables (scaffold already shows)

- Structured errors via raising / letting `_register` map exceptions — do not catch broadly to hide failures
- Explicit input schema with descriptions
- Freshness / env stamped by the wrapper (`retrieved_at`, `environment`, `customer_id`)
