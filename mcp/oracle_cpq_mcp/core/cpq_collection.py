"""Oracle CPQ REST collection query params (q, sort, pagination, expand, finder).

See Oracle CPQ REST docs: Query Collections, Sort, Paginate, Expand.
Fusion CX Adaptive Search uses a separate code path (tools/cx/).
"""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.pagination import build_page_params


def cpq_collection_extra(
    *,
    q_expr: str | None = None,
    fields: list[str] | None = None,
    orderby: list[str] | None = None,
    expand: str | None = None,
    exclude_field_types: str | None = None,
    finder: str | None = None,
    only_data: bool | None = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map MCP tool filter args to CPQ GET query string parameters."""
    params: dict[str, Any] = dict(extra or {})
    if q_expr:
        params["q"] = q_expr
    if fields:
        params["fields"] = ",".join(fields)
    if orderby:
        params["orderby"] = ",".join(orderby)
    if expand:
        params["expand"] = expand
    if exclude_field_types:
        params["excludeFieldTypes"] = exclude_field_types
    if finder:
        params["finder"] = finder
    if only_data is True:
        params["onlyData"] = "true"
    elif only_data is False:
        params["onlyData"] = "false"
    return params


def cpq_expand_params(
    *,
    expand: str | None = None,
    exclude_field_types: str | None = None,
    only_data: bool | None = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Query params for singular GET resources that support expand."""
    params = cpq_collection_extra(
        expand=expand,
        exclude_field_types=exclude_field_types,
        only_data=only_data,
        extra=extra,
    )
    return params or None


def cpq_list_params(
    limit: int,
    offset: int,
    *,
    total_results: bool = True,
    q_expr: str | None = None,
    fields: list[str] | None = None,
    orderby: list[str] | None = None,
    expand: str | None = None,
    exclude_field_types: str | None = None,
    finder: str | None = None,
    only_data: bool | None = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build full CPQ collection page params (pagination + collection filters)."""
    collection = cpq_collection_extra(
        q_expr=q_expr,
        fields=fields,
        orderby=orderby,
        expand=expand,
        exclude_field_types=exclude_field_types,
        finder=finder,
        only_data=only_data,
        extra=extra,
    )
    return build_page_params(
        limit,
        offset,
        total_results=total_results,
        extra=collection or None,
    )
