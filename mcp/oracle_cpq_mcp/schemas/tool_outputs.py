"""Pydantic-derived JSON Schemas for MCP tool output contracts."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolErrorOutput(BaseModel):
    """Canonical structured error envelope returned by the security pipeline."""

    status: Literal["error"] = "error"
    code: str
    message: str
    hint: str | None = None
    details: dict[str, Any] | None = None


class CpqCollectionOutput(BaseModel):
    """Paginated CPQ collection response (list_* tools, metadata actionDefs/attributes)."""

    model_config = ConfigDict(extra="allow")

    items: list[Any] = Field(default_factory=list)


class CpqObjectOutput(BaseModel):
    """Single CPQ entity or open CPQ JSON object."""

    model_config = ConfigDict(extra="allow")


class DiscoverToolsOutput(BaseModel):
    """discover_tools catalog payload."""

    count: int
    tools: list[dict[str, Any]]


class WriteToolOutput(BaseModel):
    """Preflight, confirmation, read-only block, or successful CPQ mutation response."""

    model_config = ConfigDict(extra="allow")

    tool: str | None = None
    action: str | None = None
    status: str
    message: str | None = None
    dry_run: bool | None = None


class BmlJsonOutput(BaseModel):
    """get_all_bml_code delivery=json payload."""

    model_config = ConfigDict(extra="allow")

    delivery: Literal["json"]
    utilLibraryFunctionCount: int
    utilLibraryFunctions: list[dict[str, Any]]


def _error_schema() -> dict[str, Any]:
    return ToolErrorOutput.model_json_schema()


def _with_error(success: dict[str, Any]) -> dict[str, Any]:
    """Union structured success payloads with the canonical error envelope."""
    return {"oneOf": [_error_schema(), success]}


def _cpq_collection_schema() -> dict[str, Any]:
    return _with_error(CpqCollectionOutput.model_json_schema())


def _cpq_object_schema() -> dict[str, Any]:
    return _with_error(CpqObjectOutput.model_json_schema())


def _write_tool_schema() -> dict[str, Any]:
    return _with_error(WriteToolOutput.model_json_schema())


def _discover_tools_schema() -> dict[str, Any]:
    return _with_error(DiscoverToolsOutput.model_json_schema())


def _bml_json_schema() -> dict[str, Any]:
    return _with_error(BmlJsonOutput.model_json_schema())


def _export_list_schema() -> dict[str, Any]:
    return _with_error(
        {
            "type": "array",
            "items": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "object", "additionalProperties": True},
                ]
            },
        }
    )


def _bml_export_schema() -> dict[str, Any]:
    return {
        "oneOf": [
            _error_schema(),
            BmlJsonOutput.model_json_schema(),
            {
                "type": "array",
                "items": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "object", "additionalProperties": True},
                    ]
                },
            },
        ]
    }


_CPQ_COLLECTION_SCHEMA = _cpq_collection_schema()
_CPQ_OBJECT_SCHEMA = _cpq_object_schema()
_WRITE_TOOL_SCHEMA = _write_tool_schema()
_DISCOVER_TOOLS_SCHEMA = _discover_tools_schema()
_EXPORT_LIST_SCHEMA = _export_list_schema()
_BML_EXPORT_SCHEMA = _bml_export_schema()

TOOL_OUTPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "list_users": _CPQ_COLLECTION_SCHEMA,
    "export_users_excel": _EXPORT_LIST_SCHEMA,
    "get_user": _CPQ_OBJECT_SCHEMA,
    "get_user_groups": _CPQ_COLLECTION_SCHEMA,
    "update_user": _WRITE_TOOL_SCHEMA,
    "list_groups": _CPQ_COLLECTION_SCHEMA,
    "get_group": _CPQ_OBJECT_SCHEMA,
    "list_group_users": _CPQ_COLLECTION_SCHEMA,
    "create_group": _WRITE_TOOL_SCHEMA,
    "list_datatables": _CPQ_COLLECTION_SCHEMA,
    "get_datatable": _CPQ_OBJECT_SCHEMA,
    "get_datatable_rows": _CPQ_COLLECTION_SCHEMA,
    "deploy_datatables": _WRITE_TOOL_SCHEMA,
    "get_all_bml_code": _BML_EXPORT_SCHEMA,
    "get_commerce_attributes": _CPQ_COLLECTION_SCHEMA,
    "get_commerce_actions": _CPQ_COLLECTION_SCHEMA,
    "get_line_attributes": _CPQ_COLLECTION_SCHEMA,
    "get_line_actions": _CPQ_COLLECTION_SCHEMA,
    "discover_tools": _DISCOVER_TOOLS_SCHEMA,
}


def get_tool_output_schema(tool_name: str) -> dict[str, Any] | None:
    """Return the JSON Schema for a tool's output, if registered."""
    return TOOL_OUTPUT_SCHEMAS.get(tool_name)
