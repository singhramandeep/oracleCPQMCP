"""Tests for MCP tool output JSON Schemas."""

from __future__ import annotations

import json

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG, mcp_tool_kwargs
from oracle_cpq_mcp.schemas.tool_outputs import TOOL_OUTPUT_SCHEMAS, ToolErrorOutput


def test_every_catalog_tool_has_output_schema() -> None:
    assert set(TOOL_OUTPUT_SCHEMAS) == set(TOOL_CATALOG)


def test_mcp_tool_kwargs_includes_output_schema() -> None:
    kwargs = mcp_tool_kwargs(TOOL_CATALOG["list_users"])
    assert "output_schema" in kwargs
    schema = kwargs["output_schema"]
    assert "oneOf" in schema
    assert schema["oneOf"][0]["properties"]["status"]["const"] == "error"


def test_error_schema_is_valid_json() -> None:
    schema = ToolErrorOutput.model_json_schema()
    json.dumps(schema)
    assert schema["properties"]["status"]["const"] == "error"


def test_write_tool_schema_covers_preflight_status() -> None:
    schema = TOOL_OUTPUT_SCHEMAS["update_user"]
    success_branch = schema["oneOf"][1]
    assert "status" in success_branch["properties"]
