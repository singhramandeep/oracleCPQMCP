# Focalpoint — customer knowledge

Site-specific notes for the Focalpoint CPQ profile. Shared rules still apply from `CPQBaseKnowledge.md`.

## Commerce

- Primary / “base” commerce process variable name is typically `oraclecpqo` (confirm via profile `COMMERCE_PROCESS_VAR_NAME` and `COMMERCE_PROCESS_ALIAS`).
- When the user says **base commerce process** (or the configured alias), use that mapped process var name in commerce and transaction tools.

## Data tables

- Common default table on this site includes `ModelMaster` (see profile `CUSTOM_DATA_TABLE_NAME` / `CUSTOM_DATA_TABLE_ALIAS`).
- BML under `data/focalpoint/{env}/bml/site/` may reference ModelMaster via util libraries (`getModelMasterDetails`, punch-in URL helpers) and commerce libraries such as `fetchConfigAttributesFromLine`.

## Conventions

- Host company for groups is usually `_host` (`COMPANY_LOGIN_NAME`).
- Prefer local BML extract under `data/focalpoint/{env}/bml/site/` for offline impact analysis when a fresh zip is not required.
