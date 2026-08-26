# Keste — customer knowledge

Site-specific notes for the Keste CPQ profile. Shared rules still apply from `CPQBaseKnowledge.md`.

## Commerce

- Confirm the active process from profile `COMMERCE_PROCESS_VAR_NAME` and any `COMMERCE_PROCESS_ALIAS` entries.
- When the user uses an alias phrase (e.g. **base commerce process**), map it to the paired process variable name before calling commerce/transaction tools.

## Data tables

- Default / named tables come from `CUSTOM_DATA_TABLE_NAME` (+ `_1`, `_2`, …) and matching `CUSTOM_DATA_TABLE_ALIAS` values on the profile.
- Prefer cached snapshots under `data/keste/{env}/` when policy allows.

## Conventions

- Use `COMPANY_LOGIN_NAME` from the profile for company-scoped group APIs (often `_host`).
- Keep customer-specific runbooks and naming quirks in this file; reload MCP after edits.

Only use these common processes and ignore all others as they are junk: Hillman, General Motors , wholesale, Homebuilding
