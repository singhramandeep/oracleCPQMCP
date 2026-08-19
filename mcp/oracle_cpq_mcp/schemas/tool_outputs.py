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


class ToolSuccessEnvelope(BaseModel):
    """Standard read-tool success envelope."""

    model_config = ConfigDict(extra="allow")

    status: Literal["ok"] = "ok"
    tool: str
    data: dict[str, Any] | list[Any]


class ToolWriteEnvelope(BaseModel):
    """Write-tool preflight, confirmation, or execution envelope."""

    model_config = ConfigDict(extra="allow")

    status: str
    tool: str
    data: dict[str, Any] = Field(default_factory=dict)


class ToolExportEnvelope(BaseModel):
    """Export tool summary envelope preceding binary attachments."""

    status: Literal["ok"] = "ok"
    tool: str
    message: str


class DiscoverToolsOutput(BaseModel):
    """discover_tools payload nested under data."""

    count: int
    tools: list[dict[str, Any]]


class BmlJsonOutput(BaseModel):
    """get_all_bml_code delivery=json payload nested under data."""

    model_config = ConfigDict(extra="allow")

    delivery: Literal["json"]
    utilLibraryFunctionCount: int
    utilLibraryFunctions: list[dict[str, Any]]


def _error_schema() -> dict[str, Any]:
    return ToolErrorOutput.model_json_schema()


def _with_error(success: dict[str, Any]) -> dict[str, Any]:
    """Union structured success payloads with the canonical error envelope."""
    return {"oneOf": [_error_schema(), success]}


def _success_envelope_schema() -> dict[str, Any]:
    return _with_error(ToolSuccessEnvelope.model_json_schema())


def _write_envelope_schema() -> dict[str, Any]:
    return _with_error(ToolWriteEnvelope.model_json_schema())


def _discover_tools_schema() -> dict[str, Any]:
    inner = ToolSuccessEnvelope.model_json_schema()
    inner["properties"]["data"] = DiscoverToolsOutput.model_json_schema()
    return _with_error(inner)


def _bml_json_schema() -> dict[str, Any]:
    inner = ToolSuccessEnvelope.model_json_schema()
    inner["properties"]["data"] = BmlJsonOutput.model_json_schema()
    return _with_error(inner)


def _export_list_schema() -> dict[str, Any]:
    return _with_error(
        {
            "type": "array",
            "items": {
                "anyOf": [
                    ToolExportEnvelope.model_json_schema(),
                    ToolErrorOutput.model_json_schema(),
                    {"type": "object", "additionalProperties": True},
                ]
            },
        }
    )


def _bml_export_schema() -> dict[str, Any]:
    return {
        "oneOf": [
            _error_schema(),
            ToolSuccessEnvelope.model_json_schema(),
            _export_list_schema()["oneOf"][0],
        ]
    }


_SUCCESS_ENVELOPE_SCHEMA = _success_envelope_schema()
_WRITE_ENVELOPE_SCHEMA = _write_envelope_schema()
_DISCOVER_TOOLS_SCHEMA = _discover_tools_schema()
_EXPORT_LIST_SCHEMA = _export_list_schema()
_BML_JSON_SCHEMA = _bml_json_schema()
_BML_EXPORT_SCHEMA = _bml_export_schema()

TOOL_OUTPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "list_users": _SUCCESS_ENVELOPE_SCHEMA,
    "export_users_excel": _EXPORT_LIST_SCHEMA,
    "get_user": _SUCCESS_ENVELOPE_SCHEMA,
    "get_user_groups": _SUCCESS_ENVELOPE_SCHEMA,
    "update_user": _WRITE_ENVELOPE_SCHEMA,
    "list_groups": _SUCCESS_ENVELOPE_SCHEMA,
    "get_group": _SUCCESS_ENVELOPE_SCHEMA,
    "list_group_users": _SUCCESS_ENVELOPE_SCHEMA,
    "create_group": _WRITE_ENVELOPE_SCHEMA,
    "list_datatables": _SUCCESS_ENVELOPE_SCHEMA,
    "get_datatable": _SUCCESS_ENVELOPE_SCHEMA,
    "get_datatable_rows": _SUCCESS_ENVELOPE_SCHEMA,
    "deploy_datatables": _WRITE_ENVELOPE_SCHEMA,
    "get_all_bml_code": _BML_EXPORT_SCHEMA,
    "get_commerce_attributes": _SUCCESS_ENVELOPE_SCHEMA,
    "get_commerce_actions": _SUCCESS_ENVELOPE_SCHEMA,
    "get_line_attributes": _SUCCESS_ENVELOPE_SCHEMA,
    "get_line_actions": _SUCCESS_ENVELOPE_SCHEMA,
    "discover_tools": _DISCOVER_TOOLS_SCHEMA,
}


def get_tool_output_schema(tool_name: str) -> dict[str, Any] | None:
    """Return the JSON Schema for a tool's output, if registered."""
    return TOOL_OUTPUT_SCHEMAS.get(tool_name)
