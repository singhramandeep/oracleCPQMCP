"""Tests for MCP tool output JSON Schemas."""

from __future__ import annotations

import json

import pytest
from fastmcp.tools.function_tool import FunctionTool

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG, mcp_tool_kwargs
from oracle_cpq_mcp.schemas.tool_outputs import (
    TOOL_OUTPUT_SCHEMAS,
    ToolErrorOutput,
    catalog_tools_without_output_schema,
    get_tool_output_schema,
    mcp_tool_output_schema,
)


def test_every_catalog_tool_has_output_schema_entry() -> None:
    assert set(TOOL_OUTPUT_SCHEMAS) == set(TOOL_CATALOG)


def test_list_tools_use_mcp_object_output_schema() -> None:
    kwargs = mcp_tool_kwargs(TOOL_CATALOG["list_users"])
    assert "output_schema" in kwargs
    schema = kwargs["output_schema"]
    assert schema["type"] == "object"
    assert "oneOf" not in schema
    assert schema["properties"]["status"]["type"] == "string"


def test_export_tools_omit_output_schema() -> None:
    for tool_name in catalog_tools_without_output_schema():
        kwargs = mcp_tool_kwargs(TOOL_CATALOG[tool_name])
        assert "output_schema" not in kwargs
        assert get_tool_output_schema(tool_name) is None


def test_mcp_tool_output_schema_is_fastmcp_compatible() -> None:
    schema = mcp_tool_output_schema()

    def sample() -> dict[str, str]:
        return {"status": "ok"}

    FunctionTool.from_function(fn=sample, name="sample", output_schema=schema)


def test_error_schema_is_valid_json() -> None:
    schema = ToolErrorOutput.model_json_schema()
    json.dumps(schema)
    assert schema["properties"]["status"]["const"] == "error"


def test_write_tool_schema_is_object_with_status_and_data() -> None:
    schema = TOOL_OUTPUT_SCHEMAS["update_user"]
    assert schema is not None
    assert schema["type"] == "object"
    assert "status" in schema["properties"]
    assert "data" in schema["properties"]


@pytest.mark.parametrize("tool_name", sorted(set(TOOL_CATALOG) - catalog_tools_without_output_schema()))
def test_registered_output_schemas_are_objects(tool_name: str) -> None:
    schema = get_tool_output_schema(tool_name)
    assert schema is not None
    assert schema["type"] == "object"

    def sample() -> dict[str, str]:
        return {"status": "ok"}

    FunctionTool.from_function(fn=sample, name=tool_name, output_schema=schema)
