"""MCP tools for Oracle CPQ Metrics APIs."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.metrics_filters import build_metrics_q, normalize_metric_name
from oracle_cpq_mcp.core.pagination import build_page_params, enrich_pagination_hint
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool


def _attach_metric_descriptions(
    payload: dict[str, Any],
    descriptions: dict[str, str],
) -> dict[str, Any]:
    """Copy items and add ``description`` from profile METRICS_* map when known."""
    items = payload.get("items")
    if not isinstance(items, list) or not descriptions:
        return payload
    enriched: list[Any] = []
    for item in items:
        if not isinstance(item, dict):
            enriched.append(item)
            continue
        copy = dict(item)
        raw_name = copy.get("name")
        if isinstance(raw_name, str) and raw_name.strip():
            key = normalize_metric_name(raw_name)
            if key in descriptions:
                copy["description"] = descriptions[key]
        enriched.append(copy)
    out = dict(payload)
    out["items"] = enriched
    return out


def register_metrics_tools(mcp: Any, client: CPQClient) -> None:
    """Register Metrics tools on the FastMCP instance."""

    def list_metrics(
        limit: int = 100,
        offset: int = 0,
        total_results: bool = True,
        name: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        date_modified_from: str | None = None,
        date_modified_to: str | None = None,
        date_added_from: str | None = None,
        date_added_to: str | None = None,
    ) -> dict[str, Any]:
        q = build_metrics_q(
            name=name,
            start_time=start_time,
            end_time=end_time,
            date_modified_from=date_modified_from,
            date_modified_to=date_modified_to,
            date_added_from=date_added_from,
            date_added_to=date_added_to,
        )
        extra: dict[str, Any] = {}
        if q:
            extra["q"] = q
        params = build_page_params(
            limit,
            offset,
            total_results=total_results,
            extra=extra or None,
        )
        response = client.get("/metrics", params=params)
        if not isinstance(response, dict):
            return response
        enriched = _attach_metric_descriptions(
            response,
            client.profile.metric_descriptions,
        )
        if "hasMore" in enriched or "items" in enriched:
            return enrich_pagination_hint(enriched, "list_metrics")
        return enriched

    list_metrics.__doc__ = TOOL_CATALOG["list_metrics"].description
    register_tool(mcp, list_metrics, "list_metrics")
