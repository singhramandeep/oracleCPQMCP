"""MCP tools for Oracle CPQ Tasks APIs."""

from __future__ import annotations

from typing import Any

from fastmcp.utilities.types import File

from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.responses import build_attachment_lead_envelope
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool


def register_tasks_tools(mcp: Any, client: CPQClient) -> None:
    """Register task status and file download tools."""

    def get_task(task_id: str) -> dict[str, Any]:
        return client.get(f"/tasks/{task_id}")

    get_task.__doc__ = TOOL_CATALOG["get_task"].description
    register_tool(mcp, get_task, "get_task")

    def download_task_file(task_id: str, file_name: str) -> list[Any]:
        path = f"/tasks/{task_id}/files/{file_name}"
        data = client.get_bytes(path, accept="*/*")
        return [
            build_attachment_lead_envelope(
                "download_task_file",
                message=f"Downloaded task file '{file_name}' for task '{task_id}'.",
                filename=file_name,
                extra={"task_id": task_id, "file_name": file_name},
            ),
            File(data=data, name=file_name),
        ]

    download_task_file.__doc__ = TOOL_CATALOG["download_task_file"].description
    register_tool(mcp, download_task_file, "download_task_file")
