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
    pagination: dict[str, Any] | None = None


class ToolWriteEnvelope(BaseModel):
    """Write-tool preflight, confirmation, or execution envelope."""

    model_config = ConfigDict(extra="allow")

    status: str
    tool: str
    data: dict[str, Any] = Field(default_factory=dict)


class ToolAttachmentLeadEnvelope(BaseModel):
    """First list element for export/BML tools that attach binary resources."""

    model_config = ConfigDict(extra="allow")

    status: Literal["ok"] = "ok"
    tool: str
    data: dict[str, Any]


class DiscoverToolsOutput(BaseModel):
    """discover_tools payload nested under data."""

    count: int
    tools: list[dict[str, Any]]


def mcp_tool_output_schema(
    *,
    data_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a single object schema accepted by MCP / FastMCP output registration.

    MCP requires top-level ``type: object`` — ``oneOf`` and top-level arrays are rejected.
    Runtime responses use this shape for dict results. Attachment tools return a list whose
    first element matches this schema, followed by a ``File`` resource.
    """
    properties: dict[str, Any] = {
        "status": {
            "type": "string",
            "description": (
                "Result status: ok, error, preflight_ok, confirmation_required, "
                "read_only_blocked, etc."
            ),
        },
        "tool": {"type": "string"},
        "code": {"type": "string"},
        "message": {"type": "string"},
        "hint": {"type": "string"},
        "details": {"type": "object", "additionalProperties": True},
        "pagination": {"type": "object", "additionalProperties": True},
        "environment": {
            "type": "string",
            "description": "Active CPQ environment (dev, test, or prod).",
        },
        "customer_id": {
            "type": "string",
            "description": "Active customer profile id.",
        },
        "retrieved_at": {
            "type": "string",
            "description": "UTC ISO-8601 timestamp when the tool result was produced.",
        },
        "data": data_schema
        or {
            "description": "Tool-specific payload for successful or preflight responses.",
        },
    }
    return {
        "type": "object",
        "properties": properties,
        "required": ["status"],
        "additionalProperties": True,
    }


_READ_OUTPUT_SCHEMA = mcp_tool_output_schema()
_WRITE_OUTPUT_SCHEMA = mcp_tool_output_schema()
_DISCOVER_TOOLS_SCHEMA = mcp_tool_output_schema(
    data_schema=DiscoverToolsOutput.model_json_schema(),
)
_ATTACHMENT_LEAD_SCHEMA = mcp_tool_output_schema(
    data_schema={
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "filename": {"type": "string"},
        },
        "required": ["message"],
        "additionalProperties": True,
    }
)

# Tools that return a top-level list (summary envelope + File attachment) cannot declare a
# compliant MCP object output schema at the tool root; the first list element uses
# ``_ATTACHMENT_LEAD_SCHEMA`` instead.
_TOOLS_WITHOUT_OUTPUT_SCHEMA = frozenset(
    {
        "export_users_excel",
        "get_all_bml_code",
        "download_attachment",
        "download_task_file",
        "export_performance_logs",
    }
)

TOOL_OUTPUT_SCHEMAS: dict[str, dict[str, Any] | None] = {
    "list_users": _READ_OUTPUT_SCHEMA,
    "export_users_excel": None,
    "get_user": _READ_OUTPUT_SCHEMA,
    "get_user_groups": _READ_OUTPUT_SCHEMA,
    "update_user": _WRITE_OUTPUT_SCHEMA,
    "list_groups": _READ_OUTPUT_SCHEMA,
    "get_group": _READ_OUTPUT_SCHEMA,
    "list_group_users": _READ_OUTPUT_SCHEMA,
    "create_group": _WRITE_OUTPUT_SCHEMA,
    "list_datatables": _READ_OUTPUT_SCHEMA,
    "get_datatable": _READ_OUTPUT_SCHEMA,
    "get_datatable_rows": _READ_OUTPUT_SCHEMA,
    "list_datatable_fields": _READ_OUTPUT_SCHEMA,
    "get_datatable_field": _READ_OUTPUT_SCHEMA,
    "deploy_datatables": _WRITE_OUTPUT_SCHEMA,
    "create_datatable": _WRITE_OUTPUT_SCHEMA,
    "export_datatables": _WRITE_OUTPUT_SCHEMA,
    "get_all_bml_code": None,
    "get_bml_function": _READ_OUTPUT_SCHEMA,
    "search_bml_scripts": _READ_OUTPUT_SCHEMA,
    "list_bml_common_functions": _READ_OUTPUT_SCHEMA,
    "get_bml_common_function": _READ_OUTPUT_SCHEMA,
    "list_bml_library_folders": _READ_OUTPUT_SCHEMA,
    "get_bml_dependent_attributes": _READ_OUTPUT_SCHEMA,
    "export_bml_library_functions": _WRITE_OUTPUT_SCHEMA,
    "get_task": _READ_OUTPUT_SCHEMA,
    "download_task_file": None,
    "list_product_families": _READ_OUTPUT_SCHEMA,
    "get_product_family": _READ_OUTPUT_SCHEMA,
    "list_product_lines": _READ_OUTPUT_SCHEMA,
    "get_product_line": _READ_OUTPUT_SCHEMA,
    "list_models": _READ_OUTPUT_SCHEMA,
    "get_model": _READ_OUTPUT_SCHEMA,
    "list_config_attributes": _READ_OUTPUT_SCHEMA,
    "get_config_attribute": _READ_OUTPUT_SCHEMA,
    "list_array_sets": _READ_OUTPUT_SCHEMA,
    "get_array_set": _READ_OUTPUT_SCHEMA,
    "list_array_set_attributes": _READ_OUTPUT_SCHEMA,
    "get_array_set_attribute": _READ_OUTPUT_SCHEMA,
    "list_config_menu_items": _READ_OUTPUT_SCHEMA,
    "get_config_menu_item": _READ_OUTPUT_SCHEMA,
    "get_config_layout": _READ_OUTPUT_SCHEMA,
    "get_layout_cache_attributes": _READ_OUTPUT_SCHEMA,
    "get_commerce_attributes": _READ_OUTPUT_SCHEMA,
    "get_commerce_actions": _READ_OUTPUT_SCHEMA,
    "get_commerce_attribute": _READ_OUTPUT_SCHEMA,
    "get_commerce_action": _READ_OUTPUT_SCHEMA,
    "list_commerce_processes": _READ_OUTPUT_SCHEMA,
    "get_line_attributes": _READ_OUTPUT_SCHEMA,
    "get_line_actions": _READ_OUTPUT_SCHEMA,
    "list_transactions": _READ_OUTPUT_SCHEMA,
    "get_transaction": _READ_OUTPUT_SCHEMA,
    "list_transaction_lines": _READ_OUTPUT_SCHEMA,
    "get_transaction_line": _READ_OUTPUT_SCHEMA,
    "get_document_layout": _READ_OUTPUT_SCHEMA,
    "generate_proposal": _WRITE_OUTPUT_SCHEMA,
    "export_attachment": _WRITE_OUTPUT_SCHEMA,
    "download_attachment": None,
    "copy_transaction": _WRITE_OUTPUT_SCHEMA,
    "copy_transaction_lines": _WRITE_OUTPUT_SCHEMA,
    "list_performance_logs": _READ_OUTPUT_SCHEMA,
    "get_performance_log": _READ_OUTPUT_SCHEMA,
    "export_performance_logs": None,
    "list_parts": _READ_OUTPUT_SCHEMA,
    "get_part": _READ_OUTPUT_SCHEMA,
    "search_parts": _READ_OUTPUT_SCHEMA,
    "discover_tools": _DISCOVER_TOOLS_SCHEMA,
    "list_saved_prompts": _READ_OUTPUT_SCHEMA,
    "search_saved_prompts": _READ_OUTPUT_SCHEMA,
    "get_saved_prompt": _READ_OUTPUT_SCHEMA,
    "record_prompt_use": _READ_OUTPUT_SCHEMA,
    "save_refined_prompt": _READ_OUTPUT_SCHEMA,
    "offer_save_refined_prompt": _READ_OUTPUT_SCHEMA,
    "set_auto_save_refined_prompt": _READ_OUTPUT_SCHEMA,
    "start_prompt_picker": _READ_OUTPUT_SCHEMA,
    "set_saved_prompt_enabled": _READ_OUTPUT_SCHEMA,
    "list_local_data": _READ_OUTPUT_SCHEMA,
    "get_local_data_status": _READ_OUTPUT_SCHEMA,
    "load_local_data": _READ_OUTPUT_SCHEMA,
    "offer_use_local_data": _READ_OUTPUT_SCHEMA,
    "set_local_data_policy": _READ_OUTPUT_SCHEMA,
    "sync_users_local": _READ_OUTPUT_SCHEMA,
    "sync_groups_local": _READ_OUTPUT_SCHEMA,
    "sync_bml_local": _READ_OUTPUT_SCHEMA,
    "sync_commerce_metadata_local": _READ_OUTPUT_SCHEMA,
    "sync_datatable_local": _READ_OUTPUT_SCHEMA,
    "sync_datatables_local": _READ_OUTPUT_SCHEMA,
}


def get_tool_output_schema(tool_name: str) -> dict[str, Any] | None:
    """Return the MCP-compliant JSON Schema for a tool's output, if registered."""
    if tool_name in _TOOLS_WITHOUT_OUTPUT_SCHEMA:
        return None
    return TOOL_OUTPUT_SCHEMAS.get(tool_name)


def get_attachment_lead_output_schema() -> dict[str, Any]:
    """Schema for the object envelope that precedes binary attachments in list results."""
    return _ATTACHMENT_LEAD_SCHEMA


def catalog_tools_without_output_schema() -> frozenset[str]:
    """Tools whose runtime output is a list (object envelope + attachment)."""
    return _TOOLS_WITHOUT_OUTPUT_SCHEMA
