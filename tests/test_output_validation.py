"""Tests for post-execution output schema validation."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from oracle_cpq_mcp.core.output_validation import (
    OutputValidationError,
    build_output_validation_error,
    resolve_output_schema,
    validate_tool_output,
)
from oracle_cpq_mcp.core.responses import build_attachment_lead_envelope, build_ok_envelope


def test_resolve_output_schema_for_dict_tool() -> None:
    schema = resolve_output_schema("get_user")
    assert schema is not None
    assert schema["type"] == "object"


def test_resolve_output_schema_for_attachment_tool() -> None:
    schema = resolve_output_schema("export_users_excel")
    assert schema is not None
    assert schema["type"] == "object"


def test_validate_accepts_ok_envelope() -> None:
    payload = build_ok_envelope("get_user", {"partyNumber": "user123"})
    validate_tool_output("get_user", payload)


def test_validate_accepts_error_envelope() -> None:
    payload = {
        "status": "error",
        "code": "NOT_FOUND",
        "message": "User not found.",
    }
    validate_tool_output("get_user", payload)


def test_validate_accepts_attachment_lead_envelope() -> None:
    payload = [
        build_attachment_lead_envelope(
            "export_users_excel",
            message="Exported 10 users.",
            filename="users.xlsx",
        ),
        {"attachment": "skipped"},
    ]
    validate_tool_output("export_users_excel", payload)


def test_validate_rejects_missing_status() -> None:
    with pytest.raises(OutputValidationError):
        validate_tool_output("get_user", {"tool": "get_user", "data": {}})


def test_validate_rejects_ok_envelope_missing_tool_and_data() -> None:
    with pytest.raises(OutputValidationError):
        validate_tool_output("get_user", {"status": "ok"})


def test_validate_rejects_error_envelope_missing_code() -> None:
    with pytest.raises(OutputValidationError):
        validate_tool_output("get_user", {"status": "error", "message": "failed"})


def test_build_output_validation_error_is_safe() -> None:
    cpq_blob = {"partyNumber": "secret-user", "email": "user@example.com"}
    error = build_output_validation_error()
    serialized = str(error)
    assert error["code"] == "INTERNAL_ERROR"
    assert error["details"] == {"reason": "output_schema_validation_failed"}
    assert "secret-user" not in serialized
    assert "user@example.com" not in serialized
    assert cpq_blob["partyNumber"] not in serialized


def test_validate_does_not_leak_cpq_blob_on_failure() -> None:
    cpq_blob = {
        "status": "ok",
        "tool": "get_user",
        "data": {
            "partyNumber": "leaked-user-999",
            "email": "leaked@example.com",
        },
        "unexpected_top_level": {"nested": "value"},
    }
    cpq_blob.pop("tool")
    cpq_blob.pop("data")
    cpq_blob["status"] = "ok"

    with pytest.raises(OutputValidationError):
        validate_tool_output("get_user", cpq_blob)

    safe = build_output_validation_error()
    assert "leaked-user-999" not in str(safe)
    assert "leaked@example.com" not in str(safe)


def test_validate_skips_non_dict_list_tail() -> None:
    payload = [
        build_attachment_lead_envelope(
            "export_users_excel",
            message="done",
            filename="users.xlsx",
        ),
        b"binary-bytes-not-validated",
    ]
    validate_tool_output("export_users_excel", payload)


def test_validate_rejects_malformed_attachment_lead() -> None:
    with pytest.raises(OutputValidationError):
        validate_tool_output("export_users_excel", [{"foo": "bar"}])
