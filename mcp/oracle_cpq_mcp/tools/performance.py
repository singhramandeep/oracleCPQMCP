"""MCP tools for Oracle CPQ Performance Logs APIs."""

from __future__ import annotations

import json
from typing import Any

from fastmcp.utilities.types import File

from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.pagination import build_page_params, enrich_pagination_hint
from oracle_cpq_mcp.core.preflight import resolve_write_execution
from oracle_cpq_mcp.core.responses import build_attachment_lead_envelope
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool


def _list_query_extra(
    *,
    q_expr: str | None,
    fields: list[str] | None,
    orderby: list[str] | None,
) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    if q_expr:
        extra["q"] = q_expr
    if fields:
        extra["fields"] = ",".join(fields)
    if orderby:
        extra["orderby"] = ",".join(orderby)
    return extra


def register_performance_tools(mcp: Any, client: CPQClient) -> None:
    """Register performance log tools on the FastMCP instance."""

    def list_performance_logs(
        limit: int = 100,
        offset: int = 0,
        total_results: bool = True,
        q_expr: str | None = None,
        fields: list[str] | None = None,
        orderby: list[str] | None = None,
    ) -> dict[str, Any]:
        params = build_page_params(
            limit,
            offset,
            total_results=total_results,
            extra=_list_query_extra(q_expr=q_expr, fields=fields, orderby=orderby) or None,
        )
        response = client.get("/performanceLogs", params=params)
        return enrich_pagination_hint(response, "list_performance_logs")

    list_performance_logs.__doc__ = TOOL_CATALOG["list_performance_logs"].description
    register_tool(mcp, list_performance_logs, "list_performance_logs")

    def get_performance_log(log_id: str) -> dict[str, Any]:
        return client.get(f"/performanceLogs/{log_id}")

    get_performance_log.__doc__ = TOOL_CATALOG["get_performance_log"].description
    register_tool(mcp, get_performance_log, "get_performance_log")

    def export_performance_logs(
        log_id: str | None = None,
        body: dict[str, Any] | None = None,
        dry_run: bool = True,
        confirmation_token: str | None = None,
    ) -> Any:
        if log_id:
            post_path = f"/performanceLogs/{log_id}/actions/export"
        else:
            post_path = "/performanceLogs/actions/export"
        payload = body or {}

        def _preflight() -> dict[str, Any]:
            return {
                "dry_run": True,
                "tool": "export_performance_logs",
                "action": "deploy",
                "status": "preflight_ok",
                "message": (
                    f"This will EXPORT PERFORMANCE LOGS via '{post_path}' in CPQ."
                ),
                "confirmation_prompt": (
                    f"This will EXPORT PERFORMANCE LOGS via '{post_path}' in CPQ. "
                    "Confirm to proceed."
                ),
                "would_execute": {
                    "method": "POST",
                    "path": post_path,
                    "body": payload,
                },
                "preflight": {
                    "post_path": post_path,
                    "log_id": log_id,
                    "body_keys": sorted(payload.keys()),
                },
            }

        def _execute() -> Any:
            raw = client.post_bytes(post_path, json_body=payload, accept="*/*")
            try:
                return json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                filename = (
                    f"performance_log_{log_id}.bin"
                    if log_id
                    else "performance_logs_export.bin"
                )
                return [
                    build_attachment_lead_envelope(
                        "export_performance_logs",
                        message="Exported performance log data from CPQ.",
                        filename=filename,
                        extra={"log_id": log_id},
                    ),
                    File(data=raw, name=filename),
                ]

        return resolve_write_execution(
            read_only=client.profile.read_only,
            dry_run=dry_run,
            confirmation_token=confirmation_token,
            tool="export_performance_logs",
            action="deploy",
            preflight_fn=_preflight,
            execute_fn=_execute,
        )

    export_performance_logs.__doc__ = TOOL_CATALOG["export_performance_logs"].description
    register_tool(mcp, export_performance_logs, "export_performance_logs")
