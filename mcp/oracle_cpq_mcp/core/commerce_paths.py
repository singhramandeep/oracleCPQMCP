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


def commerce_document_item_path(
    process_var_name: str,
    doc_var_name: str,
    resource: CommerceResource,
    item_var_name: str,
) -> str:
    """Build path to one attribute or actionDef by variable name."""
    return f"{commerce_document_path(process_var_name, doc_var_name, resource)}/{item_var_name}"


def _cap_var_name(name: str) -> str:
    """Capitalize the first character for commerceDocuments path segments."""
    if not name:
        return name
    return name[:1].upper() + name[1:]


def commerce_documents_base(
    process_var_name: str,
    doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
) -> str:
    """Build Commerce document collection base path.

    Example: oraclecpqo + transaction -> /commerceDocumentsOraclecpqoTransaction
    """
    return (
        f"/commerceDocuments{_cap_var_name(process_var_name)}"
        f"{_cap_var_name(doc_var_name)}"
    )


def commerce_layout_path(process_var_name: str, doc_var_name: str) -> str:
    """Build Commerce process document layout path."""
    return f"/commerceProcesses/{process_var_name}/layouts/{doc_var_name}"


def commerce_query_params(
    *,
    expand_all: bool,
    limit: int | None = None,
    offset: int | None = None,
) -> dict[str, Any] | None:
    """Optional query params for metadata expansion and pagination."""
    params: dict[str, Any] = {}
    if expand_all:
        params["expand"] = "all*"
    if limit is not None:
        params["limit"] = limit
        params["totalResults"] = "true"
    if offset is not None:
        params["offset"] = offset
    return params or None
