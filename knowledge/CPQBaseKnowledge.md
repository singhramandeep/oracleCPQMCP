# CPQ base knowledge (all customers)

Follow these rules on every engagement unless the user explicitly overrides them.

## Safety and credentials

- Never put CPQ passwords, confirmation secrets, or raw `.env` contents in chat or commits.
- Profiles default to `READ_ONLY=true`. Do not attempt create/update/deploy unless the profile allows writes and the user confirms.
- Mutating tools use dry-run preflight first, then require a server `confirmation_token` before apply.

## Tooling habits

- Prefer `discover_tools` when unsure which MCP tool to use.
- Before large list/export work (users, groups, BML, commerce metadata, datatables), honor `LOCAL_DATA_POLICY` and check local `data/{profile}/{env}/` snapshots.
- When the user says “use cached data” or “fresh data”, follow that over the default policy.

## Property aliases

- Profile `.env` may define friendly aliases (e.g. `COMMERCE_PROCESS_ALIAS=base commerce process` paired with `COMMERCE_PROCESS_VAR_NAME=oraclecpqo`).
- When the user refers to an alias phrase, resolve it to the mapped variable name for tool arguments.
- Same pattern applies to data tables (`CUSTOM_DATA_TABLE_ALIAS` ↔ `CUSTOM_DATA_TABLE_NAME`).

## Knowledge

- Shared guidance lives in this file; customer-specific notes load from `knowledge/{CUSTOMER_KNOWLEDGE_FILE}` when set on the profile.
- After changing knowledge markdown or alias keys, reload the MCP server so instructions refresh.
