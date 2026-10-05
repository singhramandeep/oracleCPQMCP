"""Shared helpers for Fusion CX MCP tools (Sales, PRM, Service, …)."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from oracle_cpq_mcp.core.cx_client import CXAPIError, CXClient
from oracle_cpq_mcp.core.pagination import enrich_pagination_hint
from oracle_cpq_mcp.core.profile_yaml import FUSION_MODULE_ALLOWLIST

CRM_REST_VERSION = "11.13.18.05"


def crm_rest_path(resource: str) -> str:
    """Build a Fusion CRM REST collection path for *resource* (no leading slash)."""
    name = resource.strip().lstrip("/")
    return f"/crmRestApi/resources/{CRM_REST_VERSION}/{name}"


def path_segment(value: str) -> str:
    """URL-encode one ADF path segment (party numbers, uniq ids, etc.)."""
    return quote(str(value).strip(), safe="")


def require_cx_module(client: CXClient, yaml_module: str) -> None:
    """Raise if CX is off or *yaml_module* is missing from profile ``cx.modules``."""
    profile = client.profile
    if not profile.cx_enabled:
        raise CXAPIError(
            "CX Fusion is not enabled on this profile/environment.",
            code="VALIDATION_ERROR",
            hint="Set environments.<env>.cx.enabled: true with url, auth, and modules.",
        )
    if yaml_module not in FUSION_MODULE_ALLOWLIST:
        raise CXAPIError(
            f"Unknown CX module {yaml_module!r}.",
            code="VALIDATION_ERROR",
            hint=f"Allowed: {', '.join(FUSION_MODULE_ALLOWLIST)}.",
        )
    if yaml_module not in (profile.cx_modules or []):
        raise CXAPIError(
            f"This tool requires {yaml_module} in environments.<env>.cx.modules.",
            code="VALIDATION_ERROR",
            hint=f"Add {yaml_module} to cx.modules and reload MCP.",
        )


def adf_collection_params(
    *,
    limit: int,
    offset: int,
    q: str | None = None,
    finder: str | None = None,
    fields: str | None = None,
    order_by: str | None = None,
    only_data: bool = True,
    total_results: bool = False,
    effective_date: str | None = None,
) -> dict[str, Any]:
    """ADF REST collection query params (omit empty optional filters)."""
    params: dict[str, Any] = {
        "limit": limit,
        "offset": offset,
        "onlyData": "true" if only_data else "false",
        "totalResults": "true" if total_results else "false",
    }
    if q:
        params["q"] = q
    if finder:
        params["finder"] = finder
    if fields:
        params["fields"] = fields
    if order_by:
        params["orderBy"] = order_by
    if effective_date:
        params["effectiveDate"] = effective_date
    return params


def adf_item_params(
    *,
    fields: str | None = None,
    only_data: bool = True,
    expand: str | None = None,
) -> dict[str, Any]:
    """ADF REST singular resource query params."""
    params: dict[str, Any] = {
        "onlyData": "true" if only_data else "false",
    }
    if fields:
        params["fields"] = fields
    if expand:
        params["expand"] = expand
    return params


def cx_get_collection(
    client: CXClient,
    path: str,
    tool_name: str,
    yaml_module: str,
    *,
    limit: int = 25,
    offset: int = 0,
    q: str | None = None,
    finder: str | None = None,
    fields: str | None = None,
    order_by: str | None = None,
    only_data: bool = True,
    total_results: bool = False,
    effective_date: str | None = None,
) -> dict[str, Any]:
    """GET an ADF collection after module gating; enrich pagination hints when applicable."""
    require_cx_module(client, yaml_module)
    params = adf_collection_params(
        limit=limit,
        offset=offset,
        q=q,
        finder=finder,
        fields=fields,
        order_by=order_by,
        only_data=only_data,
        total_results=total_results,
        effective_date=effective_date,
    )
    response = client.get(path, params=params)
    if isinstance(response, dict) and ("hasMore" in response or "items" in response):
        return enrich_pagination_hint(response, tool_name)
    return response


def cx_get_item(
    client: CXClient,
    path: str,
    yaml_module: str,
    *,
    fields: str | None = None,
    only_data: bool = True,
    expand: str | None = None,
) -> Any:
    """GET one ADF resource after module gating."""
    require_cx_module(client, yaml_module)
    params = adf_item_params(fields=fields, only_data=only_data, expand=expand)
    return client.get(path, params=params)
