# CPQ base knowledge (all customers)

Engagement tips (credentials / scratch / READ_ONLY live in MCP server instructions).

## Tooling

- Prefer `discover_tools` when unsure which tool to use (`cx_module=sales|prm` for Fusion CX).
- Before large list/export, honor `LOCAL_DATA_POLICY` and check `data/{profile}/{env}/`.
- User “use cached data” / “fresh data” overrides the policy for that turn.
- Partner LookupCode values: `list_partner_lov` (do not invent Meaning).

## Property aliases

- Friendly phrases from the profile (e.g. “base commerce process”) map to CPQ var names in tool args — honor the Property aliases section injected with MCP instructions.
- Reload MCP after changing knowledge markdown or alias keys.
