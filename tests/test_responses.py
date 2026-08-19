"""Tests for standard MCP tool response envelopes."""

from __future__ import annotations

from oracle_cpq_mcp.core.responses import wrap_tool_success


def test_wrap_read_success_moves_pagination_to_envelope() -> None:
    payload = {
        "items": [{"partyNumber": "1"}],
        "hasMore": True,
        "pagination": {"nextOffset": 100},
    }
    wrapped = wrap_tool_success("list_users", payload)
    assert wrapped["status"] == "ok"
    assert wrapped["tool"] == "list_users"
    assert wrapped["data"]["items"][0]["partyNumber"] == "1"
    assert "pagination" not in wrapped["data"]
    assert wrapped["pagination"]["nextOffset"] == 100


def test_wrap_write_preflight_keeps_status_at_top_level() -> None:
    payload = {
        "status": "preflight_ok",
        "tool": "update_user",
        "dry_run": True,
        "message": "preview",
    }
    wrapped = wrap_tool_success("update_user", payload)
    assert wrapped["status"] == "preflight_ok"
    assert wrapped["data"]["message"] == "preview"


def test_wrap_export_list_leaves_file_attachment_in_place() -> None:
    file_obj = {"kind": "file"}
    wrapped = wrap_tool_success(
        "export_users_excel",
        ["Exported 10 users", file_obj],
    )
    assert wrapped[0]["status"] == "ok"
    assert wrapped[0]["message"].startswith("Exported")
    assert wrapped[1] == file_obj


def test_wrap_leaves_errors_untouched() -> None:
    error = {"status": "error", "code": "NOT_FOUND", "message": "missing"}
    assert wrap_tool_success("get_user", error) == error
