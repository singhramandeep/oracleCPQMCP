"""MCP tools for Oracle CPQ Commerce metadata (attributes and actions)."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.commerce_paths import (
    DEFAULT_COMMERCE_DOC_VAR_NAME,
    DEFAULT_LINE_DOC_VAR_NAME,
    commerce_document_item_path,
    commerce_document_path,
    commerce_query_params,
    resolve_process_var_name,
)
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.pagination import build_page_params, clamp_limit, enrich_pagination_hint
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool


def _fetch_commerce_metadata(
    client: CPQClient,
    *,
    tool_name: str,
    process_var_name: str | None,
    doc_var_name: str,
    resource: str,
    expand_all: bool,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    resolved = resolve_process_var_name(client.profile, process_var_name)
    if isinstance(resolved, dict):
        return resolved

    path = commerce_document_path(resolved, doc_var_name, resource)  # type: ignore[arg-type]
    params = commerce_query_params(
        expand_all=expand_all,
        limit=clamp_limit(limit),
        offset=max(0, offset),
    )
    response = client.get(path, params=params)
    if not isinstance(response, dict):
        return response
    if "hasMore" in response or "items" in response:
        return enrich_pagination_hint(response, tool_name)
    return response


def register_commerce_tools(mcp: Any, client: CPQClient) -> None:
    """Register Commerce metadata tools on the FastMCP instance."""

    def get_commerce_attributes(
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
        expand_all: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        return _fetch_commerce_metadata(
            client,
            tool_name="get_commerce_attributes",
            process_var_name=process_var_name,
            doc_var_name=doc_var_name,
            resource="attributes",
            expand_all=expand_all,
            limit=limit,
            offset=offset,
        )

    get_commerce_attributes.__doc__ = TOOL_CATALOG["get_commerce_attributes"].description
    register_tool(mcp, get_commerce_attributes, "get_commerce_attributes")

    def get_commerce_actions(
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
        expand_all: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        return _fetch_commerce_metadata(
            client,
            tool_name="get_commerce_actions",
            process_var_name=process_var_name,
            doc_var_name=doc_var_name,
            resource="actionDefs",
            expand_all=expand_all,
            limit=limit,
            offset=offset,
        )

    get_commerce_actions.__doc__ = TOOL_CATALOG["get_commerce_actions"].description
    register_tool(mcp, get_commerce_actions, "get_commerce_actions")

    def get_line_attributes(
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_LINE_DOC_VAR_NAME,
        expand_all: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        return _fetch_commerce_metadata(
            client,
            tool_name="get_line_attributes",
            process_var_name=process_var_name,
            doc_var_name=doc_var_name,
            resource="attributes",
            expand_all=expand_all,
            limit=limit,
            offset=offset,
        )

    get_line_attributes.__doc__ = TOOL_CATALOG["get_line_attributes"].description
    register_tool(mcp, get_line_attributes, "get_line_attributes")

    def get_line_actions(
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_LINE_DOC_VAR_NAME,
        expand_all: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        return _fetch_commerce_metadata(
            client,
            tool_name="get_line_actions",
            process_var_name=process_var_name,
            doc_var_name=doc_var_name,
            resource="actionDefs",
            expand_all=expand_all,
            limit=limit,
            offset=offset,
        )

    get_line_actions.__doc__ = TOOL_CATALOG["get_line_actions"].description
    register_tool(mcp, get_line_actions, "get_line_actions")

    def get_commerce_attribute(
        attribute_var_name: str,
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
        expand_all: bool = False,
    ) -> dict[str, Any]:
        resolved = resolve_process_var_name(client.profile, process_var_name)
        if isinstance(resolved, dict):
            return resolved
        path = commerce_document_item_path(
            resolved, doc_var_name, "attributes", attribute_var_name
        )
        params = commerce_query_params(expand_all=expand_all)
        return client.get(path, params=params)

    get_commerce_attribute.__doc__ = TOOL_CATALOG["get_commerce_attribute"].description
    register_tool(mcp, get_commerce_attribute, "get_commerce_attribute")

    def get_commerce_action(
        action_var_name: str,
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
        expand_all: bool = False,
    ) -> dict[str, Any]:
        resolved = resolve_process_var_name(client.profile, process_var_name)
        if isinstance(resolved, dict):
            return resolved
        path = commerce_document_item_path(
            resolved, doc_var_name, "actionDefs", action_var_name
        )
        params = commerce_query_params(expand_all=expand_all)
        return client.get(path, params=params)

    get_commerce_action.__doc__ = TOOL_CATALOG["get_commerce_action"].description
    register_tool(mcp, get_commerce_action, "get_commerce_action")

    def list_commerce_processes(limit: int = 100, offset: int = 0) -> dict[str, Any]:
        params = build_page_params(limit, offset)
        response = client.get("/commerceProcessSetups", params=params)
        return enrich_pagination_hint(response, "list_commerce_processes")

    list_commerce_processes.__doc__ = TOOL_CATALOG["list_commerce_processes"].description
    register_tool(mcp, list_commerce_processes, "list_commerce_processes")
