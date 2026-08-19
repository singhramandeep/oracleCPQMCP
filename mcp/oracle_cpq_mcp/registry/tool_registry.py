"""Central catalog and search/filter helpers for Oracle CPQ MCP tools."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from mcp.types import ToolAnnotations

DomainName = Literal["users", "groups", "datatables", "meta"]
OperationName = Literal["read", "write"]
DomainFilter = Literal["users", "groups", "datatables", "all"]
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
    "discover_tools": _spec(
        "discover_tools",
        domain="meta",
        operation="read",
        description=(
            "Search and filter the Oracle CPQ MCP tool catalog by domain, operation, "
            "or free-text query. Use this to find read-only vs write tools before calling them."
        ),
        tags={"discovery"},
        read_only=True,
    ),
}

CPQ_API_TOOLS = frozenset(name for name, spec in TOOL_CATALOG.items() if spec.domain != "meta")


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

    return {
        "tags": set(spec.tags),
        "annotations": ToolAnnotations(
            readOnlyHint=spec.read_only,
            destructiveHint=spec.destructive,
            title=spec.name,
        ),
        "meta": meta,
    }


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
