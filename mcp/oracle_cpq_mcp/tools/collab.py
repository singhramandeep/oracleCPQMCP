"""MCP tools for Oracle CPQ Collaborative Quote Operation Queues."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.preflight import resolve_write_execution
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool


def _queue_path(bs_id: int) -> str:
    return f"/collabOperationQueues/{bs_id}"


def _clear_path(bs_id: int) -> str:
    return f"/collabOperationQueues/{bs_id}/actions/clearCurrentQueue"


def _summarize_queue(snapshot: Any) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        return {"raw_type": type(snapshot).__name__}
    queued = snapshot.get("queuedOperations")
    executing = snapshot.get("currentlyExecutingOperation")
    sample: list[str] = []
    if isinstance(queued, list):
        for op in queued[:5]:
            if isinstance(op, dict):
                desc = op.get("description") or op.get("operation") or op.get("name")
                if desc:
                    sample.append(str(desc))
            else:
                sample.append(str(op))
    return {
        "operationCount": snapshot.get("operationCount"),
        "node": snapshot.get("node"),
        "queued_count": len(queued) if isinstance(queued, list) else None,
        "has_currently_executing": executing is not None,
        "sample_queued_descriptions": sample,
    }


def register_collab_tools(mcp: Any, client: CPQClient) -> None:
    """Register collaborative quote queue tools on the FastMCP instance."""

    def get_collab_operation_queue(bs_id: int) -> dict[str, Any]:
        return client.get(_queue_path(bs_id))

    get_collab_operation_queue.__doc__ = TOOL_CATALOG[
        "get_collab_operation_queue"
    ].description
    register_tool(mcp, get_collab_operation_queue, "get_collab_operation_queue")

    def clear_collab_operation_queue(
        bs_id: int,
        dry_run: bool = True,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        post_path = _clear_path(bs_id)

        def _preflight() -> dict[str, Any]:
            snapshot = client.get(_queue_path(bs_id))
            summary = _summarize_queue(snapshot)
            return {
                "dry_run": True,
                "tool": "clear_collab_operation_queue",
                "action": "deploy",
                "status": "preflight_ok",
                "message": (
                    f"This will CLEAR the collaborative quote operation queue "
                    f"for bs_id={bs_id} via '{post_path}'."
                ),
                "confirmation_prompt": (
                    f"This will CLEAR the collaborative quote operation queue "
                    f"for bs_id={bs_id}. Confirm to proceed."
                ),
                "would_execute": {
                    "method": "POST",
                    "path": post_path,
                    "body": None,
                },
                "preflight": {
                    "bs_id": bs_id,
                    "post_path": post_path,
                    "queue_summary": summary,
                },
            }

        def _execute() -> dict[str, Any]:
            result = client.post(post_path)
            if result is None:
                return {
                    "cleared": True,
                    "bs_id": bs_id,
                    "path": post_path,
                    "http_status": 204,
                }
            if isinstance(result, dict):
                out = dict(result)
                out.setdefault("cleared", True)
                out.setdefault("bs_id", bs_id)
                return out
            return {"cleared": True, "bs_id": bs_id, "result": result}

        return resolve_write_execution(
            read_only=client.profile.read_only,
            dry_run=dry_run,
            confirmation_token=confirmation_token,
            tool="clear_collab_operation_queue",
            action="deploy",
            preflight_fn=_preflight,
            execute_fn=_execute,
        )

    clear_collab_operation_queue.__doc__ = TOOL_CATALOG[
        "clear_collab_operation_queue"
    ].description
    register_tool(mcp, clear_collab_operation_queue, "clear_collab_operation_queue")
