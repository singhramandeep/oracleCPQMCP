"""Tests for standard MCP tool response envelopes."""

from __future__ import annotations

from types import SimpleNamespace

from oracle_cpq_mcp.core.responses import (
    build_attachment_lead_envelope,
    build_write_envelope,
    is_tool_output_envelope,
    stamp_response_context,
    wrap_tool_success,
)
from oracle_cpq_mcp.schemas.tool_outputs import get_attachment_lead_output_schema


def test_stamp_response_context_adds_env_and_timestamp() -> None:
    ctx = SimpleNamespace(environment="dev", customer_id="acme")
    stamped = stamp_response_context(
        {"status": "ok", "tool": "get_user", "data": {}},
        ctx,
    )
    assert stamped["environment"] == "dev"
    assert stamped["customer_id"] == "acme"
    assert stamped["retrieved_at"].endswith("Z")


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
    assert is_tool_output_envelope(wrapped)


def test_wrap_write_preflight_keeps_status_at_top_level() -> None:
    payload = {
        "status": "preflight_ok",
        "tool": "update_user",
        "dry_run": True,
        "message": "preview",
    }
    wrapped = wrap_tool_success("update_user", payload)
    assert wrapped["status"] == "preflight_ok"
    assert wrapped["tool"] == "update_user"
    assert wrapped["data"]["message"] == "preview"
    assert "tool" not in wrapped["data"]
    assert is_tool_output_envelope(wrapped)


def test_build_write_envelope_from_helper() -> None:
    envelope = build_write_envelope(
        "create_group",
        {
            "status": "confirmation_required",
            "tool": "create_group",
            "message": "confirm",
        },
    )
    assert envelope["status"] == "confirmation_required"
    assert envelope["data"]["message"] == "confirm"


def test_wrap_export_list_leaves_file_attachment_in_place() -> None:
    file_obj = {"kind": "file"}
    lead = build_attachment_lead_envelope(
        "export_users_excel",
        message="Exported 10 users",
        filename="users.xlsx",
    )
    wrapped = wrap_tool_success("export_users_excel", [lead, file_obj])
    assert wrapped[0]["status"] == "ok"
    assert wrapped[0]["data"]["message"].startswith("Exported")
    assert wrapped[0]["data"]["filename"] == "users.xlsx"
    assert wrapped[1] == file_obj
    assert is_tool_output_envelope(wrapped[0])


def test_wrap_export_list_from_plain_summary_string() -> None:
    wrapped = wrap_tool_success(
        "export_users_excel",
        ["Exported 10 users", {"kind": "file"}],
    )
    assert wrapped[0]["data"]["message"].startswith("Exported")
    assert is_tool_output_envelope(wrapped[0])


def test_wrap_skips_already_wrapped_envelope() -> None:
    payload = {
        "status": "ok",
        "tool": "get_user",
        "data": {"partyNumber": "1"},
    }
    assert wrap_tool_success("get_user", payload) == payload


def test_wrap_leaves_errors_untouched() -> None:
    error = {"status": "error", "code": "NOT_FOUND", "message": "missing"}
    assert wrap_tool_success("get_user", error) == error
    assert is_tool_output_envelope(error)


def test_attachment_lead_schema_is_mcp_object() -> None:
    schema = get_attachment_lead_output_schema()
    assert schema["type"] == "object"
    assert "oneOf" not in schema
