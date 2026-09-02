# Live smoke honesty matrix

Machine-readable guidance for agents and humans: which Oracle CPQ MCP surfaces have been exercised against a live site vs offline-only coverage.

Package: **0.3.0**. Offline unit/contract tests cover the full catalog. Live status below is the **source of truth** for agent honesty (also summarized in server instructions).

| Area | Tools / path | Live status | Notes |
|------|----------------|-------------|--------|
| Users / groups | list/get/export/update, groups | **Used live** | Core path |
| Datatables read/deploy | list/get/rows/deploy | **Used live** | create/export **untested** |
| BML zip / local extract | `get_all_bml_code`, `start_bml_site_export` | **Partial** | Large sites timeout without async/job + raised `HTTP_TIMEOUT` |
| BML util JSON | `get_all_bml_code(json)`, `sync_bml_local` | **Partial** | N+1 GETs; prefer cache |
| BML live search | `search_bml_scripts` | **May 404** | Prefer `search_local_bml` after extract |
| Local BML search | `search_local_bml` | **Offline OK** | Needs `data/.../bml/site/` |
| Commerce metadata / txns | attributes, transactions, … | **Used live** | |
| Metrics / collab / UI settings | list_metrics, collab, commerceUISettings | **v19 preferred** | v18 may 404 |
| Saved searches / admin | searchResources, certificates, SSO | **v19 preferred** | PEM redacted |
| Parts | list/get/search | **Used live** | |
| Performance logs | list/get/export | **Used live** | |
| Tasks | `get_task`, `download_task_file` | **Untested live** | Needed after export_* taskId |
| Configuration | productFamilies / layoutcache | **Untested live** | |
| Meta / local data / prompts | discover, sync_*, prompts, exports | **Local / used** | |

## Agent rules

1. If live status is untested or v19-only, say so; do not invent success.
2. Prefer `list_local_data` / `cpq://local` / `search_local_bml` before re-fetching huge BML.
3. Long BML: `start_bml_site_export` → `get_local_job` loop (not one blocking `get_all_bml_code` when hosts time out).
4. CPQ async exports: `export_*` → `get_task` → `download_task_file`.

Update this file when live smoke results change.
