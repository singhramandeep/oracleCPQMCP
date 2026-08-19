"""Path builders and profile defaults for Commerce metadata REST APIs."""

from __future__ import annotations

from typing import Any, Literal

from oracle_cpq_mcp.core.config import CPQProfile
from oracle_cpq_mcp.core.errors import build_tool_error

CommerceResource = Literal["attributes", "actionDefs"]

DEFAULT_COMMERCE_DOC_VAR_NAME = "transaction"
DEFAULT_LINE_DOC_VAR_NAME = "transactionLine"


def resolve_process_var_name(
    profile: CPQProfile,
    process_var_name: str | None,
) -> str | dict[str, Any]:
    """Return process variable name from arg or profile, else validation error."""
    name = process_var_name or profile.commerce_process_var_name
    if not name:
        return build_tool_error(
            "VALIDATION_ERROR",
            "process_var_name is required (no COMMERCE_PROCESS_VAR_NAME in profile)",
            hint="Set COMMERCE_PROCESS_VAR_NAME in the profile .env or pass process_var_name.",
        )
    return name


def commerce_document_path(
    process_var_name: str,
    doc_var_name: str,
    resource: CommerceResource,
) -> str:
    """Build a Commerce Layout & Metadata REST path."""
    return (
        f"/commerceProcesses/{process_var_name}/documents/{doc_var_name}/{resource}"
    )


def commerce_query_params(*, expand_all: bool) -> dict[str, str] | None:
    """Optional query params for metadata expansion."""
    if not expand_all:
        return None
    return {"expand": "all*"}
