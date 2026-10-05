# Release notes

Changelog for the **Oracle CPQ MCP** server. Format inspired by [Keep a Changelog](https://keepachangelog.com/).  
Package version today: **`0.3.0`** (see [`pyproject.toml`](../pyproject.toml)).

Related docs: [FEATURES.md](FEATURES.md) · [FAQ.md](FAQ.md) · [TOOL_CATALOG.md](TOOL_CATALOG.md) · [LIVE_SMOKE_MATRIX.md](LIVE_SMOKE_MATRIX.md) · [SETUP.md](SETUP.md) · [QUICKSTART.md](QUICKSTART.md) · [UPGRADE.md](UPGRADE.md) · [SECURITY.md](../SECURITY.md) · [README — Update the package version](../README.md#update-the-package-version)

## How to refresh

```bash
python scripts/update_release_notes.py
```

The script regenerates **only** the git-backed list between `<!-- git-commits -->` markers from `git log` (idempotent). A **pre-commit** hook runs the same command; if the file changes, re-stage `docs/RELEASE_NOTES.md` and commit again.

Narrative sections above the markers are **hand-maintained** — update them when you ship meaningful features (do not rely on commit subjects alone).

## How to cut a versioned release

See also the contributor checklist in the [README](../README.md#update-the-package-version).

1. Bump `version` in [`pyproject.toml`](../pyproject.toml).
2. Move the current Unreleased **Highlights / Added / Changed / …** blocks under a new heading such as `## [0.3.0] - YYYY-MM-DD`.
3. Leave a fresh Unreleased section and keep the standalone git-commits HTML comment markers for future commits.
4. If tools changed: regenerate `tool_manifest.json` and `docs/TOOL_CATALOG.md`, then run tests.
5. Commit and optionally tag: `git tag v0.3.0`.

---

## Unreleased

Package remains **`0.3.0`**; Prompt Studio app is **`0.4.3`**. Catalog is now **157** tools (`cx_module`: 101 `cpq` + 25 `meta` + 14 `sales` + 17 `prm`). Reload / restart Oracle CPQ MCP after pull so new CX tools and instruction text appear. Cursor’s MCP panel may also list a host `mcp_auth` helper — that name is **not** in the Oracle catalog.

### Summary (this wave)

| Area | What shipped |
|------|----------------|
| **Fusion CX Sales** | 14 GET tools (territories, accounts + account team, contacts, leads + lead opportunities, products) |
| **Fusion CX PRM** | 17 GET tools (partners, partner LOV, contacts, deals, programs, partner-contact children) |
| **CX runtime** | `CXClient` + `tools/cx/` package; register only enabled `cx.modules` |
| **Partner codes** | `list_partner_lov` maps LookupCode → Meaning/DisplayLabel |
| **Protocol** | `register_tool` passes FastMCP `name=`; contract tests cover CX + knowledge |
| **Docs** | FEATURES / FAQ / README / SETUP / QUICKSTART / LIVE_SMOKE / STANDARDS + Mermaid architecture diagrams |

### Highlights

#### Fusion CX Sales + PRM (catalog 157)

- **CX tools package:** handlers under [`mcp/oracle_cpq_mcp/tools/cx/`](../mcp/oracle_cpq_mcp/tools/cx/) (`sales.py`, `prm.py`, shared `_common.py`). `register_cx_tools` registers **only** YAML-enabled `cx.modules`. Catalog `cx_module` slugs match `FUSION_MODULE_SLUGS` (`sales`, `prm`, …). HTTP goes through [`CXClient`](../mcp/oracle_cpq_mcp/core/cx_client.py) to `{cx.url}/crmRestApi/resources/11.13.18.05/…` (ADF collection params: `q`, `finder`, `fields`, `orderBy`, `limit`, `offset`, `onlyData`, `totalResults`, `expand`).
- **Sales (14 GET):** `list_territories` / `get_territory`; `list_accounts` / `get_account`; `list_account_team` / `get_account_team_member`; `list_contacts` / `get_contact`; `list_leads` / `get_lead`; `list_lead_opportunities` / `get_lead_opportunity`; `list_products` / `get_product`. Requires `cx.enabled` and `Sales` in `cx.modules`.
- **PRM (17 GET):** `list_partners` / `get_partner`; **`list_partner_lov`**; `list_partner_contacts` / `get_partner_contact`; `list_deals` / `get_deal`; `list_partner_programs` / `get_partner_program`; partner-contact children — addresses, attachments, contact points, user details (`list_*` + `get_*` each). Requires `PRM` in `cx.modules`. Partners are keyed by **CompanyNumber** (not display name).
- **`list_partner_lov`:** GET `partners/{CompanyNumber}/lov/{LovName}` to resolve partner LookupCode values to Meaning/DisplayLabel after `list_partners` / `get_partner`. Convention: field `PartnerProfilePEO_<suffix>` → `lov_name=PartnerProfilePEO_LOVVA_For_<suffix>`. Optional `lookup_code` sets `q=LookupCode="…"` when `q` is omitted. Do not invent `lov_name`; if unknown, `get_partner(only_data=false)` and follow `rel=lov` links. MCP instructions + Cursor mirror tell agents to resolve codes before user-facing status answers.
- **Module gating:** Service / Field Service / Subscription / Incentive Compensation remain **allowlist names only** (no handlers yet). Filter with `discover_tools(domain=…)` or `discover_tools(cx_module=sales|prm)`.
- **Live honesty:** Sales/PRM GETs exercised on Fusion CX; some ADF `q` / `fields`+`expand` combinations return 400 — see [`LIVE_SMOKE_MATRIX.md`](LIVE_SMOKE_MATRIX.md).

#### Profile / clients / agent policy

- **Dual CPQ + CX Fusion profile YAML (format 1.06):** nested `environments.<env>.cpq` and `cx` blocks, each with its own URL and `auth: basic` (default) or `bearer`. CX `modules` required when CX is enabled. Legacy flat env + `cpq_mode` still migrate. Samples: [`.config/example.yaml`](../.config/example.yaml), [`.config/example_fusion.yaml`](../.config/example_fusion.yaml).
- **`fusion_modules` / `cx.modules` (format 1.05+):** YAML list of Fusion CX modules. **Sales** and **PRM** now register GET tools; other allowlisted names remain reserved. Host `CPQ_FUSION_MODULES`.
- **Fusion-hosted CPQ:** nested `cpq.hosted: fusion` + `cpq.auth: bearer` → OAuth Bearer + `/cpq/rest/{version}` for CPQ REST via `CPQClient` (same tools as standalone). Legacy `cpq_mode` / `fusion_enabled` still migrate.
- **Customer knowledge memory:** `get_customer_knowledge` / `ensure_customer_knowledge` / `append_customer_knowledge` persist engagement discoveries under `knowledge/{customer_id}.md`; profile `customer_knowledge_file` auto-wired via ensure. Reload MCP so the next chat injects updated knowledge.
- **Agent instruction compression + frugal_mode:** `build_server_instructions` shortened; `frugal_mode` / `CPQ_FRUGAL_MODE` forces refined footer / post-response export / Prompt Studio ensure off.
- **Tool catalog columns:** each tool lists **CPQ REST URL** and **Fusion REST URL**. Sales/PRM put the CRM path in the Fusion column and mark the CPQ column as not-CPQ (regenerate with `python scripts/generate_tool_catalog.py`).
- Branded Word/Excel/PPT exports via `.config/template/` + Mermaid diagrams in analytical Word exports (local `mmdc`).
- Prompt Studio **0.4.3+** (ratings, API logs, Profiles & Paths, version badge). Agents call `ensure_prompt_studio` after YES-gate CPQ work.
- Unified customer profile YAML; maintainer CLI `oracle-cpq`; defaults `local_data_policy=prefer`, `post_response_export=always_excel`.

#### Documentation (CX wave)

- Updated for **157** tools and live Sales/PRM: [`FEATURES.md`](FEATURES.md), [`FAQ.md`](FAQ.md), [`README.md`](../README.md), [`SETUP.md`](SETUP.md), [`QUICKSTART.md`](QUICKSTART.md), [`UPGRADE.md`](UPGRADE.md), [`LIVE_SMOKE_MATRIX.md`](LIVE_SMOKE_MATRIX.md), [`STANDARDS.md`](STANDARDS.md), [`COMMON_PROMPTS.md`](COMMON_PROMPTS.md), [`PRE_COMMIT_REVIEW.md`](PRE_COMMIT_REVIEW.md), [`templates/NEW_TOOL.md`](templates/NEW_TOOL.md), [`AGENTS.md`](../AGENTS.md), [`knowledge/CPQBaseKnowledge.md`](../knowledge/CPQBaseKnowledge.md).
- Mermaid diagrams for CPQ vs CX clients, module gating, partner LOV resolve, customer-knowledge reload, and YAML `cpq`/`cx` split.
- FAQ: how to resolve partner LookupCode; why Cursor may show fewer than 157 tools; `discover_tools` accepts `sales` / `prm` / `cx_module`.
- Example profile comments no longer say CX is “helper only”.

### Added

#### Fusion CX

- [`mcp/oracle_cpq_mcp/core/cx_client.py`](../mcp/oracle_cpq_mcp/core/cx_client.py) — Fusion CX REST client (Basic/Bearer from nested `cx:`).
- [`mcp/oracle_cpq_mcp/tools/cx/`](../mcp/oracle_cpq_mcp/tools/cx/) — `sales.py` (14), `prm.py` (17), `_common.py` (ADF collection helpers / CRM version).
- **Sales tools:** `list_territories`, `get_territory`, `list_accounts`, `get_account`, `list_account_team`, `get_account_team_member`, `list_contacts`, `get_contact`, `list_leads`, `get_lead`, `list_lead_opportunities`, `get_lead_opportunity`, `list_products`, `get_product`.
- **PRM tools:** `list_partners`, `get_partner`, `list_partner_lov`, `list_partner_contacts`, `get_partner_contact`, `list_deals`, `get_deal`, `list_partner_programs`, `get_partner_program`, `list_partner_contact_addresses`, `get_partner_contact_address`, `list_partner_contact_attachments`, `get_partner_contact_attachment`, `list_partner_contact_contact_points`, `get_partner_contact_contact_point`, `list_partner_contact_user_details`, `get_partner_contact_user_detail`.
- Typed inputs in `security/validation.py` (CX ADF collection models + `ListPartnerLovInput` with path-safe `lov_name`).
- ToolSpecs with `cx_module=sales|prm`, `http_method=GET`, `/crmRestApi/resources/11.13.18.05/…` paths; manifest regenerated (tool_count **157**).
- Unit tests: `tests/test_sales_tools.py`, `tests/test_prm_tools.py`, `tests/test_cx_client.py`; contract kwargs for all CX + customer-knowledge tools in `tests/test_tool_contracts.py`.
- MCP instructions: Fusion modules section + PRM LOV resolve rule; Cursor mirror `.cursor/rules/cpq-mcp-core.mdc`.

#### Earlier Unreleased (still shipping)

- `oracle_cpq_mcp.exporters.branded_documents` and `mermaid_render` (clone templates; local Mermaid PNG).
- Word `diagrams` on `export_response_word`; lightweight structured `notes` (`##` / bullets); center-aligned diagram images/captions; tall-diagram height cap.
- Cross-IDE agent policy in `AGENTS.md` + MCP `DOCUMENT_TEMPLATES` (Mermaid expected for analytical Word without user ask).
- Prompt Studio profile stamp/filter (`SavedPrompt.profile`, `GET /api/profiles`, toolbar select); restart scripts `scripts/restart-prompt-studio.*`.
- MCP tools `list_product_hierarchy_table` and `list_commerce_processes_table` (flat variable-name tables).
- MCP tool `ensure_prompt_studio` — probe/auto-start local Prompt Studio after YES-gate site/cache turns.
- MCP customer knowledge tools (`get_customer_knowledge`, `ensure_customer_knowledge`, `append_customer_knowledge`) — meta; local `knowledge/` only. Gitignore `knowledge/*` except `CPQBaseKnowledge.md`.
- [`mcp/oracle_cpq_mcp/core/profile_yaml.py`](../mcp/oracle_cpq_mcp/core/profile_yaml.py) full-document loader; [`scripts/migrate_profile_yaml.py`](../scripts/migrate_profile_yaml.py); [`.config/example.yaml`](../.config/example.yaml).
- `PyYAML` dependency and [`mcp/oracle_cpq_mcp/core/catalog.py`](../mcp/oracle_cpq_mcp/core/catalog.py) loader.
- Prompt Studio ratings/comments APIs; per-source `record_prompt_use` **1.1.0** (`duration_ms` + `source=cache|api|mixed`); Profiles & Paths APIs; Studio **0.4.1–0.4.3** UI (rating filter, version badge, autosize edit areas, Help).
- `export_response_word` catalog **1.2.0** — Mermaid `pie` / `xychart-beta` / `flowchart` guidance.
- Profile `frugal_mode` / host `CPQ_FRUGAL_MODE`; format **1.05** `fusion_modules` → **1.06** nested `cpq`/`cx`.

### Changed

- `register_tool` now passes FastMCP `name=<catalog name>` so handshake tool lists match `TOOL_CATALOG` (avoids silent `fn.__name__` drift).
- `discover_tools` filters by `cx_module` (`sales` / `prm` / `meta` / …); meta tools stay hidden unless requested.
- Catalog generator preamble documents nested `cpq.hosted` / CRM REST for Sales/PRM (not only legacy `cpq_mode` + `fusion_enabled`).
- MCP `build_server_instructions` compressed; knowledge / `AGENTS.md` / Cursor mirrors slimmed.
- Example profiles: CX comments updated — Sales/PRM are real GET tools (not “helper only”).
- Prompt Studio static cache-bust / list grid / Help / README (app **0.4.3+**); saved-prompt dedupe per content hash + profile.
- Profile template path renamed `.config/.profile.yaml.example` → `.config/example.yaml`.
- Doc counts and checklists (README / FEATURES / FAQ / PRE_COMMIT) updated **122/123/126 → 157**.

### Fixed

- Contract-test gap: CX Sales/PRM + customer-knowledge tools were in `TOOL_CATALOG` but missing from `tests/test_tool_contracts.py` (FakeCXClient + TOOL_KWARGS for all 34 names, including `list_partner_lov`).
- Cursor handshake could omit a newly added Oracle tool while still showing 157 names (host `mcp_auth` filling a slot) — mitigated by explicit FastMCP `name=` on register.
- Empty Word/Excel table rows when agents passed list-of-list sheet `rows` — `coerce_sheet_records` maps positional lists to column dicts.
- MCP startup fail-closed on stale `tool_manifest.json` after tool-description edits — regenerate via `write_manifest_file()`.
- Invalid profile YAML `local_data_policy: true` (bool) rejected by schema — must be `ask`|`prefer`|`never` (string).

### Documentation

- [`TOOL_CATALOG.md`](TOOL_CATALOG.md) regenerated (**157** tools; Sales/PRM domains; CRM REST in Fusion URL column).
- [`FEATURES.md`](FEATURES.md) — CX architecture Mermaid, partner LOV flow, customer-knowledge flow; catalog table **157**.
- [`FAQ.md`](FAQ.md) — CX coverage, `list_partner_lov` how-to, Cursor tool-count FAQ, `discover_tools` domains.
- [`LIVE_SMOKE_MATRIX.md`](LIVE_SMOKE_MATRIX.md) — Sales/PRM **Used live**; other CX modules **No tools yet**.
- [`QUICKSTART.md`](QUICKSTART.md) §6.12 Fusion CX sample prompts; SETUP/UPGRADE `cx.modules` wording.
- [`STANDARDS.md`](STANDARDS.md) / [`templates/NEW_TOOL.md`](templates/NEW_TOOL.md) — `CXClient`, catalog `name=`, contract coverage for CX.
- Doc sync tests: `tests/test_docs_tool_catalog.py` asserts FEATURES/FAQ catalog count + `list_partner_lov`.

### Git commits (auto-generated)

<!-- git-commits -->
- `01ee399` added CX tools
- `6da1c42` feature additions. fusion CPQ
- `47229e1` feature additions
- `c8ef795` feature additions
- `d004860` improved documentation
- `b5bba1d` generic improvements
- `3f86111` generic improvements
- `2b890d5` committed some leftovers
- `3f71082` Ship branded Word/Mermaid exports and Prompt Studio profile filter.
- `9afbe0c` add yaml support
- `62bcf6f` Ship 0.3.0 agent UX and Prompt Studio editing.
- `17d2b93` major feature addition
- `32f8320` major feature addition
- `f90354a` some documentation
- `d88bb7b` some documentation
- `2ee4c83` Added couple of tools, better prompt suggestios, prompt studio
- `fda086e` release notes
- `a1b39e2` release notes
- `c000974` Expand MCP catalog to 67 tools with tasks, configuration, parts, and transactions.
- `b3f0445` updated quickstart
- `b5c97c5` updated documentation
- `c05cd49` updated documentation
- `494b2ee` Restructure QUICKSTART for clearer first-time setup flow.
- `90bb92c` Add cross-platform MCP config, output validation, and doc sync for 19 tools.
- `62f1a29` Add MCP best-practice envelopes, annotations, and progress
- `df85397` Add JSON Schema output contracts for all MCP tools
- `0714bcb` Add commerce and line-level attribute and action metadata tools
- `130ba9b` Add get_all_bml_code MCP tool for BML export and util library source
- `ceaa2a6` first commit
<!-- /git-commits -->

---

## [0.3.0] - 2026-09-01

### Highlights

Agent-UX release: **async BML jobs**, **local cache resources**, **dual-env examples**, **capability/smoke honesty**, configurable HTTP timeouts. Catalog **103** tools.

| Area | What you get |
|------|----------------|
| Async BML | `start_bml_site_export` → poll `get_local_job` (avoids multi-minute MCP blocks) |
| Local search | `search_local_bml` over `data/.../bml/site/` |
| Resources | `cpq://local`, `cpq://local/bml/{path}` |
| Timeouts | Profile `HTTP_TIMEOUT` / host `CPQ_HTTP_TIMEOUT` (default 60s) |
| Dual env | `.cursor/mcp.json.dual.example.json` + Antigravity dual example; envelopes stamp `profile` |
| Honesty | [`LIVE_SMOKE_MATRIX.md`](LIVE_SMOKE_MATRIX.md) + capability card in server instructions |

### Added

- `start_bml_site_export`, `get_local_job`, `search_local_bml`
- MCP resources for local data index and BML file reads
- Dual-MCP config examples; FAQ async agent loop for BML/exports
- Configurable HTTP timeout (5–3600s)

### Changed

- Tool envelopes include `profile` (alias of `customer_id`) plus `environment`
- `get_all_bml_code` docs point agents at async job path for large sites
- Package version **0.3.0**

---

## [0.2.0] - 2026-08-26

### Highlights

**100 MCP tools**, local caching, reusable refined prompts, optional Prompt Studio, and stronger operator diagnostics.

| Area | What you get |
|------|----------------|
| Tool catalog | **100** tools — users, groups, datatables, BML, commerce (incl. saved searches), metrics, collab, **admin** (certificates/SSO), performance, parts, tasks, configuration, meta |
| Diagnostics | **DEBUG_MODE** file logging of redacted CPQ request traces under `logs/{profile}-{environment}.log` |
| Local cache | Snapshots under `data/{profile}/{env}/` with ask/prefer/never policy |
| Refined prompts | End-of-task footer + optional auto-save + picker |
| Prompt Studio | UI on **8765** — cards/list, favorites/suites, Run modal, **Download all** library JSON |
| Docs | FAQ, FEATURES, formal TOOL_CATALOG, contributor version-bump section in README |

### Added

#### This release focus

- Commerce **saved searches** — `list_saved_searches`, `get_saved_search` (`GET /searchResources/...`; resource defaults from commerce process var).
- Site **admin** domain — `list_certificates`, `get_certificate`, `get_sso_configuration`; PEM / IdP / SAML keystore fields redacted to `[REDACTED]`.
- Prompt Studio **Download all** — `GET /api/prompts/download` (full `.prompts/saved_prompts.json`; includes disabled by default).
- **DEBUG_MODE API file logging** — profile `DEBUG_MODE` (default `true`; host `CPQ_DEBUG_MODE` / `CPQ_DEBUG_LOG_DIR`). Appends timestamped, redacted request traces (curl + parameters) to `logs/{profile}-{environment}.log`. Passwords stay `***`; response bodies are not logged. Live `CPQClient` HTTP only (cache-only work writes nothing).
- Formal catalog at **100** tools ([`TOOL_CATALOG.md`](TOOL_CATALOG.md); regenerate: `python scripts/generate_tool_catalog.py`).

#### Catalog domains already in this line (summary)

Shipped earlier in the 0.1.x → 0.2.0 growth path (not re-listed as new APIs this week):

- Metrics (`list_metrics`), collab queues, commerce UI settings, transactions, performance logs, parts, tasks, configuration (`productFamilies`), broader BML/datatables, `discover_tools`.
- Refined-prompt footer + library tools; local `data/` sync policy; post-response Excel/Word export.
- BML zip + extract to `data/.../bml/site/`; Prompt Studio app; FAQ / FEATURES / pre-commit docs.

Details for those areas remain in [FEATURES.md](FEATURES.md) and the README domain summary.

### Changed

- README tool list slimmed to a **domain summary** (full per-tool tables live in TOOL_CATALOG).
- README adds **Update the package version** for contributors cutting releases.
- `.env.example` / server instructions cover DEBUG_MODE, refined prompts, local-data policy, post-response export.
- Schema integrity / `tool_manifest.json` updated for the 100-tool catalog.

### Security

- Default **`READ_ONLY=true`**; writes use dry-run + HMAC `confirmation_token`.
- Certificate/SSO PEM material never returned unredacted through MCP.
- Credentials never belong in MCP JSON — [SECURITY.md](../SECURITY.md).

### Known gaps / testing honesty

Offline unit/contract tests cover the catalog. Against **live** CPQ, still **untested**:

- Tasks (`get_task`, `download_task_file`)
- Configuration / `productFamilies` / layout cache
- Some newer BML extensions and datatable create/export writes
- Saved searches / certificates / SSO may 404 on sites still on REST **v18** (Oracle docs target **v19**)

**Dual environments:** one MCP process = one active env. For dev+test in one prompt, use two MCP entries or compare `data/{profile}/dev` vs `test` — [FAQ](FAQ.md#can-the-llm-connect-with-two-environments-at-the-same-time).

### Earlier milestones (summarized)

| Milestone | Summary |
|-----------|---------|
| Commerce metadata | Main + line attribute/action tools; process defaults from `COMMERCE_PROCESS_VAR_NAME` |
| BML export | `get_all_bml_code` zip + util-library JSON delivery |
| MCP quality | JSON Schema output contracts, envelopes/annotations/progress, schema integrity |
| Cross-platform MCP | Antigravity / Cursor / VS Code examples; `.cmd` + `.sh` launchers |
| Catalog growth | 67 → 87 → **100** tools |
| Quick setup (`SETUP.md`) | 8-step first-time path |
| Full setup guide (`QUICKSTART.md`) | Detailed install, MCP connect, samples |

### Git commits (through 0.2.0 cut)

<!-- git-commits-0.2.0 -->
- `d88bb7b` some documentation
- `2ee4c83` Added couple of tools, better prompt suggestios, prompt studio
- `fda086e` release notes
- `a1b39e2` release notes
- `c000974` Expand MCP catalog to 67 tools with tasks, configuration, parts, and transactions.
- `b3f0445` updated quickstart
- `b5c97c5` updated documentation
- `c05cd49` updated documentation
- `494b2ee` Restructure QUICKSTART for clearer first-time setup flow.
- `90bb92c` Add cross-platform MCP config, output validation, and doc sync for 19 tools.
- `62f1a29` Add MCP best-practice envelopes, annotations, and progress
- `df85397` Add JSON Schema output contracts for all MCP tools
- `0714bcb` Add commerce and line-level attribute and action metadata tools
- `130ba9b` Add get_all_bml_code MCP tool for BML export and util library source
- `ceaa2a6` first commit
<!-- /git-commits-0.2.0 -->

Note: the live auto-update script only rewrites the **Unreleased** `<!-- git-commits -->` block. Historical lists above are frozen for this release.
