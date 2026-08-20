"""Central catalog and search/filter helpers for Oracle CPQ MCP tools."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from mcp.types import ToolAnnotations

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
    "meta",
]
OperationName = Literal["read", "write"]
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
    "all",
]
OperationFilter = Literal["read", "write", "all"]
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
    destructive: bool = False
    http_method: str | None = None
    api_path: str | None = None
    risk: RiskLevel = "READ_ONLY"


def _compute_risk(
    name: str,
    *,
    operation: OperationName,
    destructive: bool,
) -> RiskLevel:
    if name == "export_users_excel":
        return "PRIVILEGED"
    if name == "get_all_bml_code":
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
) -> ToolSpec:
    merged_tags = frozenset({domain, operation, *tags})
    spec = ToolSpec(
        name=name,
        domain=domain,
        operation=operation,
        description=description,
        tags=merged_tags,
        read_only=read_only,
        destructive=destructive,
        http_method=http_method,
        api_path=api_path,
    )
    return ToolSpec(
        name=spec.name,
        domain=spec.domain,
        operation=spec.operation,
        description=spec.description,
        tags=spec.tags,
        read_only=spec.read_only,
        destructive=spec.destructive,
        http_method=spec.http_method,
        api_path=spec.api_path,
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
        description="Export CPQ users to an Excel (.xlsx) file. Defaults to active users only.",
        tags={"export", "excel"},
        read_only=True,
        http_method="GET",
        api_path="/users",
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
            "Download or retrieve BML source code from the CPQ site. "
            "delivery='zip' (default) exports all Commerce BML and BMLT files via "
            "GET /adminMeta — equivalent to cpq-toolkit pull. "
            "delivery='json' returns util library functions with scriptText inline "
            "(paginated fetch of /bml/library/functions plus per-function detail). "
            "Admin permissions required."
        ),
        tags={"export", "admin", "bml"},
        read_only=True,
        http_method="GET",
        api_path="/adminMeta",
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
            "(users/groups/datatables/bml/commerce/performance/parts/tasks/configuration), "
            "operation, or free-text query. Use this to find read-only vs write tools "
            "before calling them."
        ),
        tags={"discovery"},
        read_only=True,
    ),
}

CPQ_API_TOOLS = frozenset(name for name, spec in TOOL_CATALOG.items() if spec.domain != "meta")


def human_tool_title(name: str) -> str:
    """Convert snake_case tool names into MCP annotation titles."""
    special = {"bml": "BML", "cpq": "CPQ", "excel": "Excel"}
    return " ".join(special.get(part, part.capitalize()) for part in name.split("_"))


def mcp_tool_kwargs(spec: ToolSpec) -> dict[str, Any]:
    """Build FastMCP @tool decorator kwargs from a catalog spec."""
    meta: dict[str, Any] = {
        "domain": spec.domain,
        "operation": spec.operation,
    }
    if spec.http_method:
        meta["http_method"] = spec.http_method
    if spec.api_path:
        meta["api_path"] = spec.api_path

    kwargs: dict[str, Any] = {
        "tags": set(spec.tags),
        "annotations": ToolAnnotations(
            readOnlyHint=spec.read_only,
            destructiveHint=spec.destructive,
            idempotentHint=spec.read_only,
            openWorldHint=spec.domain != "meta",
            title=human_tool_title(spec.name),
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
        "domain": spec.domain,
        "operation": spec.operation,
        "description": spec.description,
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
            spec.domain,
            spec.operation,
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
    include_meta: bool = False,
) -> list[ToolSpec]:
    """Return catalog tools matching domain and operation filters."""
    results: list[ToolSpec] = []
    for name, spec in TOOL_CATALOG.items():
        if spec.domain == "meta" and not include_meta:
            continue
        if domain != "all" and spec.domain != domain:
            continue
        if operation != "all" and spec.operation != operation:
            continue
        results.append(spec)
    return sorted(results, key=lambda item: item.name)


def search_tools(
    query: str,
    *,
    domain: DomainFilter = "all",
    operation: OperationFilter = "all",
    limit: int = 20,
    include_meta: bool = False,
) -> list[ToolSpec]:
    """Filter then rank tools by relevance to a free-text query."""
    candidates = filter_tools(domain=domain, operation=operation, include_meta=include_meta)
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
    limit: int = 20,
) -> dict[str, Any]:
    """Build the discover_tools MCP tool response payload."""
    if query and query.strip():
        specs = search_tools(
            query,
            domain=domain,
            operation=operation,
            limit=limit,
            include_meta=False,
        )
    else:
        specs = filter_tools(domain=domain, operation=operation, include_meta=False)[:limit]

    tools = [tool_to_dict(spec) for spec in specs]
    return {"count": len(tools), "tools": tools}
