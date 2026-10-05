"""Central catalog and search/filter helpers for Oracle CPQ MCP tools."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from mcp.types import Icon, ToolAnnotations

from oracle_cpq_mcp.registry.tool_icons import IconSpec, resolve_tool_icons
from oracle_cpq_mcp.schemas.tool_outputs import get_tool_output_schema

DomainName = Literal[
    "users",
    "groups",
    "datatables",
    "bml",
    "commerce",
    "performance",
    "parts",
    "tasks",
    "configuration",
    "metrics",
    "collab",
    "admin",
    "sales",
    "prm",
    "service",
    "field_service",
    "subscription",
    "incentive_compensation",
    "meta",
]
OperationName = Literal["read", "write"]
# cpq/meta plus Fusion CX products (YAML cx.modules slugs).
CxModuleName = Literal[
    "cpq",
    "sales",
    "prm",
    "service",
    "field_service",
    "subscription",
    "incentive_compensation",
    "meta",
]
FUSION_CX_MODULE_NAMES: frozenset[str] = frozenset(
    {
        "sales",
        "prm",
        "service",
        "field_service",
        "subscription",
        "incentive_compensation",
    }
)
DomainFilter = Literal[
    "users",
    "groups",
    "datatables",
    "bml",
    "commerce",
    "performance",
    "parts",
    "tasks",
    "configuration",
    "metrics",
    "collab",
    "admin",
    "sales",
    "prm",
    "service",
    "field_service",
    "subscription",
    "incentive_compensation",
    "all",
]
OperationFilter = Literal["read", "write", "all"]
CxModuleFilter = Literal[
    "cpq",
    "sales",
    "prm",
    "service",
    "field_service",
    "subscription",
    "incentive_compensation",
    "meta",
    "all",
]
RiskLevel = Literal[
    "READ_ONLY",
    "LOW_RISK_WRITE",
    "HIGH_RISK_WRITE",
    "DESTRUCTIVE",
    "PRIVILEGED",
]

DRY_RUN_DESCRIPTION_SUFFIX = (
    " Safe execution: defaults to dry_run=true (preflight only — validates inputs, "
    "checks existence via read-only GETs, returns a preview stating this will UPDATE/CREATE/DEPLOY). "
    "Ask the user to confirm before applying. Mutation requires dry_run=false and a valid "
    "confirmation_token from preflight. Blocked entirely when profile READ_ONLY=true (default)."
)


@dataclass(frozen=True)
class ToolSpec:
    """Metadata for one MCP tool."""

    name: str
    domain: DomainName
    operation: OperationName
    description: str
    tags: frozenset[str]
    read_only: bool
    title: str
    version: str
    icons: tuple[IconSpec, ...]
    cx_module: CxModuleName = "cpq"
    destructive: bool = False
    http_method: str | None = None
    api_path: str | None = None
    risk: RiskLevel = "READ_ONLY"


def human_tool_title(name: str) -> str:
    """Convert snake_case tool names into MCP annotation titles."""
    special = {"bml": "BML", "cpq": "CPQ", "excel": "Excel"}
    return " ".join(special.get(part, part.capitalize()) for part in name.split("_"))


def _compute_risk(
    name: str,
    *,
    operation: OperationName,
    destructive: bool,
) -> RiskLevel:
    if name in {
        "export_users_excel",
        "get_all_bml_code",
        "sync_users_local",
        "sync_groups_local",
        "sync_bml_local",
        "sync_commerce_metadata_local",
        "sync_datatable_local",
        "sync_datatables_local",
    }:
        return "PRIVILEGED"
    if destructive:
        return "DESTRUCTIVE"
    if operation == "write":
        return "HIGH_RISK_WRITE"
    return "READ_ONLY"


def _spec(
    name: str,
    *,
    domain: DomainName,
    operation: OperationName,
    description: str,
    tags: set[str],
    read_only: bool,
    destructive: bool = False,
    http_method: str | None = None,
    api_path: str | None = None,
    title: str | None = None,
    version: str = "1.0.1",
    icons: tuple[IconSpec, ...] | None = None,
    cx_module: CxModuleName | None = None,
) -> ToolSpec:
    resolved_module: CxModuleName = (
        cx_module if cx_module is not None else ("meta" if domain == "meta" else "cpq")
    )
    merged_tags = frozenset({domain, operation, resolved_module, *tags})
    resolved_title = (title or human_tool_title(name)).strip()
    resolved_icons = resolve_tool_icons(domain, icons)
    return ToolSpec(
        name=name,
        domain=domain,
        operation=operation,
        description=description,
        tags=merged_tags,
        read_only=read_only,
        title=resolved_title,
        version=version,
        icons=resolved_icons,
        cx_module=resolved_module,
        destructive=destructive,
        http_method=http_method,
        api_path=api_path,
        risk=_compute_risk(name, operation=operation, destructive=destructive),
    )


TOOL_CATALOG: dict[str, ToolSpec] = {
    "list_users": _spec(
        "list_users",
        domain="users",
        operation="read",
        description=(
            "List users across all companies on the CPQ site. Defaults to active users only. "
            "Returns one page of results. If hasMore is true, call again with "
            "offset = offset + limit. Use export_users_excel for a full Excel export."
        ),
        tags={"paginated"},
        read_only=True,
        http_method="GET",
        api_path="/users",
    ),
    "export_users_excel": _spec(
        "export_users_excel",
        domain="users",
        operation="read",
        description=(
            "Export CPQ users to an Excel (.xlsx) file. Defaults to active users only. "
            "Also writes users.json + users.xlsx under data/{profile}/{env}/users/."
        ),
        tags={"export", "excel", "local_data"},
        read_only=True,
        http_method="GET",
        api_path="/users",
        version="1.2.1",
    ),
    "get_user": _spec(
        "get_user",
        domain="users",
        operation="read",
        description="Get a single user by party number.",
        tags={},
        read_only=True,
        http_method="GET",
        api_path="/users/{partyNumber}",
    ),
    "get_user_groups": _spec(
        "get_user_groups",
        domain="users",
        operation="read",
        description=(
            "List all groups assigned to a user. Returns one page of results. "
            "If hasMore is true, call again with offset = offset + limit."
        ),
        tags={"paginated", "groups"},
        read_only=True,
        http_method="GET",
        api_path="/users/{partyNumber}/groups",
    ),
    "update_user": _spec(
        "update_user",
        domain="users",
        operation="write",
        description=(
            "Patch-update an existing user. Only include fields you intend to change."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation"},
        read_only=False,
        http_method="PATCH",
        api_path="/users/{partyNumber}",
    ),
    "list_groups": _spec(
        "list_groups",
        domain="groups",
        operation="read",
        description=(
            "List groups for the configured company (defaults to host company `_host`). "
            "Returns one page of results. If hasMore is true, call again with "
            "offset = offset + limit."
        ),
        tags={"paginated"},
        read_only=True,
        http_method="GET",
        api_path="/companies/{company}/groups",
    ),
    "get_group": _spec(
        "get_group",
        domain="groups",
        operation="read",
        description="Get details for a single group by its variable name.",
        tags={},
        read_only=True,
        http_method="GET",
        api_path="/companies/{company}/groups/{groupVarName}",
    ),
    "list_group_users": _spec(
        "list_group_users",
        domain="groups",
        operation="read",
        description=(
            "List users that belong to a group. Returns one page of results. "
            "If hasMore is true, call again with offset = offset + limit."
        ),
        tags={"paginated", "users"},
        read_only=True,
        http_method="GET",
        api_path="/companies/{company}/groups/{groupVarName}/users",
    ),
    "create_group": _spec(
        "create_group",
        domain="groups",
        operation="write",
        description=(
            "Create a new group for the configured company. Requires admin permissions."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation"},
        read_only=False,
        http_method="POST",
        api_path="/companies/{company}/groups",
    ),
    "list_datatables": _spec(
        "list_datatables",
        domain="datatables",
        operation="read",
        description=(
            "List data tables defined on the CPQ site. Returns one page of results. "
            "If hasMore is true, call again with offset = offset + limit."
        ),
        tags={"paginated"},
        read_only=True,
        http_method="GET",
        api_path="/datatables",
    ),
    "get_datatable": _spec(
        "get_datatable",
        domain="datatables",
        operation="read",
        description=(
            "Get metadata/properties for a data table. "
            "Defaults to the first CUSTOM_DATA_TABLE_NAME from profile "
            "(supports CUSTOM_DATA_TABLE_NAME_1, _2, etc.)."
        ),
        tags={},
        read_only=True,
        http_method="GET",
        api_path="/datatables/{tableName}",
    ),
    "get_datatable_rows": _spec(
        "get_datatable_rows",
        domain="datatables",
        operation="read",
        description=(
            "Get rows from a deployed data table. Defaults to the first "
            "CUSTOM_DATA_TABLE_NAME from profile (supports _1, _2 suffixes). "
            "Returns one page of results. If hasMore is true, call again with "
            "offset = offset + limit."
        ),
        tags={"paginated"},
        read_only=True,
        http_method="GET",
        api_path="/adminCustom{tableName}",
    ),
    "list_datatable_fields": _spec(
        "list_datatable_fields",
        domain="datatables",
        operation="read",
        description=(
            "List field definitions for a data table. Defaults table_name from profile. "
            "Returns one page of results. If hasMore is true, call again with "
            "offset = offset + limit."
        ),
        tags={"paginated"},
        read_only=True,
        http_method="GET",
        api_path="/datatables/{tableName}/fields",
    ),
    "get_datatable_field": _spec(
        "get_datatable_field",
        domain="datatables",
        operation="read",
        description=(
            "Get one data table field definition by field name. "
            "Defaults table_name from profile."
        ),
        tags={},
        read_only=True,
        http_method="GET",
        api_path="/datatables/{tableName}/fields/{fieldName}",
    ),
    "deploy_datatables": _spec(
        "deploy_datatables",
        domain="datatables",
        operation="write",
        description=(
            "Deploy one or more data tables. Admin-only — changes live CPQ configuration."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"admin", "dry_run", "confirmation"},
        read_only=False,
        destructive=True,
        http_method="POST",
        api_path="/datatables/actions/deploy",
    ),
    "create_datatable": _spec(
        "create_datatable",
        domain="datatables",
        operation="write",
        description=(
            "Create a new data table via POST /datatables. "
            "Requires name; optional description, folder, fields, isLive."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"admin", "dry_run", "confirmation"},
        read_only=False,
        http_method="POST",
        api_path="/datatables",
    ),
    "export_datatables": _spec(
        "export_datatables",
        domain="datatables",
        operation="write",
        description=(
            "Start a data table export task via POST /datatables/actions/export. "
            "Returns taskId; poll with get_task and download with download_task_file."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"admin", "dry_run", "confirmation", "export"},
        read_only=False,
        http_method="POST",
        api_path="/datatables/actions/export",
    ),
    "get_all_bml_code": _spec(
        "get_all_bml_code",
        domain="bml",
        operation="read",
        description=(
            "Download or retrieve BML source code from the CPQ site (synchronous — "
            "blocks the MCP tool call until done). "
            "delivery='zip' (default) exports all Commerce BML and BMLT files via "
            "GET /adminMeta — equivalent to cpq-toolkit pull; saves the zip under "
            "data/{profile}/{env}/bml/ and extracts the full folder tree to "
            "data/{profile}/{env}/bml/site/. "
            "delivery='json' returns util library functions with scriptText inline "
            "(paginated fetch of /bml/library/functions plus per-function detail) and "
            "writes library.json plus per-function .bml/.json under data/.../bml/. "
            "For large sites that exceed MCP/host timeouts, prefer "
            "start_bml_site_export + get_local_job instead of delivery=zip. "
            "Raise HTTP_TIMEOUT / CPQ_HTTP_TIMEOUT (seconds) if needed. "
            "Admin permissions required."
        ),
        tags={"export", "admin", "bml", "local_data"},
        read_only=True,
        http_method="GET",
        api_path="/adminMeta",
        version="1.4.1",
    ),
    "start_bml_site_export": _spec(
        "start_bml_site_export",
        domain="bml",
        operation="read",
        description=(
            "Start a background MCP-local job that downloads the full Commerce BML/BMLT "
            "site zip (GET /adminMeta), persists under data/{profile}/{env}/bml/, and "
            "extracts to bml/site/. Returns immediately with job_id. Poll with "
            "get_local_job until status is succeeded or failed. Prefer this over "
            "get_all_bml_code(delivery=zip) when the sync call times out. "
            "Does not use Oracle taskId (that path is export_bml_library_functions)."
        ),
        tags={"export", "bml", "local_data", "async"},
        read_only=True,
        http_method="GET",
        api_path="/adminMeta",
        version="1.0.1",
    ),
    "search_local_bml": _spec(
        "search_local_bml",
        domain="bml",
        operation="read",
        description=(
            "Search text across extracted local BML files under "
            "data/{profile}/{env}/bml/site/ (and util library .bml under bml/functions/). "
            "Does not call Oracle CPQ. Use after get_all_bml_code or start_bml_site_export "
            "has populated the cache. Prefer this when live search_bml_scripts 404s."
        ),
        tags={"bml", "search", "local_data"},
        read_only=True,
        version="1.0.1",
    ),
    "get_bml_function": _spec(
        "get_bml_function",
        domain="bml",
        operation="read",
        description=(
            "Get one util library BML function by function_id (namespace.variableName). "
            "Does not export full site zip."
        ),
        tags={"bml"},
        read_only=True,
        http_method="GET",
        api_path="/bml/library/functions/{namespace.variableName}",
    ),
    "search_bml_scripts": _spec(
        "search_bml_scripts",
        domain="bml",
        operation="read",
        description=(
            "Search BML scripts containing a string via GET /bml/scripts. "
            "Supports q_expr, limit, offset, orderby, fields."
        ),
        tags={"bml", "search", "paginated"},
        read_only=True,
        http_method="GET",
        api_path="/bml/scripts",
    ),
    "list_bml_common_functions": _spec(
        "list_bml_common_functions",
        domain="bml",
        operation="read",
        description=(
            "List built-in BML common functions (atoi, len, etc.) via "
            "GET /bml/common/functions."
        ),
        tags={"bml"},
        read_only=True,
        http_method="GET",
        api_path="/bml/common/functions",
    ),
    "get_bml_common_function": _spec(
        "get_bml_common_function",
        domain="bml",
        operation="read",
        description="Get one BML common function by name via GET /bml/common/functions/{name}.",
        tags={"bml"},
        read_only=True,
        http_method="GET",
        api_path="/bml/common/functions/{name}",
    ),
    "list_bml_library_folders": _spec(
        "list_bml_library_folders",
        domain="bml",
        operation="read",
        description="List util library folders via GET /bml/library/folders.",
        tags={"bml"},
        read_only=True,
        http_method="GET",
        api_path="/bml/library/folders",
    ),
    "get_bml_dependent_attributes": _spec(
        "get_bml_dependent_attributes",
        domain="bml",
        operation="read",
        description=(
            "Return attributes referenced by util library functions via "
            "POST /bml/library/functions/actions/dependentAttributes. "
            "Read-like; allowed under READ_ONLY."
        ),
        tags={"bml"},
        read_only=True,
        http_method="POST",
        api_path="/bml/library/functions/actions/dependentAttributes",
    ),
    "export_bml_library_functions": _spec(
        "export_bml_library_functions",
        domain="bml",
        operation="write",
        description=(
            "Export util library functions via POST .../actions/export. "
            "Returns taskId; use get_task and download_task_file."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"bml", "dry_run", "confirmation", "export"},
        read_only=False,
        http_method="POST",
        api_path="/bml/library/functions/actions/export",
    ),
    "get_task": _spec(
        "get_task",
        domain="tasks",
        operation="read",
        description=(
            "Get task status/details by task_id (e.g. after export_datatables). "
            "GET /tasks/{taskId}."
        ),
        tags={"tasks"},
        read_only=True,
        http_method="GET",
        api_path="/tasks/{taskId}",
    ),
    "download_task_file": _spec(
        "download_task_file",
        domain="tasks",
        operation="read",
        description=(
            "Download a file associated with a task (export zip/log). "
            "GET /tasks/{taskId}/files/{fileName}. Returns [envelope, File]."
        ),
        tags={"tasks", "export"},
        read_only=True,
        http_method="GET",
        api_path="/tasks/{taskId}/files/{fileName}",
    ),
    "list_product_families": _spec(
        "list_product_families",
        domain="configuration",
        operation="read",
        description="List product family metadata via GET /productFamilies.",
        tags={"configuration", "metadata"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies",
    ),
    "get_product_family": _spec(
        "get_product_family",
        domain="configuration",
        operation="read",
        description="Get one product family by prod_fam_var_name.",
        tags={"configuration", "metadata"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies/{prodFamVarName}",
    ),
    "list_product_lines": _spec(
        "list_product_lines",
        domain="configuration",
        operation="read",
        description="List product lines under a product family.",
        tags={"configuration", "metadata"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies/{prodFamVarName}/productLines",
    ),
    "get_product_line": _spec(
        "get_product_line",
        domain="configuration",
        operation="read",
        description="Get one product line by family + line variable names.",
        tags={"configuration", "metadata"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies/{prodFamVarName}/productLines/{prodLineVarName}",
    ),
    "list_models": _spec(
        "list_models",
        domain="configuration",
        operation="read",
        description="List models under a product family/line.",
        tags={"configuration", "metadata"},
        read_only=True,
        http_method="GET",
        api_path=(
            "/productFamilies/{prodFamVarName}/productLines/{prodLineVarName}/models"
        ),
    ),
    "list_product_hierarchy_table": _spec(
        "list_product_hierarchy_table",
        domain="configuration",
        operation="read",
        description=(
            "Walk all product families → lines → models and return a flat table of "
            "variable names and display names (one row per model; empty model "
            "columns when a family/line has no models). Pages CPQ collections. "
            "Does not write profile YAML. Soft-caps at 500 families "
            "(truncated=true when more exist)."
        ),
        tags={"configuration", "metadata", "table"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies/.../productLines/.../models",
    ),
    "get_model": _spec(
        "get_model",
        domain="configuration",
        operation="read",
        description="Get one model by family, line, and model variable names.",
        tags={"configuration", "metadata"},
        read_only=True,
        http_method="GET",
        api_path=(
            "/productFamilies/{prodFamVarName}/productLines/{prodLineVarName}"
            "/models/{modelVarName}"
        ),
    ),
    "list_config_attributes": _spec(
        "list_config_attributes",
        domain="configuration",
        operation="read",
        description=(
            "List configuration attributes at scope family|line|model "
            "(composite path under /productFamilies/.../attributes)."
        ),
        tags={"configuration", "attributes"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies/.../attributes",
    ),
    "get_config_attribute": _spec(
        "get_config_attribute",
        domain="configuration",
        operation="read",
        description=(
            "Get one configuration attribute at scope family|line|model "
            "by attribute_var_name."
        ),
        tags={"configuration", "attributes"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies/.../attributes/{attributeVarName}",
    ),
    "list_array_sets": _spec(
        "list_array_sets",
        domain="configuration",
        operation="read",
        description="List array sets at scope family|line|model.",
        tags={"configuration", "arraySets"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies/.../arraySets",
    ),
    "get_array_set": _spec(
        "get_array_set",
        domain="configuration",
        operation="read",
        description="Get one array set at scope family|line|model.",
        tags={"configuration", "arraySets"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies/.../arraySets/{arraySetVarName}",
    ),
    "list_array_set_attributes": _spec(
        "list_array_set_attributes",
        domain="configuration",
        operation="read",
        description="List attributes of an array set at scope family|line|model.",
        tags={"configuration", "arraySets", "attributes"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies/.../arraySets/{arraySetVarName}/attributes",
    ),
    "get_array_set_attribute": _spec(
        "get_array_set_attribute",
        domain="configuration",
        operation="read",
        description="Get one array-set attribute at scope family|line|model.",
        tags={"configuration", "arraySets", "attributes"},
        read_only=True,
        http_method="GET",
        api_path=(
            "/productFamilies/.../arraySets/{arraySetVarName}/attributes/{attributeVarName}"
        ),
    ),
    "list_config_menu_items": _spec(
        "list_config_menu_items",
        domain="configuration",
        operation="read",
        description=(
            "List menu items for an attribute or array-set attribute "
            "(parent_kind=attribute|array_set_attribute) at scope family|line|model."
        ),
        tags={"configuration", "menuItems"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies/.../menuItems",
    ),
    "get_config_menu_item": _spec(
        "get_config_menu_item",
        domain="configuration",
        operation="read",
        description=(
            "Get one menu item by menu_item_id for an attribute or array-set attribute "
            "at scope family|line|model."
        ),
        tags={"configuration", "menuItems"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies/.../menuItems/{menuItemId}",
    ),
    "get_config_layout": _spec(
        "get_config_layout",
        domain="configuration",
        operation="read",
        description=(
            "Get a configuration layout by layout_var_name at scope family|line|model."
        ),
        tags={"configuration", "layouts"},
        read_only=True,
        http_method="GET",
        api_path="/productFamilies/.../layouts/{layoutVarName}",
    ),
    "get_layout_cache_attributes": _spec(
        "get_layout_cache_attributes",
        domain="configuration",
        operation="read",
        description=(
            "Get layout-cache attributes for a model via "
            "GET /layoutcache/{fam}/{line}/{model}/attributes."
        ),
        tags={"configuration", "layouts"},
        read_only=True,
        http_method="GET",
        api_path="/layoutcache/{prodFamVarName}/{prodLineVarName}/{modelVarName}/attributes",
    ),
    "get_commerce_attributes": _spec(
        "get_commerce_attributes",
        domain="commerce",
        operation="read",
        description=(
            "Get metadata for attributes on a Commerce MAIN document "
            "(default doc_var_name='transaction' — not the line document). "
            "Returns one page of results (limit/offset). If hasMore is true, call again "
            "with offset = offset + limit. Defaults process_var_name from "
            "COMMERCE_PROCESS_VAR_NAME in profile. Set expand_all=true for translations. "
            "For line-level attributes use get_line_attributes instead."
        ),
        tags={"metadata", "commerce", "attributes", "paginated"},
        read_only=True,
        http_method="GET",
        api_path="/commerceProcesses/{processVarName}/documents/{docVarName}/attributes",
    ),
    "get_commerce_actions": _spec(
        "get_commerce_actions",
        domain="commerce",
        operation="read",
        description=(
            "Get metadata for actions on a Commerce MAIN document "
            "(default doc_var_name='transaction' — not the line document). "
            "Returns one page of results (limit/offset). If hasMore is true, call again "
            "with offset = offset + limit. Defaults process_var_name from "
            "COMMERCE_PROCESS_VAR_NAME in profile. Set expand_all=true for translations. "
            "For line-level actions use get_line_actions instead."
        ),
        tags={"metadata", "commerce", "actions", "paginated"},
        read_only=True,
        http_method="GET",
        api_path="/commerceProcesses/{processVarName}/documents/{docVarName}/actionDefs",
    ),
    "get_line_attributes": _spec(
        "get_line_attributes",
        domain="commerce",
        operation="read",
        description=(
            "Get metadata for attributes on a Commerce LINE document "
            "(default doc_var_name='transactionLine' — not the main/header document). "
            "Returns one page of results (limit/offset). If hasMore is true, call again "
            "with offset = offset + limit. Defaults process_var_name from "
            "COMMERCE_PROCESS_VAR_NAME in profile. Set expand_all=true for translations. "
            "For header attributes use get_commerce_attributes instead."
        ),
        tags={"metadata", "commerce", "attributes", "line", "paginated"},
        read_only=True,
        http_method="GET",
        api_path="/commerceProcesses/{processVarName}/documents/{docVarName}/attributes",
    ),
    "get_line_actions": _spec(
        "get_line_actions",
        domain="commerce",
        operation="read",
        description=(
            "Get metadata for actions on a Commerce LINE document "
            "(default doc_var_name='transactionLine' — not the main/header document). "
            "Returns one page of results (limit/offset). If hasMore is true, call again "
            "with offset = offset + limit. Defaults process_var_name from "
            "COMMERCE_PROCESS_VAR_NAME in profile. Set expand_all=true for translations. "
            "For header actions use get_commerce_actions instead."
        ),
        tags={"metadata", "commerce", "actions", "line", "paginated"},
        read_only=True,
        http_method="GET",
        api_path="/commerceProcesses/{processVarName}/documents/{docVarName}/actionDefs",
    ),
    "get_commerce_attribute": _spec(
        "get_commerce_attribute",
        domain="commerce",
        operation="read",
        description=(
            "Get one Commerce document attribute definition by attribute_var_name. "
            "Defaults process from profile, doc_var_name=transaction. "
            "Does not list all attributes (use get_commerce_attributes)."
        ),
        tags={"metadata", "commerce", "attributes"},
        read_only=True,
        http_method="GET",
        api_path=(
            "/commerceProcesses/{processVarName}/documents/{docVarName}"
            "/attributes/{attributeVarName}"
        ),
    ),
    "get_commerce_action": _spec(
        "get_commerce_action",
        domain="commerce",
        operation="read",
        description=(
            "Get one Commerce document action definition by action_var_name. "
            "Defaults process from profile. Does not list all actions."
        ),
        tags={"metadata", "commerce", "actions"},
        read_only=True,
        http_method="GET",
        api_path=(
            "/commerceProcesses/{processVarName}/documents/{docVarName}"
            "/actionDefs/{actionVarName}"
        ),
    ),
    "list_commerce_processes": _spec(
        "list_commerce_processes",
        domain="commerce",
        operation="read",
        description=(
            "List Commerce process setups (admin metadata). Paginated. "
            "Does not list live transactions."
        ),
        tags={"paginated", "metadata", "commerce"},
        read_only=True,
        http_method="GET",
        api_path="/commerceProcessSetups",
    ),
    "list_commerce_processes_table": _spec(
        "list_commerce_processes_table",
        domain="commerce",
        operation="read",
        description=(
            "List all Commerce process setups as a flat table with variable_name, "
            "name, description, id, and label. Pages until complete. "
            "Does not list live transactions."
        ),
        tags={"metadata", "commerce", "table"},
        read_only=True,
        http_method="GET",
        api_path="/commerceProcessSetups",
    ),
    "list_transactions": _spec(
        "list_transactions",
        domain="commerce",
        operation="read",
        description=(
            "List Commerce transactions for the configured process "
            "(GET /commerceDocuments{Process}{Doc}). Returns one page; if hasMore is true, "
            "call again with offset = offset + limit. Supports q_expr, fields, orderby, "
            "expand, exclude_field_types, total_results. Defaults process from "
            "COMMERCE_PROCESS_VAR_NAME and doc_var_name='transaction'. "
            "Does not create or modify quotes."
        ),
        tags={"paginated", "transactions"},
        read_only=True,
        http_method="GET",
        api_path="/commerceDocuments{Process}{Doc}",
    ),
    "get_transaction": _spec(
        "get_transaction",
        domain="commerce",
        operation="read",
        description=(
            "Get one Commerce transaction by numeric transaction_id. "
            "Optional expand / exclude_field_types. Defaults process from profile."
        ),
        tags={"transactions"},
        read_only=True,
        http_method="GET",
        api_path="/commerceDocuments{Process}{Doc}/{id}",
    ),
    "list_transaction_lines": _spec(
        "list_transaction_lines",
        domain="commerce",
        operation="read",
        description=(
            "List line items for a Commerce transaction. Paginated collection with the same "
            "filter params as list_transactions. Empty items means no lines for that id."
        ),
        tags={"paginated", "transactions", "lines"},
        read_only=True,
        http_method="GET",
        api_path="/commerceDocuments{Process}{Doc}/{id}/transactionLine",
    ),
    "get_transaction_line": _spec(
        "get_transaction_line",
        domain="commerce",
        operation="read",
        description=(
            "Get a single transaction line by transaction_id and document_number "
            "(line document number)."
        ),
        tags={"transactions", "lines"},
        read_only=True,
        http_method="GET",
        api_path="/commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}",
    ),
    "get_document_layout": _spec(
        "get_document_layout",
        domain="commerce",
        operation="read",
        description=(
            "Get Commerce desktop layout definition for a process document "
            "(panels, tabs, actions, attributes). Defaults process from profile and "
            "doc_var_name='transaction'. Does not return live quote data."
        ),
        tags={"metadata", "layout"},
        read_only=True,
        http_method="GET",
        api_path="/commerceProcesses/{processVarName}/layouts/{mainDocVarName}",
    ),
    "generate_proposal": _spec(
        "generate_proposal",
        domain="commerce",
        operation="write",
        description=(
            "Generate a proposal document for a Commerce transaction "
            "(POST .../actions/generateProposal)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/generateProposal",
    ),
    "export_attachment": _spec(
        "export_attachment",
        domain="commerce",
        operation="write",
        description=(
            "Export/view a CPQ-generated transaction attachment via REST "
            "(POST .../actions/{action_var_name}). Requires attribute_var_name "
            "(attachment attribute; sent as body selections). Returns JSON "
            "(documents/warnings); does not generate a new proposal "
            "(use generate_proposal) and does not download file bytes to disk."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}",
    ),
    "download_attachment": _spec(
        "download_attachment",
        domain="commerce",
        operation="read",
        description=(
            "Download file bytes for an existing transaction attachment attribute "
            "(e.g. proposalAttachment_t). Returns MCP File attachment. "
            "Does not generate a proposal (use generate_proposal) and does not call "
            "exportAttachment (use export_attachment)."
        ),
        tags={"transactions", "attachments"},
        read_only=True,
        http_method="GET",
        api_path="attachment fileLocation",
    ),
    "copy_transaction": _spec(
        "copy_transaction",
        domain="commerce",
        operation="write",
        description=(
            "Copy a Commerce transaction (POST .../actions/_copy_transaction)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/_copy_transaction",
    ),
    "copy_transaction_lines": _spec(
        "copy_transaction_lines",
        domain="commerce",
        operation="write",
        description=(
            "Copy transaction lines onto a Commerce transaction "
            "(POST .../actions/{action_name}; default action_name=copyLineItems_t)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "lines"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/{actionName}",
    ),
    "create_transaction": _spec(
        "create_transaction",
        domain="commerce",
        operation="write",
        description=(
            "Create a Commerce transaction/quote (POST /commerceDocuments{Process}{Doc}). "
            "Pass documents/attributes in body as required by the site."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "write"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}",
    ),
    "new_transaction": _spec(
        "new_transaction",
        domain="commerce",
        operation="write",
        description=(
            "Create a Commerce transaction via the _new_transaction action "
            "(POST .../actions/_new_transaction)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "write"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/actions/_new_transaction",
    ),
    "add_from_favorites": _spec(
        "add_from_favorites",
        domain="commerce",
        operation="write",
        description=(
            "Add favorites onto a Commerce transaction "
            "(POST .../actions/{action_var_name}; default _s_addFromFavorites_t)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "write"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}",
    ),
    "display_transaction_history": _spec(
        "display_transaction_history",
        domain="commerce",
        operation="write",
        description=(
            "Display transaction history via a site-specific action "
            "(POST .../actions/{action_var_name}; action_var_name required)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "write"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}",
    ),
    "save_transaction": _spec(
        "save_transaction",
        domain="commerce",
        operation="write",
        description=(
            "Save a Commerce transaction "
            "(POST .../actions/{action_var_name}; default cleanSave_t)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "write"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}",
    ),
    "save_transaction_version": _spec(
        "save_transaction_version",
        domain="commerce",
        operation="write",
        description=(
            "Save a Commerce transaction version "
            "(POST .../actions/{action_var_name}; default versionSave_t)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "write"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}",
    ),
    "submit_transaction": _spec(
        "submit_transaction",
        domain="commerce",
        operation="write",
        description=(
            "Submit a Commerce transaction for approval "
            "(POST .../actions/{action_var_name}; default submit_t)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "write"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}",
    ),
    "reconfigure_transaction": _spec(
        "reconfigure_transaction",
        domain="commerce",
        operation="write",
        description=(
            "Reconfigure a Commerce transaction "
            "(POST .../actions/_reconfigure_action)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "write"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/_reconfigure_action",
    ),
    "create_transaction_version": _spec(
        "create_transaction_version",
        domain="commerce",
        operation="write",
        description=(
            "Create a Commerce transaction version "
            "(POST .../actions/{action_var_name}; default versionTransaction_t)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "write"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}",
    ),
    "add_transaction_lines": _spec(
        "add_transaction_lines",
        domain="commerce",
        operation="write",
        description=(
            "Add line items to a Commerce transaction "
            "(POST .../actions/{action_var_name}; default addLineItem_t)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "lines", "write"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/{actionVarName}",
    ),
    "update_transaction_lines": _spec(
        "update_transaction_lines",
        domain="commerce",
        operation="write",
        description=(
            "Update transaction lines "
            "(POST .../actions/_update_line_items)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "lines", "write"},
        read_only=False,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/_update_line_items",
    ),
    "remove_transaction_lines": _spec(
        "remove_transaction_lines",
        domain="commerce",
        operation="write",
        description=(
            "Remove transaction lines via action "
            "(POST .../actions/_remove_transactionLine). "
            "Destructive — removes selected lines from the quote."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "lines", "write"},
        read_only=False,
        destructive=True,
        http_method="POST",
        api_path="/commerceDocuments{Process}{Doc}/{id}/actions/_remove_transactionLine",
    ),
    "delete_transaction_line": _spec(
        "delete_transaction_line",
        domain="commerce",
        operation="write",
        description=(
            "Delete one transaction line "
            "(DELETE .../transactionLine/{documentNumber}). "
            "Destructive — permanently removes that line document."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "lines", "write"},
        read_only=False,
        destructive=True,
        http_method="DELETE",
        api_path="/commerceDocuments{Process}{Doc}/{id}/transactionLine/{documentNumber}",
    ),
    "interact_transaction_line": _spec(
        "interact_transaction_line",
        domain="commerce",
        operation="write",
        description=(
            "Interact with a configured transaction line "
            "(POST .../transactionLine/{documentNumber}/actions/_interact)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "lines", "write"},
        read_only=False,
        http_method="POST",
        api_path=(
            "/commerceDocuments{Process}{Doc}/{id}/transactionLine/"
            "{documentNumber}/actions/_interact"
        ),
    ),
    "reconfigure_transaction_line": _spec(
        "reconfigure_transaction_line",
        domain="commerce",
        operation="write",
        description=(
            "Reconfigure a transaction line "
            "(POST .../transactionLine/{documentNumber}/actions/_reconfigure_action)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "lines", "write"},
        read_only=False,
        http_method="POST",
        api_path=(
            "/commerceDocuments{Process}{Doc}/{id}/transactionLine/"
            "{documentNumber}/actions/_reconfigure_action"
        ),
    ),
    "reconfigure_transaction_line_inbound": _spec(
        "reconfigure_transaction_line_inbound",
        domain="commerce",
        operation="write",
        description=(
            "Inbound reconfigure of a transaction line "
            "(POST .../transactionLine/{documentNumber}/actions/_reconfigure_inbound_action)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "transactions", "lines", "write"},
        read_only=False,
        http_method="POST",
        api_path=(
            "/commerceDocuments{Process}{Doc}/{id}/transactionLine/"
            "{documentNumber}/actions/_reconfigure_inbound_action"
        ),
    ),
    "list_metrics": _spec(
        "list_metrics",
        domain="metrics",
        operation="read",
        description=(
            "List Oracle CPQ site metrics (GET /metrics). Returns one page of items "
            "(name, value, startTime, endTime, dateModified, dateAdded). Optional "
            "filters: name (exact), start_time/end_time, date_modified_from/to, "
            "date_added_from/to — combined into the MongoDB-style q query param. "
            "Each item is enriched with description from profile METRICS_<NAME> env "
            "keys when present. Requires REST version that exposes /metrics "
            "(docs target v19; set REST_API_VERSION=v19 if v18 returns 404). "
            "Does not modify CPQ data."
        ),
        tags={"paginated", "metrics"},
        read_only=True,
        http_method="GET",
        api_path="/metrics",
    ),
    "get_collab_operation_queue": _spec(
        "get_collab_operation_queue",
        domain="collab",
        operation="read",
        description=(
            "Get the collaborative quote operation queue for a commerce document "
            "(GET /collabOperationQueues/{bs_id}). Returns queuedOperations, "
            "currentlyExecutingOperation, operationCount, and node. Requires a "
            "REST version that exposes collabOperationQueues (docs target v19). "
            "Does not clear the queue."
        ),
        tags={"collab", "queue"},
        read_only=True,
        http_method="GET",
        api_path="/collabOperationQueues/{bs_id}",
    ),
    "clear_collab_operation_queue": _spec(
        "clear_collab_operation_queue",
        domain="collab",
        operation="write",
        description=(
            "Clear the collaborative quote operation queue for a commerce document "
            "(POST /collabOperationQueues/{bs_id}/actions/clearCurrentQueue). "
            "Destructive — removes queued/current collab operations for that bs_id."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "collab", "queue"},
        read_only=False,
        destructive=True,
        http_method="POST",
        api_path="/collabOperationQueues/{bs_id}/actions/clearCurrentQueue",
    ),
    "get_commerce_ui_settings": _spec(
        "get_commerce_ui_settings",
        domain="commerce",
        operation="read",
        description=(
            "Get Commerce UI and general site settings "
            "(GET /commerceUISettings). Returns commerceSettings and "
            "generalSiteSettings as provided by CPQ. Requires a REST version that "
            "exposes this resource (docs target v19; set REST_API_VERSION=v19 if "
            "v18 returns 404). Read-only; does not change site configuration."
        ),
        tags={"commerce", "ui", "settings"},
        read_only=True,
        http_method="GET",
        api_path="/commerceUISettings",
    ),
    "list_saved_searches": _spec(
        "list_saved_searches",
        domain="commerce",
        operation="read",
        description=(
            "List saved searches for a commerce document resource "
            "(GET /searchResources/{resource_var_name}). Paginated with limit/offset. "
            "Optional show_all maps to query showAll (ALL|HIDDEN|VISIBLE|INACTIVE; "
            "default VISIBLE). When resource_var_name is omitted, derives "
            "commerceDocuments{Process}Transaction from process_var_name / profile "
            "COMMERCE_PROCESS_VAR_NAME (e.g. oraclecpqo → "
            "commerceDocumentsOraclecpqoTransaction). Docs target REST v19 "
            "(404 if unsupported). Does not modify CPQ data."
        ),
        tags={"paginated", "commerce", "saved_search"},
        read_only=True,
        http_method="GET",
        api_path="/searchResources/{resourceVarName}",
    ),
    "get_saved_search": _spec(
        "get_saved_search",
        domain="commerce",
        operation="read",
        description=(
            "Get one saved search by numeric search_id "
            "(GET /searchResources/{resource_var_name}/{search_id}). "
            "resource_var_name optional — same default derivation as "
            "list_saved_searches. Docs target REST v19. Does not modify CPQ data."
        ),
        tags={"commerce", "saved_search"},
        read_only=True,
        http_method="GET",
        api_path="/searchResources/{resourceVarName}/{searchId}",
    ),
    "list_certificates": _spec(
        "list_certificates",
        domain="admin",
        operation="read",
        description=(
            "List site certificates (GET /certificates). PEM/certificate material "
            "in responses is redacted ([REDACTED]) before reaching the LLM. "
            "Docs target REST v19 (set REST_API_VERSION=v19 if v18 returns 404). "
            "Read-only; does not change site configuration."
        ),
        tags={"admin", "certificates"},
        read_only=True,
        http_method="GET",
        api_path="/certificates",
    ),
    "get_certificate": _spec(
        "get_certificate",
        domain="admin",
        operation="read",
        description=(
            "Get one site certificate by name (GET /certificates/{name}). "
            "PEM/certificate material is redacted ([REDACTED]) in MCP responses. "
            "Docs target REST v19. Read-only."
        ),
        tags={"admin", "certificates"},
        read_only=True,
        http_method="GET",
        api_path="/certificates/{name}",
    ),
    "get_sso_configuration": _spec(
        "get_sso_configuration",
        domain="admin",
        operation="read",
        description=(
            "Get site SSO configuration (GET /ssoConfiguration). IdP certificate "
            "and SAML keystore fields are redacted ([REDACTED]) in MCP responses. "
            "Docs target REST v19. Read-only; does not change SSO settings."
        ),
        tags={"admin", "sso"},
        read_only=True,
        http_method="GET",
        api_path="/ssoConfiguration",
    ),
    "get_fusion_access_token": _spec(
        "get_fusion_access_token",
        domain="admin",
        operation="read",
        description=(
            "Obtain an IDCS/Fusion OAuth access token for the active profile when "
            "cpq_mode=fusion and fusion_enabled=true (client_credentials using oauth_* "
            "fields from the current environment). Returns token_type, expires_in, "
            "scope, and access_token_masked by default; set include_token=true to also "
            "return oauth_access_token (full Bearer value). Fails unless both flags "
            "enable Fusion. Does not call CPQ REST."
        ),
        tags={"admin", "fusion", "oauth"},
        read_only=True,
        version="1.0.0",
        cx_module="meta",
    ),
    "list_territories": _spec(
        "list_territories",
        domain="sales",
        operation="read",
        description=(
            "List Fusion CX Sales territories "
            "(GET /crmRestApi/resources/11.13.18.05/territories) via the profile "
            "cx: connection (Basic or Bearer). Requires cx.enabled and Sales in "
            "cx.modules. Returns one page; if hasMore is true, call again with "
            "offset = offset + limit. Optional filters: q, finder, fields, "
            "order_by, only_data, total_results. Does not call CPQ REST "
            "(/rest or /cpq/rest). Docs: Oracle Sales territories collection."
        ),
        tags={"paginated", "sales", "territories", "cx"},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/territories",
    ),
    "get_territory": _spec(
        "get_territory",
        domain="sales",
        operation="read",
        description=(
            "Get one Fusion CX Sales territory by territory_version_id (TerritoryVersionId path key). Requires cx.enabled and Sales in cx.modules. Optional fields, only_data, expand."
        ),
        tags={'cx', 'read', 'sales', 'territories'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/territories/{TerritoryVersionId}",
    ),
    "list_accounts": _spec(
        "list_accounts",
        domain="sales",
        operation="read",
        description=(
            "List Fusion CX Sales accounts (GET accounts collection). Requires Sales in cx.modules. Paginated; supports q, finder, fields, order_by, only_data, total_results."
        ),
        tags={'accounts', 'cx', 'paginated', 'read', 'sales'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/accounts",
    ),
    "get_account": _spec(
        "get_account",
        domain="sales",
        operation="read",
        description=(
            "Get one Fusion CX Sales account by party_number (PartyNumber). Requires Sales in cx.modules."
        ),
        tags={'accounts', 'cx', 'read', 'sales'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/accounts/{PartyNumber}",
    ),
    "list_account_team": _spec(
        "list_account_team",
        domain="sales",
        operation="read",
        description=(
            "List account team members for an account (child AccountTeam). Requires Sales in cx.modules."
        ),
        tags={'accounts', 'cx', 'paginated', 'read', 'sales'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/accounts/{PartyNumber}/child/AccountTeam",
    ),
    "get_account_team_member": _spec(
        "get_account_team_member",
        domain="sales",
        operation="read",
        description=(
            "Get one account team member by party_number and account_team_uniq_id."
        ),
        tags={'accounts', 'cx', 'read', 'sales'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/accounts/{PartyNumber}/child/AccountTeam/{AccountTeamUniqId}",
    ),
    "list_contacts": _spec(
        "list_contacts",
        domain="sales",
        operation="read",
        description=(
            "List Fusion CX Sales contacts. Requires Sales in cx.modules. Paginated collection filters."
        ),
        tags={'contacts', 'cx', 'paginated', 'read', 'sales'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/contacts",
    ),
    "get_contact": _spec(
        "get_contact",
        domain="sales",
        operation="read",
        description=(
            "Get one contact by party_number."
        ),
        tags={'contacts', 'cx', 'read', 'sales'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/contacts/{PartyNumber}",
    ),
    "list_leads": _spec(
        "list_leads",
        domain="sales",
        operation="read",
        description=(
            "List Fusion CX Sales leads. Optional effective_date (yyyy-MM-dd). leads_uniq_id for get_lead comes from collection links — do not invent."
        ),
        tags={'cx', 'leads', 'paginated', 'read', 'sales'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/leads",
    ),
    "get_lead": _spec(
        "get_lead",
        domain="sales",
        operation="read",
        description=(
            "Get one lead by leads_uniq_id from the leads collection (ADF uniq id in links)."
        ),
        tags={'cx', 'leads', 'read', 'sales'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/leads/{leadsUniqID}",
    ),
    "list_lead_opportunities": _spec(
        "list_lead_opportunities",
        domain="sales",
        operation="read",
        description=(
            "List lead opportunities for a lead (child LeadOpportunity)."
        ),
        tags={'cx', 'leads', 'paginated', 'read', 'sales'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/leads/{leadsUniqID}/child/LeadOpportunity",
    ),
    "get_lead_opportunity": _spec(
        "get_lead_opportunity",
        domain="sales",
        operation="read",
        description=(
            "Get one lead opportunity by leads_uniq_id and lead_number."
        ),
        tags={'cx', 'leads', 'read', 'sales'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/leads/{leadsUniqID}/child/LeadOpportunity/{LeadNumber}",
    ),
    "list_products": _spec(
        "list_products",
        domain="sales",
        operation="read",
        description=(
            "List Fusion CX Sales products (inventory items). Paginated."
        ),
        tags={'cx', 'paginated', 'products', 'read', 'sales'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/products",
    ),
    "get_product": _spec(
        "get_product",
        domain="sales",
        operation="read",
        description=(
            "Get one product by inventory_item_id."
        ),
        tags={'cx', 'products', 'read', 'sales'},
        read_only=True,
        version="1.0.0",
        cx_module="sales",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/products/{InventoryItemId}",
    ),
    "list_partners": _spec(
        "list_partners",
        domain="prm",
        operation="read",
        description=(
            "List Fusion CX PRM partners. Requires PRM in cx.modules."
        ),
        tags={'cx', 'paginated', 'partners', 'prm', 'read'},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partners",
    ),
    "get_partner": _spec(
        "get_partner",
        domain="prm",
        operation="read",
        description=(
            "Get one partner by company_number."
        ),
        tags={'cx', 'partners', 'prm', 'read'},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partners/{CompanyNumber}",
    ),
    "list_partner_lov": _spec(
        "list_partner_lov",
        domain="prm",
        operation="read",
        description=(
            "List Fusion CX PRM partner ADF LOV rows (GET partners/{CompanyNumber}/lov/"
            "{LovName}). Use after list_partners/get_partner to resolve LookupCode values "
            "to Meaning/DisplayLabel. For field PartnerProfilePEO_<suffix>, lov_name is "
            "PartnerProfilePEO_LOVVA_For_<suffix> (example: gnx_sls_Status_c). Do not invent "
            "lov_name; if unknown, get_partner(only_data=false) and use links with rel=lov. "
            "Optional lookup_code sets q=LookupCode=\"…\" when q is omitted. Paginated; empty "
            "items means no matching codes. Does not expand LOVs on get_partner and does not "
            "PATCH partner fields."
        ),
        tags={"cx", "paginated", "partners", "prm", "read"},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partners/{CompanyNumber}/lov/{LovName}",
    ),
    "list_partner_contacts": _spec(
        "list_partner_contacts",
        domain="prm",
        operation="read",
        description=(
            "List PRM partner contacts (partnerContacts collection). Requires PRM in cx.modules."
        ),
        tags={'cx', 'paginated', 'partners', 'prm', 'read'},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partnerContacts",
    ),
    "get_partner_contact": _spec(
        "get_partner_contact",
        domain="prm",
        operation="read",
        description=(
            "Get one partner contact by party_number."
        ),
        tags={'cx', 'partners', 'prm', 'read'},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}",
    ),
    "list_deals": _spec(
        "list_deals",
        domain="prm",
        operation="read",
        description=(
            "List PRM deal registrations. Optional effective_date. deals_uniq_id for get_deal comes from collection links — do not invent."
        ),
        tags={'cx', 'deals', 'paginated', 'prm', 'read'},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/deals",
    ),
    "get_deal": _spec(
        "get_deal",
        domain="prm",
        operation="read",
        description=(
            "Get one deal registration by deals_uniq_id from the deals collection."
        ),
        tags={'cx', 'deals', 'prm', 'read'},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/deals/{dealsUniqID}",
    ),
    "list_partner_contact_addresses": _spec(
        "list_partner_contact_addresses",
        domain="prm",
        operation="read",
        description=(
            "List addresses for a PRM partner contact (child addresses). Requires "
            "party_number and PRM in cx.modules. Paginated ADF collection filters."
        ),
        tags={"cx", "paginated", "partners", "prm", "read"},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/addresses",
    ),
    "get_partner_contact_address": _spec(
        "get_partner_contact_address",
        domain="prm",
        operation="read",
        description=(
            "Get one partner-contact address by party_number and address_number."
        ),
        tags={"cx", "partners", "prm", "read"},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/addresses/{AddressNumber}",
    ),
    "list_partner_contact_attachments": _spec(
        "list_partner_contact_attachments",
        domain="prm",
        operation="read",
        description=(
            "List attachment metadata for a PRM partner contact (child attachments). "
            "attachments_uniq_id for get_partner_contact_attachment comes from collection "
            "links — do not invent. Does not download attachment binary content."
        ),
        tags={"cx", "paginated", "partners", "prm", "read"},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/attachments",
    ),
    "get_partner_contact_attachment": _spec(
        "get_partner_contact_attachment",
        domain="prm",
        operation="read",
        description=(
            "Get one partner-contact attachment by party_number and attachments_uniq_id "
            "(from attachments collection links). Does not invent hash keys."
        ),
        tags={"cx", "partners", "prm", "read"},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/attachments/{attachmentsUniqID}",
    ),
    "list_partner_contact_contact_points": _spec(
        "list_partner_contact_contact_points",
        domain="prm",
        operation="read",
        description=(
            "List contact points (phone/email) for a PRM partner contact "
            "(child contactPoints). Requires party_number and PRM in cx.modules."
        ),
        tags={"cx", "paginated", "partners", "prm", "read"},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/contactPoints",
    ),
    "get_partner_contact_contact_point": _spec(
        "get_partner_contact_contact_point",
        domain="prm",
        operation="read",
        description=(
            "Get one partner-contact contact point by party_number and contact_point_id."
        ),
        tags={"cx", "partners", "prm", "read"},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/contactPoints/{ContactPointId}",
    ),
    "list_partner_contact_user_details": _spec(
        "list_partner_contact_user_details",
        domain="prm",
        operation="read",
        description=(
            "List user-account details for a PRM partner contact (child userdetails). "
            "Requires party_number and PRM in cx.modules."
        ),
        tags={"cx", "paginated", "partners", "prm", "read"},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/userdetails",
    ),
    "get_partner_contact_user_detail": _spec(
        "get_partner_contact_user_detail",
        domain="prm",
        operation="read",
        description=(
            "Get one partner-contact user-detail row by party_number and username "
            "(Username path key; @ is URL-encoded)."
        ),
        tags={"cx", "partners", "prm", "read"},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partnerContacts/{PartyNumber}/child/userdetails/{Username}",
    ),
    "list_partner_programs": _spec(
        "list_partner_programs",
        domain="prm",
        operation="read",
        description=(
            "List Fusion CX PRM partner programs (GET partnerPrograms). Requires PRM "
            "in cx.modules. Paginated; supports q, finder, fields, order_by, only_data, "
            "total_results."
        ),
        tags={"cx", "paginated", "partners", "prm", "read"},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partnerPrograms",
    ),
    "get_partner_program": _spec(
        "get_partner_program",
        domain="prm",
        operation="read",
        description=(
            "Get one partner program by program_number (ProgramNumber path key)."
        ),
        tags={"cx", "partners", "prm", "read"},
        read_only=True,
        version="1.0.0",
        cx_module="prm",
        http_method="GET",
        api_path="/crmRestApi/resources/11.13.18.05/partnerPrograms/{ProgramNumber}",
    ),
    "list_performance_logs": _spec(
        "list_performance_logs",
        domain="performance",
        operation="read",
        description=(
            "List Oracle CPQ performance log events (user activity timing / metrics). "
            "Returns one page of results. If hasMore is true, call again with "
            "offset = offset + limit. Supports collection filters: q_expr (MongoDB q), "
            "fields (attribute projection), orderby (e.g. serverTime:desc), and "
            "total_results. Empty items means no matching events for the filters. "
            "Does not export CSV files and does not use Performance Debugger APIs."
        ),
        tags={"paginated", "logs"},
        read_only=True,
        http_method="GET",
        api_path="/performanceLogs",
    ),
    "get_performance_log": _spec(
        "get_performance_log",
        domain="performance",
        operation="read",
        description=(
            "Get a single performance log event by numeric id. "
            "Does not export CSV and does not create Performance Debugger logs."
        ),
        tags={"logs"},
        read_only=True,
        http_method="GET",
        api_path="/performanceLogs/{id}",
    ),
    "export_performance_logs": _spec(
        "export_performance_logs",
        domain="performance",
        operation="write",
        description=(
            "Export performance log events via REST. Optional log_id for single event. "
            "Does not list logs (use list_performance_logs)."
            + DRY_RUN_DESCRIPTION_SUFFIX
        ),
        tags={"dry_run", "confirmation", "logs", "export"},
        read_only=False,
        http_method="POST",
        api_path="/performanceLogs/actions/export",
    ),
    "list_parts": _spec(
        "list_parts",
        domain="parts",
        operation="read",
        description=(
            "List parts from the CPQ site. Returns one page of results. "
            "If hasMore is true, call again with offset = offset + limit."
        ),
        tags={"paginated"},
        read_only=True,
        http_method="GET",
        api_path="/parts",
    ),
    "get_part": _spec(
        "get_part",
        domain="parts",
        operation="read",
        description="Get a single part by id.",
        tags={},
        read_only=True,
        http_method="GET",
        api_path="/parts/{id}",
    ),
    "search_parts": _spec(
        "search_parts",
        domain="parts",
        operation="read",
        description=(
            "Search parts via POST /parts/actions/search with a search body. "
            "Not a mutating write; allowed under READ_ONLY via client allowlist."
        ),
        tags={"search"},
        read_only=True,
        http_method="POST",
        api_path="/parts/actions/search",
    ),
    "discover_tools": _spec(
        "discover_tools",
        domain="meta",
        operation="read",
        description=(
            "Search and filter the Oracle CPQ MCP tool catalog by domain "
            "(users/groups/datatables/bml/commerce/performance/parts/tasks/configuration/"
            "metrics/collab/admin/sales/prm/…), "
            "cx_module (cpq/sales/prm/service/field_service/subscription/"
            "incentive_compensation/meta), "
            "operation, or free-text query. Use this to find read-only vs write tools "
            "before calling them."
        ),
        tags={"discovery"},
        read_only=True,
        version="1.0.2",
    ),
    "list_saved_prompts": _spec(
        "list_saved_prompts",
        domain="meta",
        operation="read",
        description=(
            "List locally saved refined prompts (title, tags, tools, last_run). "
            "Does not call Oracle CPQ. Library file defaults to .prompts/saved_prompts.json."
        ),
        tags={"saved_prompts"},
        read_only=True,
        version="1.1.1",
    ),
    "search_saved_prompts": _spec(
        "search_saved_prompts",
        domain="meta",
        operation="read",
        description=(
            "Search saved refined prompts by title text, tag, and/or tool domain. "
            "Does not call Oracle CPQ."
        ),
        tags={"saved_prompts", "search"},
        read_only=True,
        version="1.0.1",
    ),
    "get_saved_prompt": _spec(
        "get_saved_prompt",
        domain="meta",
        operation="read",
        description=(
            "Load one saved refined prompt by id, including refined_prompt text and variables. "
            "Does not call Oracle CPQ."
        ),
        tags={"saved_prompts"},
        read_only=True,
        version="1.0.1",
    ),
    "record_prompt_use": _spec(
        "record_prompt_use",
        domain="meta",
        operation="read",
        description=(
            "Record a completed saved-prompt run after the agent finishes the task. "
            "Updates last_run_at and run_count. When duration_ms and source are set "
            "(source=cache|api|mixed), also appends run history and updates that "
            "source's last/average duration only — never blend cache and API averages. "
            "Call after YES-gate CPQ work with best-effort wall-clock elapsed. "
            "Writes only the local saved-prompts library (not Oracle CPQ)."
        ),
        tags={"saved_prompts"},
        read_only=True,
        version="1.1.1",
    ),
    "save_refined_prompt": _spec(
        "save_refined_prompt",
        domain="meta",
        operation="read",
        description=(
            "Save a refined prompt (title, original user prompt, refined text, variables, "
            "tags, tools, output_format) into the local library. "
            "output_format is chat_text (default), json, or excel_download. "
            "Dedupes by content hash (includes output_format). "
            "Writes only .prompts/saved_prompts.json (or CPQ_SAVED_PROMPTS_PATH); not Oracle CPQ."
        ),
        tags={"saved_prompts"},
        read_only=True,
        version="1.2.1",
    ),
    "offer_save_refined_prompt": _spec(
        "offer_save_refined_prompt",
        domain="meta",
        operation="read",
        description=(
            "Offer to save a refined prompt after a CPQ-related task. If save is omitted, returns "
            "needs_user_input with choices: save once, save and always auto-save, or skip "
            "(chat fallback when elicitation is unavailable). "
            "With save=true persists via save_refined_prompt (including output_format); "
            "with always=true also writes AUTO_SAVE_REFINED_PROMPT=true to the active profile .env. "
            "Local library / profile file only; does not call Oracle CPQ."
        ),
        tags={"saved_prompts"},
        read_only=True,
        version="1.2.1",
    ),
    "set_auto_save_refined_prompt": _spec(
        "set_auto_save_refined_prompt",
        domain="meta",
        operation="read",
        description=(
            "Set AUTO_SAVE_REFINED_PROMPT=true|false on the active customer profile .env "
            "(allowlisted key rewrite only). Does not call Oracle CPQ. "
            "Treat the tool result as source of truth for the rest of this session; "
            "reload MCP if you need server instructions rebuilt from the new flag."
        ),
        tags={"saved_prompts"},
        read_only=True,
        version="1.0.1",
    ),
    "start_prompt_picker": _spec(
        "start_prompt_picker",
        domain="meta",
        operation="read",
        description=(
            "Interactively pick an enabled saved refined prompt: all (by title), search, "
            "by_tag, by_tool (also last5 / by_domain). Omit mode for the top-level menu; "
            "pass prompt_id to load and record use. Disabled prompts are hidden. "
            "Returns needs_user_input when the next choice is required. Does not call Oracle CPQ."
        ),
        tags={"saved_prompts", "discovery"},
        read_only=True,
        version="1.1.1",
    ),
    "set_saved_prompt_enabled": _spec(
        "set_saved_prompt_enabled",
        domain="meta",
        operation="read",
        description=(
            "Enable or disable a saved refined prompt by id. Disabled prompts are hidden "
            "from list/search/picker. Local library file only; does not call Oracle CPQ."
        ),
        tags={"saved_prompts"},
        read_only=True,
        version="1.0.1",
    ),
    "get_local_job": _spec(
        "get_local_job",
        domain="meta",
        operation="read",
        description=(
            "Poll an MCP-local background job started by start_bml_site_export "
            "(or future local job starters). Returns status queued|running|succeeded|failed "
            "plus result paths or error. Does not call Oracle CPQ. "
            "For Oracle CPQ async exports (export_datatables / export_bml_library_functions) "
            "use get_task + download_task_file with the CPQ taskId instead."
        ),
        tags={"local_data", "async"},
        read_only=True,
        version="1.0.1",
    ),
    "list_local_data": _spec(
        "list_local_data",
        domain="meta",
        operation="read",
        description=(
            "List local data/{profile}/{env} snapshots (manifests) for the active profile. "
            "Does not call Oracle CPQ. Use before live list/export tools when "
            "LOCAL_DATA_POLICY is ask or prefer."
        ),
        tags={"local_data", "discovery"},
        read_only=True,
        version="1.1.1",
    ),
    "get_local_data_status": _spec(
        "get_local_data_status",
        domain="meta",
        operation="read",
        description=(
            "Check whether a local snapshot exists for a domain "
            "(users/groups/bml/commerce/datatables). "
            "For commerce pass process_var_name; for datatables pass table_name. "
            "Does not call Oracle CPQ."
        ),
        tags={"local_data"},
        read_only=True,
        version="1.0.1",
    ),
    "load_local_data": _spec(
        "load_local_data",
        domain="meta",
        operation="read",
        description=(
            "Load a local snapshot summary and file paths under data/. "
            "Default omits large payloads (include_payload=false) to save tokens. "
            "Does not call Oracle CPQ."
        ),
        tags={"local_data"},
        read_only=True,
        version="1.1.1",
    ),
    "offer_use_local_data": _spec(
        "offer_use_local_data",
        domain="meta",
        operation="read",
        description=(
            "Ask whether to use a local data/ snapshot or fetch fresh CPQ data. "
            "Omit choice for needs_user_input (use_cache / fetch_fresh / prefer / never). "
            "prefer/never also write LOCAL_DATA_POLICY on the profile .env. "
            "Does not call Oracle CPQ."
        ),
        tags={"local_data"},
        read_only=True,
        version="1.1.1",
    ),
    "set_local_data_policy": _spec(
        "set_local_data_policy",
        domain="meta",
        operation="read",
        description=(
            "Set LOCAL_DATA_POLICY=ask|prefer|never on the active customer profile .env "
            "(allowlisted key rewrite only). Does not call Oracle CPQ. "
            "Reload MCP if you need server instructions rebuilt from the new flag."
        ),
        tags={"local_data"},
        read_only=True,
        version="1.0.1",
    ),
    "offer_export_response": _spec(
        "offer_export_response",
        domain="meta",
        operation="read",
        description=(
            "After a tabular chat answer, offer to export structured sheets to Excel and/or Word. "
            "Omit choice for needs_user_input (excel / word / both / skip / always_excel / never). "
            "always_excel/never also write POST_RESPONSE_EXPORT on the profile .env. "
            "Pass title and optional sheets/notes for context; on excel/word/both the agent must "
            "call export_response_excel / export_response_word with the same structured sheets "
            "(do not scrape markdown). Local files only; does not call Oracle CPQ."
        ),
        tags={"export", "excel", "local_data"},
        read_only=True,
        version="1.0.1",
    ),
    "export_response_excel": _spec(
        "export_response_excel",
        domain="meta",
        operation="read",
        description=(
            "Build a multi-sheet Excel (.xlsx) from structured sheets "
            "[{name, columns?, rows}] and write under data/{profile}/{env}/exports/. "
            "Returns a success envelope with path, absolute_path, and file:// uri "
            "(no MCP File attachment — Cursor hosts reject list+[File] structured output). "
            "Caps: 20 sheets, 10k rows total. Does not call Oracle CPQ."
        ),
        tags={"export", "excel"},
        read_only=True,
        version="1.1.0",
    ),
    "export_response_word": _spec(
        "export_response_word",
        domain="meta",
        operation="read",
        description=(
            "Build a Word (.docx) from structured sheets (optional notes) and optional "
            "diagrams [{title, mermaid?, image_path?, caption?}] and write under "
            "data/{profile}/{env}/exports/. Mermaid is rasterized locally via mmdc "
            "(@mermaid-js/mermaid-cli) when on PATH, or via a pre-rendered PNG at "
            "image_path under tmp/{profile}/{env}/; skipped diagrams keep source as "
            "prose and are listed in diagrams_skipped (export still succeeds). "
            "Title/notes/tables are written first; Mermaid is best-effort with hard "
            "process-tree kill and short budgets (~8s/diagram, ~12s total) so host MCP "
            "timeouts do not leave an empty exports folder. "
            "Prefer Mermaid kinds by content: flowchart/graph for flows; pie for shares; "
            "xychart-beta bar/line for numeric comparisons (no dedicated pictograph engine — "
            "optional PNG via image_path). "
            "Returns a success envelope with path, absolute_path, and file:// uri "
            "(no MCP File attachment). "
            "Requires optional dependency python-docx "
            '(pip install python-docx or pip install -e ".[docs]"). '
            "Does not call Oracle CPQ. Does not use public Kroki/mermaid.ink."
        ),
        tags={"export"},
        read_only=True,
        version="1.4.0",
    ),
    "set_post_response_export": _spec(
        "set_post_response_export",
        domain="meta",
        operation="read",
        description=(
            "Set POST_RESPONSE_EXPORT=ask|never|always_excel on the active customer profile .env "
            "(allowlisted key rewrite only). Does not call Oracle CPQ. "
            "Reload MCP if you need server instructions rebuilt from the new flag."
        ),
        tags={"export", "local_data"},
        read_only=True,
        version="1.0.1",
    ),
    "ensure_prompt_studio": _spec(
        "ensure_prompt_studio",
        domain="meta",
        operation="read",
        description=(
            "Probe local Prompt Studio (GET http://127.0.0.1:8765/api/health by default) and "
            "auto-start it in the background if it is not running "
            "(python -m apps.prompt_studio). Returns running/started, url, host, port, "
            "optional pid, and activation_commands if start fails. "
            "Does not call Oracle CPQ. Port override: CPQ_PROMPT_STUDIO_PORT. "
            "Calling this alone does not make a turn YES-gate for refined prompts."
        ),
        tags={"saved_prompts", "prompt_studio"},
        read_only=True,
        version="1.0.1",
    ),
    "get_customer_knowledge": _spec(
        "get_customer_knowledge",
        domain="meta",
        operation="read",
        description=(
            "Read the active profile's customer knowledge markdown under knowledge/ "
            "(cross-session engagement memory). Returns path, text, and character_count. "
            "Does not call Oracle CPQ. Use before repeating discovery work."
        ),
        tags={"knowledge", "memory"},
        read_only=True,
        version="1.0.0",
    ),
    "ensure_customer_knowledge": _spec(
        "ensure_customer_knowledge",
        domain="meta",
        operation="read",
        description=(
            "Create knowledge/{customer_id}.md stub if missing and set profile "
            "customer_knowledge_file when unset (allowlisted YAML/.env rewrite). "
            "Idempotent when already configured. Does not call Oracle CPQ. "
            "Reload MCP so injected Customer knowledge picks up the file in new chats."
        ),
        tags={"knowledge", "memory"},
        read_only=True,
        version="1.0.0",
    ),
    "append_customer_knowledge": _spec(
        "append_customer_knowledge",
        domain="meta",
        operation="read",
        description=(
            "Append a dated markdown discovery entry to the active profile customer "
            "knowledge file (env-tagged). Rejects secret-like content. Caps entry size. "
            "Auto-ensures stub + profile field when missing. Does not call Oracle CPQ. "
            "Same-session reuse: call get_customer_knowledge; next chat after MCP reload "
            "injects updated Customer knowledge."
        ),
        tags={"knowledge", "memory"},
        read_only=True,
        version="1.0.0",
    ),
    "sync_users_local": _spec(
        "sync_users_local",
        domain="users",
        operation="read",
        description=(
            "Fetch all CPQ users (paginated) and write data/{profile}/{env}/users/ "
            "(users.json + users.xlsx + manifest.json). Prefer this for a complete "
            "local cache. Defaults to active users only."
        ),
        tags={"export", "excel", "local_data"},
        read_only=True,
        http_method="GET",
        api_path="/users",
        version="1.1.1",
    ),
    "sync_groups_local": _spec(
        "sync_groups_local",
        domain="groups",
        operation="read",
        description=(
            "Fetch all company groups (paginated) and write data/{profile}/{env}/groups/ "
            "(groups.json + groups.xlsx + manifest.json)."
        ),
        tags={"export", "excel", "local_data"},
        read_only=True,
        http_method="GET",
        api_path="/companies/{company}/groups",
        version="1.1.1",
    ),
    "sync_bml_local": _spec(
        "sync_bml_local",
        domain="bml",
        operation="read",
        description=(
            "Fetch all util library BML functions with scriptText and write "
            "data/{profile}/{env}/bml/ (library.json + functions/**/*.bml + **/*.json)."
        ),
        tags={"export", "bml", "local_data"},
        read_only=True,
        http_method="GET",
        api_path="/bml/library/functions",
        version="1.1.1",
    ),
    "sync_commerce_metadata_local": _spec(
        "sync_commerce_metadata_local",
        domain="commerce",
        operation="read",
        description=(
            "Fetch all header/line attributes and actions for a commerce process "
            "(paginated) and write JSON + Excel under "
            "data/{profile}/{env}/commerce/{process}/."
        ),
        tags={"export", "excel", "local_data"},
        read_only=True,
        http_method="GET",
        api_path="/commerceProcesses/{process}/documents/{doc}/{resource}",
        version="1.1.1",
    ),
    "sync_datatable_local": _spec(
        "sync_datatable_local",
        domain="datatables",
        operation="read",
        description=(
            "Fetch one data table meta + all rows and write "
            "data/{profile}/{env}/datatables/{name}/ (meta.json, rows.json, rows.xlsx)."
        ),
        tags={"export", "excel", "local_data"},
        read_only=True,
        http_method="GET",
        api_path="/datatables/{name}",
        version="1.1.1",
    ),
    "sync_datatables_local": _spec(
        "sync_datatables_local",
        domain="datatables",
        operation="read",
        description=(
            "Sync one or more data tables locally. Defaults to all "
            "CUSTOM_DATA_TABLE_NAME* values from the profile."
        ),
        tags={"export", "excel", "local_data"},
        read_only=True,
        http_method="GET",
        api_path="/datatables/{name}",
        version="1.0.1",
    ),
}

CPQ_API_TOOLS = frozenset(
    name for name, spec in TOOL_CATALOG.items() if spec.cx_module == "cpq"
)


def mcp_tool_kwargs(spec: ToolSpec) -> dict[str, Any]:
    """Build FastMCP @tool decorator kwargs from a catalog spec."""
    meta: dict[str, Any] = {
        "domain": spec.domain,
        "operation": spec.operation,
        "cx_module": spec.cx_module,
        "version": spec.version,
    }
    if spec.http_method:
        meta["http_method"] = spec.http_method
    if spec.api_path:
        meta["api_path"] = spec.api_path

    mcp_icons = [
        Icon(src=icon.src, mimeType=icon.mime_type, sizes=list(icon.sizes) if icon.sizes else None)
        for icon in spec.icons
    ]

    kwargs: dict[str, Any] = {
        "title": spec.title,
        "description": spec.description,
        "version": spec.version,
        "icons": mcp_icons,
        "tags": set(spec.tags),
        "annotations": ToolAnnotations(
            readOnlyHint=spec.read_only,
            destructiveHint=spec.destructive,
            idempotentHint=spec.read_only,
            openWorldHint=spec.domain != "meta",
            title=spec.title,
        ),
        "meta": meta,
    }
    output_schema = get_tool_output_schema(spec.name)
    if output_schema is not None:
        kwargs["output_schema"] = output_schema
    return kwargs


def tool_to_dict(spec: ToolSpec) -> dict[str, Any]:
    """Serialize a tool spec for discover_tools responses."""
    return {
        "name": spec.name,
        "title": spec.title,
        "version": spec.version,
        "domain": spec.domain,
        "operation": spec.operation,
        "cx_module": spec.cx_module,
        "description": spec.description,
        "icons": [
            {
                "src": icon.src,
                "mimeType": icon.mime_type,
                "sizes": list(icon.sizes) if icon.sizes else None,
            }
            for icon in spec.icons
        ],
        "tags": sorted(spec.tags),
        "http_method": spec.http_method,
        "api_path": spec.api_path,
        "readOnlyHint": spec.read_only,
        "destructiveHint": spec.destructive,
        "risk": spec.risk,
    }


def _searchable_text(spec: ToolSpec) -> str:
    return " ".join(
        [
            spec.name,
            spec.title,
            spec.domain,
            spec.operation,
            spec.cx_module,
            spec.description,
            *spec.tags,
            spec.http_method or "",
            spec.api_path or "",
        ]
    ).lower()


def _tokenize(text: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", text.lower()) if len(token) > 1]


def _score_spec(spec: ToolSpec, query: str) -> int:
    lowered_query = query.lower().strip()
    if not lowered_query:
        return 0

    if spec.name.lower() == lowered_query:
        return 100
    if lowered_query in spec.name.lower():
        return 80
    if lowered_query in spec.description.lower():
        return 60

    tokens = _tokenize(lowered_query)
    if not tokens:
        return 0

    haystack = _searchable_text(spec)
    score = 0
    for token in tokens:
        if token in spec.name.lower():
            score += 30
        elif token in haystack:
            score += 10
    return score


def filter_tools(
    *,
    domain: DomainFilter = "all",
    operation: OperationFilter = "all",
    cx_module: CxModuleFilter = "all",
    include_meta: bool = False,
) -> list[ToolSpec]:
    """Return catalog tools matching domain, operation, and CX module filters."""
    results: list[ToolSpec] = []
    for name, spec in TOOL_CATALOG.items():
        # Local/helper tools (domain=meta or cx_module=meta) stay hidden unless requested.
        if not include_meta and (spec.domain == "meta" or spec.cx_module == "meta"):
            continue
        if domain != "all" and spec.domain != domain:
            continue
        if operation != "all" and spec.operation != operation:
            continue
        if cx_module != "all" and spec.cx_module != cx_module:
            continue
        results.append(spec)
    return sorted(results, key=lambda item: item.name)


def search_tools(
    query: str,
    *,
    domain: DomainFilter = "all",
    operation: OperationFilter = "all",
    cx_module: CxModuleFilter = "all",
    limit: int = 20,
    include_meta: bool = False,
) -> list[ToolSpec]:
    """Filter then rank tools by relevance to a free-text query."""
    candidates = filter_tools(
        domain=domain,
        operation=operation,
        cx_module=cx_module,
        include_meta=include_meta,
    )
    if not query.strip():
        return candidates[:limit]

    scored = [(spec, _score_spec(spec, query)) for spec in candidates]
    matched = [spec for spec, score in scored if score > 0]
    matched.sort(key=lambda spec: (_score_spec(spec, query), spec.name), reverse=True)
    return matched[:limit]


def discover_tools_result(
    *,
    query: str | None = None,
    domain: DomainFilter = "all",
    operation: OperationFilter = "all",
    cx_module: CxModuleFilter = "all",
    limit: int = 20,
) -> dict[str, Any]:
    """Build the discover_tools MCP tool response payload."""
    # Meta tools are hidden unless the caller filters cx_module=meta explicitly.
    include_meta = cx_module == "meta"
    if query and query.strip():
        specs = search_tools(
            query,
            domain=domain,
            operation=operation,
            cx_module=cx_module,
            limit=limit,
            include_meta=include_meta,
        )
    else:
        specs = filter_tools(
            domain=domain,
            operation=operation,
            cx_module=cx_module,
            include_meta=include_meta,
        )[:limit]

    tools = [tool_to_dict(spec) for spec in specs]
    return {"count": len(tools), "tools": tools}
