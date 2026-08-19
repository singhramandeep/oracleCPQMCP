"""Helpers for fetching Oracle CPQ BML source code via REST APIs."""

from __future__ import annotations

import logging
from typing import Any

from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.config import CPQProfile
from oracle_cpq_mcp.core.pagination import iterate_collection
from oracle_cpq_mcp.core.progress import report_tool_progress

logger = logging.getLogger(__name__)

DEFAULT_MAX_UTIL_FUNCTIONS = 1000


def bml_export_filename(profile: CPQProfile) -> str:
    """Build a stable zip filename for a site BML export."""
    return f"{profile.customer_id}_{profile.environment}_bml_export.zip"


def library_function_resource_id(item: dict[str, Any]) -> str:
    """Resolve the CPQ path segment for one util library function."""
    for link in item.get("links") or []:
        if link.get("rel") == "self":
            href = link.get("href", "")
            marker = "/bml/library/functions/"
            if marker in href:
                return href.split(marker, 1)[1].split("?", 1)[0]

    variable_name = item.get("variableName")
    if not variable_name or not isinstance(variable_name, str):
        raise ValueError("Util library function is missing variableName")

    namespace = item.get("namespace")
    if namespace and isinstance(namespace, str):
        return f"{namespace}.{variable_name}"
    return variable_name


def fetch_all_util_library_code(
    client: CPQClient,
    *,
    max_functions: int = DEFAULT_MAX_UTIL_FUNCTIONS,
) -> list[dict[str, Any]]:
    """Fetch util library function metadata and scriptText for every function."""
    report_tool_progress(0, float(max_functions), message="Listing util library functions")
    summaries = iterate_collection(
        client,
        "/bml/library/functions",
        page_size=100,
        max_items=max_functions,
        on_progress=lambda count, message: report_tool_progress(
            float(count),
            float(max_functions),
            message=message or f"Listed {count} util library functions",
        ),
    )
    functions: list[dict[str, Any]] = []
    total = len(summaries)

    for index, item in enumerate(summaries, start=1):
        if not isinstance(item, dict):
            continue
        resource_id = library_function_resource_id(item)
        report_tool_progress(
            float(index),
            float(total or 1),
            message=f"Fetching BML source for {resource_id}",
        )
        detail = client.get(f"/bml/library/functions/{resource_id}")
        if not isinstance(detail, dict):
            logger.warning("Unexpected detail payload for BML function %s", resource_id)
            continue
        functions.append(
            {
                "resourceId": resource_id,
                "name": detail.get("name"),
                "variableName": detail.get("variableName"),
                "namespace": detail.get("namespace") or detail.get("folderName"),
                "description": detail.get("description"),
                "scriptText": detail.get("scriptText"),
                "returnType": detail.get("returnType"),
                "parameters": detail.get("parameters"),
                "isDeployed": detail.get("isDeployed", item.get("isDeployed")),
            }
        )

    return functions
