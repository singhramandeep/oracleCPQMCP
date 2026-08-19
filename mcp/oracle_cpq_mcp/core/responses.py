"""Standard MCP tool success response envelopes."""

from __future__ import annotations

from typing import Any

_WRITE_STATUSES = frozenset(
    {
        "preflight_ok",
        "preflight_failed",
        "confirmation_required",
        "read_only_blocked",
    }
)


def is_tool_error(payload: Any) -> bool:
    """Return True when *payload* is a structured tool error dict."""
    return isinstance(payload, dict) and payload.get("status") == "error"


def wrap_tool_success(tool_name: str, result: Any) -> Any:
    """Wrap successful tool payloads in a consistent MCP response envelope."""
    if is_tool_error(result):
        return result

    if isinstance(result, list):
        return _wrap_list_success(tool_name, result)

    if not isinstance(result, dict):
        return result

    status = result.get("status")
    if status in _WRITE_STATUSES:
        data = {key: value for key, value in result.items() if key != "status"}
        return {
            "status": status,
            "tool": result.get("tool") or tool_name,
            "data": data,
        }

    data = dict(result)
    pagination = data.pop("pagination", None)
    envelope: dict[str, Any] = {
        "status": "ok",
        "tool": tool_name,
        "data": data,
    }
    if pagination is not None:
        envelope["pagination"] = pagination
    return envelope


def _wrap_list_success(tool_name: str, result: list[Any]) -> list[Any]:
    if not result:
        return result

    first = result[0]
    if is_tool_error(first):
        return result

    if isinstance(first, str):
        envelope: dict[str, Any] = {
            "status": "ok",
            "tool": tool_name,
            "message": first,
        }
        return [envelope, *result[1:]]

    if isinstance(first, dict) and first.get("status") in _WRITE_STATUSES:
        return [wrap_tool_success(tool_name, first), *result[1:]]

    return [wrap_tool_success(tool_name, first), *result[1:]]
