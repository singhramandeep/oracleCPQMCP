"""Shared helpers for Fusion CX MCP tools (Sales, PRM, Service, …)."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from oracle_cpq_mcp.core.cx_client import CXAPIError, CXClient
from oracle_cpq_mcp.core.pagination import enrich_pagination_hint
from oracle_cpq_mcp.core.profile_yaml import FUSION_MODULE_ALLOWLIST

CRM_REST_VERSION = "11.13.18.05"

# Top-level CX list_* tools → Adaptive Search entity names (not used for CPQ).
CX_AS_ENTITY_BY_TOOL: dict[str, str] = {
    "list_accounts": "Account",
    "list_contacts": "Contact",
    "list_leads": "Lead",
    "list_opportunities": "Opportunity",
    "list_products": "Product",
    "list_territories": "SalesTerritory",
    "list_partners": "Partner",
    "list_partner_contacts": "PartnerContact",
    "list_deals": "Deal",
    "list_partner_programs": "PartnerProgram",
    "list_partner_tiers": "PartnerTier",
}


def crm_rest_path(resource: str) -> str:
    """Build a Fusion CRM REST (ADF) collection path for *resource*."""
    name = resource.strip().lstrip("/")
    return f"/crmRestApi/resources/{CRM_REST_VERSION}/{name}"


def crm_search_path(resource: str) -> str:
    """Build a Fusion Adaptive Search path under searchResources."""
    name = resource.strip().lstrip("/")
    return f"/crmRestApi/searchResources/{CRM_REST_VERSION}/{name}"


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


def require_any_cx_module(client: CXClient) -> None:
    """Raise if CX is off or ``cx.modules`` is empty (shared Adaptive Search tools)."""
    profile = client.profile
    if not profile.cx_enabled:
        raise CXAPIError(
            "CX Fusion is not enabled on this profile/environment.",
            code="VALIDATION_ERROR",
            hint="Set environments.<env>.cx.enabled: true with url, auth, and modules.",
        )
    if not (profile.cx_modules or []):
        raise CXAPIError(
            "Adaptive Search tools require at least one entry in cx.modules.",
            code="VALIDATION_ERROR",
            hint="Add Sales, PRM, or another CX product to cx.modules and reload MCP.",
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


def _order_by_to_as_sort(order_by: str | None) -> list[dict[str, str]] | None:
    """Map ADF-style ``Name:asc`` / ``Name:desc`` to Adaptive Search sort array."""
    if not order_by or not str(order_by).strip():
        return None
    sort: list[dict[str, str]] = []
    for part in str(order_by).split(","):
        token = part.strip()
        if not token:
            continue
        if ":" in token:
            attr, direction = token.split(":", 1)
            attr = attr.strip()
            direction_raw = direction.strip().lower()
        else:
            attr = token
            direction_raw = "asc"
        if not attr:
            continue
        if direction_raw in {"desc", "descending"}:
            direction_out = "descending"
        else:
            direction_out = "ascending"
        sort.append({"attribute": attr, "direction": direction_out})
    return sort or None


def _fields_to_as_list(fields: str | None) -> list[str] | None:
    if not fields or not str(fields).strip():
        return None
    out = [p.strip() for p in str(fields).split(",") if p.strip()]
    return out or None


def cx_adaptive_list(
    client: CXClient,
    tool_name: str,
    yaml_module: str,
    entity: str,
    *,
    limit: int = 25,
    offset: int = 0,
    q: dict[str, Any] | None = None,
    keywords: str | None = None,
    fields: str | None = None,
    order_by: str | None = None,
    only_data: bool = True,
    total_results: bool = False,
) -> dict[str, Any]:
    """POST Adaptive Search transient query for a top-level CX entity list."""
    require_cx_module(client, yaml_module)
    body: dict[str, Any] = {
        "entity": entity,
        "limit": limit,
        "offset": offset,
    }
    if q is not None:
        body["q"] = q
    if keywords is not None and str(keywords).strip():
        body["keywords"] = str(keywords).strip()
    field_list = _fields_to_as_list(fields)
    if field_list is not None:
        body["fields"] = field_list
    sort = _order_by_to_as_sort(order_by)
    if sort is not None:
        body["sort"] = sort

    params: dict[str, Any] = {
        "onlyData": "true" if only_data else "false",
        "totalResults": "true" if total_results else "false",
    }
    path = crm_search_path("custom-actions/queries")
    response = client.post(
        path,
        json_body=body,
        params=params,
        headers={"Preference": "transient"},
    )
    if isinstance(response, dict) and ("hasMore" in response or "items" in response):
        return enrich_pagination_hint(response, tool_name)
    if isinstance(response, dict):
        return response
    return {"items": [], "count": 0, "hasMore": False, "raw": response}


def cx_adaptive_get(
    client: CXClient,
    path: str,
    *,
    params: dict[str, Any] | None = None,
) -> Any:
    """GET an Adaptive Search resource after any-CX-module gating."""
    require_any_cx_module(client)
    return client.get(path, params=params)


def cx_adaptive_suggest(
    client: CXClient,
    *,
    entity: str,
    suggestions: dict[str, Any],
    keywords: str | None = None,
    q: dict[str, Any] | None = None,
    fields: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> dict[str, Any]:
    """POST Adaptive Search Smart Suggest (Preference: recommend)."""
    require_any_cx_module(client)
    body: dict[str, Any] = {
        "entity": entity,
        "suggestions": suggestions,
        "limit": limit,
        "offset": offset,
    }
    if keywords is not None:
        body["keywords"] = keywords
    if q is not None:
        body["q"] = q
    field_list = _fields_to_as_list(fields)
    if field_list is not None:
        body["fields"] = field_list
    path = crm_search_path("custom-actions/queries")
    response = client.post(
        path,
        json_body=body,
        headers={"Preference": "recommend"},
    )
    if isinstance(response, dict) and ("hasMore" in response or "items" in response):
        return enrich_pagination_hint(response, "suggest_adaptive_search")
    if isinstance(response, dict):
        return response
    return {"items": [], "count": 0, "hasMore": False, "raw": response}
