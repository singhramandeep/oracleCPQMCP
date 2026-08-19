"""Ensure runtime tool outputs match MCP object envelope contracts."""

from __future__ import annotations

from typing import Any

import pytest

from oracle_cpq_mcp.core.responses import is_tool_output_envelope
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.schemas.tool_outputs import (
    catalog_tools_without_output_schema,
    get_attachment_lead_output_schema,
    get_tool_output_schema,
)


def _assert_object_schema(schema: dict[str, Any]) -> None:
    assert schema["type"] == "object"
    assert "oneOf" not in schema
    assert "status" in schema["properties"]


@pytest.mark.parametrize(
    "tool_name",
    sorted(set(TOOL_CATALOG) - catalog_tools_without_output_schema()),
)
def test_catalog_tool_output_schema_is_mcp_object(tool_name: str) -> None:
    schema = get_tool_output_schema(tool_name)
    assert schema is not None
    _assert_object_schema(schema)


def test_attachment_lead_schema_is_mcp_object() -> None:
    _assert_object_schema(get_attachment_lead_output_schema())


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "ok", "tool": "list_users", "data": {"items": []}},
        {
            "status": "preflight_ok",
            "tool": "update_user",
            "data": {"message": "preview", "dry_run": True},
        },
        {"status": "error", "code": "NOT_FOUND", "message": "missing"},
    ],
)
def test_runtime_envelope_detector(payload: dict[str, Any]) -> None:
    assert is_tool_output_envelope(payload)
