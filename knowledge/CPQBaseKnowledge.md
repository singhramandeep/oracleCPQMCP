# CPQ base knowledge (all customers)

Follow these rules on every engagement unless the user explicitly overrides them.

## Safety and credentials

- Never put CPQ passwords, confirmation secrets, or raw `.env` contents in chat or commits.
- Never create, edit, delete, reformat, quote, or rewrite `username` / `password` (or `*_USERNAME` / `*_PASSWORD`) in `.config/*.yaml` or `.config/*.env`. The user alone owns credential changes. On 401 or profile-load failures, report the error — do not “fix” credentials.
- Live CPQ access must go only through Oracle CPQ MCP tools. Never use profile credentials for direct CPQ REST (curl, httpx, requests, or local `load_profile` + `CPQClient` / Basic auth for user tasks).
- Treat `.config/template/` as read-only for agents and MCP (open/clone only). Never create, overwrite, delete, or “fix” branding templates there; write new Office files under `data/{profile}/{env}/exports/`.
- Profiles default to `READ_ONLY=true`. Do not attempt create/update/deploy unless the profile allows writes and the user confirms.
- Mutating tools use dry-run preflight first, then require a server `confirmation_token` before apply.

## Tooling habits

- Prefer `discover_tools` when unsure which MCP tool to use.
- Before large list/export work (users, groups, BML, commerce metadata, datatables), honor `LOCAL_DATA_POLICY` and check local `data/{profile}/{env}/` snapshots.
- When the user says “use cached data” or “fresh data”, follow that over the default policy.
- Write agent scratch dumps (JSON/MD) under `tmp/{profile}/{env}/`, never at the repo root; when you create or update them, list the paths under **Scratch files** in the reply.

## Property aliases

- Profile `.env` may define friendly aliases (e.g. `COMMERCE_PROCESS_ALIAS=base commerce process` paired with `COMMERCE_PROCESS_VAR_NAME=oraclecpqo`).
- When the user refers to an alias phrase, resolve it to the mapped variable name for tool arguments.
- Same pattern applies to data tables (`CUSTOM_DATA_TABLE_ALIAS` ↔ `CUSTOM_DATA_TABLE_NAME`).

## Knowledge

- Shared guidance lives in this file; customer-specific notes load from `knowledge/{CUSTOMER_KNOWLEDGE_FILE}` when set on the profile.
- After changing knowledge markdown or alias keys, reload the MCP server so instructions refresh.
