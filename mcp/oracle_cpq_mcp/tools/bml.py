"""MCP tools for Oracle CPQ BML APIs."""

from __future__ import annotations

from typing import Any, Literal

from fastmcp.utilities.types import File

from oracle_cpq_mcp.core.bml_fetchers import (
    bml_export_filename,
    fetch_all_util_library_code,
)
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.pagination import build_page_params, enrich_pagination_hint
from oracle_cpq_mcp.core.preflight import (
    resolve_write_execution,
    run_export_bml_library_preflight,
)
from oracle_cpq_mcp.core.progress import report_tool_progress
from oracle_cpq_mcp.core.responses import build_attachment_lead_envelope
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool

BmlDelivery = Literal["zip", "json"]


def register_bml_tools(mcp: Any, client: CPQClient) -> None:
    """Register BML tools on the FastMCP instance."""

    def get_all_bml_code(delivery: BmlDelivery = "zip") -> list[str | File] | dict[str, Any]:
        if delivery == "zip":
            report_tool_progress(0, 1, message="Downloading BML/BMLT site export")
            zip_bytes = client.get_bytes("/adminMeta")
            report_tool_progress(1, 1, message="BML export download complete")
            filename = bml_export_filename(client.profile)
            summary = (
                f"Downloaded all Commerce BML and BMLT files from "
                f"{client.profile.customer_name} ({client.profile.environment}) "
                f"to {filename}. Equivalent to cpq-toolkit pull."
            )
            return [
                build_attachment_lead_envelope(
                    "get_all_bml_code",
                    message=summary,
                    filename=filename,
                    extra={"delivery": "zip"},
                ),
                File(
                    data=zip_bytes,
                    format="zip",
                    name=filename,
                ),
            ]

        functions, truncated, has_more = fetch_all_util_library_code(client)
        return {
            "delivery": "json",
            "customer": client.profile.customer_name,
            "environment": client.profile.environment,
            "utilLibraryFunctionCount": len(functions),
            "utilLibraryFunctions": functions,
            "truncated": truncated,
            "has_more": has_more,
            "note": (
                "JSON delivery returns util library scriptText only. "
                "Use delivery='zip' for the full Commerce BML/BMLT site export."
            ),
        }

    get_all_bml_code.__doc__ = TOOL_CATALOG["get_all_bml_code"].description
    register_tool(mcp, get_all_bml_code, "get_all_bml_code")

    def get_bml_function(function_id: str) -> dict[str, Any]:
        return client.get(f"/bml/library/functions/{function_id}")

    get_bml_function.__doc__ = TOOL_CATALOG["get_bml_function"].description
    register_tool(mcp, get_bml_function, "get_bml_function")

    def search_bml_scripts(
        q_expr: str | None = None,
        limit: int = 100,
        offset: int = 0,
        orderby: str | None = None,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        extra: dict[str, Any] = {}
        if q_expr:
            extra["q"] = q_expr
        if orderby:
            extra["orderby"] = orderby
        if fields:
            extra["fields"] = ",".join(fields)
        params = build_page_params(limit, offset, extra=extra or None)
        response = client.get("/bml/scripts", params=params)
        return enrich_pagination_hint(response, "search_bml_scripts")

    search_bml_scripts.__doc__ = TOOL_CATALOG["search_bml_scripts"].description
    register_tool(mcp, search_bml_scripts, "search_bml_scripts")

    def list_bml_common_functions(
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params = build_page_params(limit, offset)
        response = client.get("/bml/common/functions", params=params)
        return enrich_pagination_hint(response, "list_bml_common_functions")

    list_bml_common_functions.__doc__ = TOOL_CATALOG["list_bml_common_functions"].description
    register_tool(mcp, list_bml_common_functions, "list_bml_common_functions")

    def get_bml_common_function(name: str) -> dict[str, Any]:
        return client.get(f"/bml/common/functions/{name}")

    get_bml_common_function.__doc__ = TOOL_CATALOG["get_bml_common_function"].description
    register_tool(mcp, get_bml_common_function, "get_bml_common_function")

    def list_bml_library_folders(
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params = build_page_params(limit, offset)
        response = client.get("/bml/library/folders", params=params)
        return enrich_pagination_hint(response, "list_bml_library_folders")

    list_bml_library_folders.__doc__ = TOOL_CATALOG["list_bml_library_folders"].description
    register_tool(mcp, list_bml_library_folders, "list_bml_library_folders")

    def get_bml_dependent_attributes(body: dict[str, Any] | None = None) -> dict[str, Any]:
        return client.post(
            "/bml/library/functions/actions/dependentAttributes",
            json_body=body or {},
        )

    get_bml_dependent_attributes.__doc__ = TOOL_CATALOG[
        "get_bml_dependent_attributes"
    ].description
    register_tool(mcp, get_bml_dependent_attributes, "get_bml_dependent_attributes")

    def export_bml_library_functions(
        body: dict[str, Any] | None = None,
        dry_run: bool = True,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        payload = body or {}
        return resolve_write_execution(
            read_only=client.profile.read_only,
            dry_run=dry_run,
            confirmation_token=confirmation_token,
            tool="export_bml_library_functions",
            action="export",
            preflight_fn=lambda: run_export_bml_library_preflight(client, payload),
            execute_fn=lambda: client.post(
                "/bml/library/functions/actions/export",
                json_body=payload,
            ),
        )

    export_bml_library_functions.__doc__ = TOOL_CATALOG[
        "export_bml_library_functions"
    ].description
    register_tool(mcp, export_bml_library_functions, "export_bml_library_functions")
