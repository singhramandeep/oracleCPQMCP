"""Post-execution validation of tool outputs against declared MCP schemas."""

from __future__ import annotations

import logging
from typing import Any

from jsonschema import Draft202012Validator

from oracle_cpq_mcp.core.errors import build_tool_error
from oracle_cpq_mcp.core.responses import is_tool_output_envelope
from oracle_cpq_mcp.schemas.tool_outputs import (
    catalog_tools_without_output_schema,
    get_attachment_lead_output_schema,
    get_tool_output_schema,
)

logger = logging.getLogger(__name__)


class OutputValidationError(Exception):
    """Raised when a tool result fails declared output schema validation."""

    def __init__(self, tool_name: str, *, paths: list[str] | None = None) -> None:
        self.tool_name = tool_name
        self.paths = paths or []
        super().__init__(f"Output validation failed for {tool_name}")


def resolve_output_schema(tool_name: str) -> dict[str, Any] | None:
    """Return the JSON Schema used to validate a tool's runtime output."""
    schema = get_tool_output_schema(tool_name)
    if schema is not None:
        return schema
    if tool_name in catalog_tools_without_output_schema():
        return get_attachment_lead_output_schema()
    return None


def build_output_validation_error() -> dict[str, Any]:
    """Build a safe INTERNAL_ERROR envelope for output validation failures."""
    return build_tool_error(
        "INTERNAL_ERROR",
        "Tool response failed output validation.",
        hint="Retry the request; if it persists, check server logs for details.",
        details={"reason": "output_schema_validation_failed"},
    )


def _format_validation_paths(errors: list[Any]) -> list[str]:
    paths: list[str] = []
    for error in errors:
        path = ".".join(str(part) for part in error.path)
        paths.append(path or "<root>")
    return paths


def _validate_instance(tool_name: str, instance: Any, schema: dict[str, Any]) -> None:
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda err: list(err.path))
    if errors:
        paths = _format_validation_paths(errors)
        logger.warning(
            "Output schema validation failed for %s at paths: %s",
            tool_name,
            ", ".join(paths),
        )
        raise OutputValidationError(tool_name, paths=paths)

    if isinstance(instance, dict) and not is_tool_output_envelope(instance):
        logger.warning(
            "Output envelope validation failed for %s: malformed status/tool/data shape",
            tool_name,
        )
        raise OutputValidationError(tool_name, paths=["<envelope>"])


def validate_tool_output(tool_name: str, result: Any) -> None:
    """Validate *result* against the declared MCP output schema for *tool_name*."""
    schema = resolve_output_schema(tool_name)
    if schema is None:
        return

    if isinstance(result, dict):
        _validate_instance(tool_name, result, schema)
        return

    if isinstance(result, list):
        if not result:
            return
        first = result[0]
        if isinstance(first, dict):
            _validate_instance(tool_name, first, schema)
        return

    logger.warning(
        "Output validation failed for %s: unexpected result type %s",
        tool_name,
        type(result).__name__,
    )
    raise OutputValidationError(tool_name, paths=["<type>"])
