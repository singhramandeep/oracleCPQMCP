"""Standard MCP tool success/error response envelopes."""

from __future__ import annotations

from typing import Any

WRITE_RESPONSE_STATUSES = frozenset(
    {
        "preflight_ok",
        "preflight_failed",
        "confirmation_required",
        "read_only_blocked",
    }
)

_ENVELOPE_KEYS = frozenset({"status", "tool", "data", "pagination"})


def is_tool_error(payload: Any) -> bool:
    """Return True when *payload* is a structured tool error dict."""
    return isinstance(payload, dict) and payload.get("status") == "error"


def is_tool_output_envelope(payload: Any) -> bool:
    """Return True when *payload* already matches the MCP object output envelope."""
    if not isinstance(payload, dict) or "status" not in payload:
        return False

    status = payload.get("status")
    if status == "error":
        return "code" in payload and "message" in payload

    if status == "ok":
        return "tool" in payload and "data" in payload

    if status in WRITE_RESPONSE_STATUSES:
        return "tool" in payload and "data" in payload

    return False


def build_ok_envelope(
    tool_name: str,
    data: dict[str, Any],
    *,
    pagination: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a read-tool success envelope."""
    envelope: dict[str, Any] = {
        "status": "ok",
        "tool": tool_name,
        "data": data,
    }
    if pagination is not None:
        envelope["pagination"] = pagination
    return envelope


def build_write_envelope(tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Build a write/preflight envelope with write metadata nested under data."""
    status = payload.get("status")
    if status not in WRITE_RESPONSE_STATUSES:
        raise ValueError(f"Unsupported write status for envelope: {status!r}")

    data = {
        key: value
        for key, value in payload.items()
        if key not in {"status", "tool"}
    }
    return {
        "status": status,
        "tool": payload.get("tool") or tool_name,
        "data": data,
    }


def build_attachment_lead_envelope(
    tool_name: str,
    *,
    message: str,
    filename: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the object envelope used as the first element of attachment tool results."""
    data: dict[str, Any] = {"message": message}
    if filename is not None:
        data["filename"] = filename
    if extra:
        data.update(extra)
    return build_ok_envelope(tool_name, data)


def wrap_tool_success(tool_name: str, result: Any) -> Any:
    """Wrap tool payloads in the MCP-compliant object envelope where applicable."""
    if is_tool_error(result):
        return result

    if isinstance(result, list):
        return _wrap_list_success(tool_name, result)

    if not isinstance(result, dict):
        return result

    if is_tool_output_envelope(result):
        return result

    status = result.get("status")
    if status in WRITE_RESPONSE_STATUSES:
        return build_write_envelope(tool_name, result)

    data = dict(result)
    pagination = data.pop("pagination", None)
    return build_ok_envelope(tool_name, data, pagination=pagination)


def _wrap_list_success(tool_name: str, result: list[Any]) -> list[Any]:
    if not result:
        return result

    first = result[0]
    if is_tool_error(first):
        return result

    if isinstance(first, dict) and is_tool_output_envelope(first):
        return result

    if isinstance(first, str):
        return [build_attachment_lead_envelope(tool_name, message=first), *result[1:]]

    return [wrap_tool_success(tool_name, first), *result[1:]]
