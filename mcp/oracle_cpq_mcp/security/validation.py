"""Strict Pydantic input validation for MCP tool arguments."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from oracle_cpq_mcp.core.pagination import clamp_limit
from oracle_cpq_mcp.core.users_filters import UserStatusFilter
from oracle_cpq_mcp.security.exceptions import ValidationSecurityError

CPQ_ID_PATTERN = r"^[A-Za-z0-9_-]+$"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ListUsersInput(_StrictModel):
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size (1–1000). Clamped by the server.",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )
    status_filter: UserStatusFilter = Field(
        default="active",
        description="Filter by user status: active, inactive, or all.",
    )
    q_expr: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional CPQ MongoDB-style q expression to further filter users.",
    )

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class ExportUsersExcelInput(_StrictModel):
    status_filter: UserStatusFilter = Field(
        default="active",
        description="Filter by user status: active, inactive, or all.",
    )
    q_expr: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional CPQ MongoDB-style q expression to further filter users.",
    )
    columns: list[str] | None = Field(
        default=None,
        max_length=50,
        description="Optional Excel column names (CPQ field ids). Defaults to a standard set.",
    )

    @field_validator("columns")
    @classmethod
    def validate_columns(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for col in v:
            if len(col) > 128 or not re.match(CPQ_ID_PATTERN, col):
                raise ValueError(f"Invalid column name: {col}")
        return v


class GetUserInput(_StrictModel):
    party_number: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=CPQ_ID_PATTERN,
        description="CPQ partyNumber for the user (not the login name).",
    )


class GetUserGroupsInput(_StrictModel):
    party_number: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=CPQ_ID_PATTERN,
        description="CPQ partyNumber for the user (not the login name).",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size (1–1000).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )


class UpdateUserInput(_StrictModel):
    party_number: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=CPQ_ID_PATTERN,
        description="CPQ partyNumber for the user to patch.",
    )
    patch_body: dict[str, Any] = Field(
        ...,
        description="Non-empty JSON object of fields to change (only include intended updates).",
    )
    dry_run: bool = Field(
        default=True,
        description="When true (default), run preflight only and return a confirmation_token.",
    )
    confirmation_token: str | None = Field(
        default=None,
        max_length=512,
        description="Server-issued token required when dry_run=false to apply the change.",
    )

    @field_validator("patch_body")
    @classmethod
    def validate_patch_body(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not v:
            raise ValueError("patch_body must be non-empty")
        if len(v) > 50:
            raise ValueError("patch_body has too many fields")
        return v


class ListGroupsInput(_StrictModel):
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size (1–1000).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )


class GetGroupInput(_StrictModel):
    group_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=CPQ_ID_PATTERN,
        description="Group variableName identifier.",
    )


class ListGroupUsersInput(_StrictModel):
    group_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=CPQ_ID_PATTERN,
        description="Group variableName whose members to list.",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size (1–1000).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )


class CreateGroupInput(_StrictModel):
    group_body: dict[str, Any] = Field(
        ...,
        description="JSON body for group create; must include variableName.",
    )
    dry_run: bool = Field(
        default=True,
        description="When true (default), run preflight only and return a confirmation_token.",
    )
    confirmation_token: str | None = Field(
        default=None,
        max_length=512,
        description="Server-issued token required when dry_run=false to apply the create.",
    )

    @field_validator("group_body")
    @classmethod
    def validate_group_body(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not v:
            raise ValueError("group_body must be non-empty")
        var_name = v.get("variableName")
        if not var_name or not isinstance(var_name, str):
            raise ValueError("group_body must include variableName")
        if not re.match(CPQ_ID_PATTERN, var_name) or len(var_name) > 128:
            raise ValueError("variableName has invalid format")
        return v


class ListDatatablesInput(_StrictModel):
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size (1–1000).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )


class GetDatatableInput(_StrictModel):
    table_name: str | None = Field(
        default=None,
        max_length=128,
        description="Data table name. When omitted, uses the profile default table.",
    )

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError("table_name has invalid format")
        return v


class GetDatatableRowsInput(_StrictModel):
    table_name: str | None = Field(
        default=None,
        max_length=128,
        description="Data table name. When omitted, uses the profile default table.",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Page size (1–1000).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError("table_name has invalid format")
        return v


class DeployDatatablesInput(_StrictModel):
    table_names: list[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="One or more data table names to deploy (destructive write).",
    )
    dry_run: bool = Field(
        default=True,
        description="When true (default), run preflight only and return a confirmation_token.",
    )
    confirmation_token: str | None = Field(
        default=None,
        max_length=512,
        description="Server-issued token required when dry_run=false to apply the deploy.",
    )

    @field_validator("table_names")
    @classmethod
    def validate_table_names(cls, v: list[str]) -> list[str]:
        for name in v:
            if not name or not re.match(CPQ_ID_PATTERN, name) or len(name) > 128:
                raise ValueError(f"Invalid table name: {name}")
        return v


class DiscoverToolsInput(_StrictModel):
    query: str | None = Field(
        default=None,
        max_length=500,
        description="Optional free-text search over tool names and descriptions.",
    )
    domain: Literal[
        "users",
        "groups",
        "datatables",
        "bml",
        "commerce",
        "performance",
        "parts",
        "tasks",
        "configuration",
        "all",
    ] = Field(
        default="all",
        description="Filter tools by domain, or all.",
    )
    operation: Literal["read", "write", "all"] = Field(
        default="all",
        description="Filter tools by operation, or all.",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Maximum number of tools to return (1–50).",
    )


class GetAllBmlCodeInput(_StrictModel):
    delivery: Literal["zip", "json"] = Field(
        default="zip",
        description="Return a zip attachment (zip) or a JSON summary payload (json).",
    )


_ORDERBY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(:(asc|desc))?$", re.IGNORECASE)
_FIELD_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ACTION_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ListPerformanceLogsInput(_StrictModel):
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size (1–1000). Clamped by the server.",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )
    total_results: bool = Field(
        default=True,
        description="When true, request totalResults from CPQ (may be expensive on large logs).",
    )
    q_expr: str | None = Field(
        default=None,
        max_length=4000,
        description=(
            "Optional MongoDB-style q filter on performance log fields "
            "(e.g. {event:{$eq:'Logout'}}, {serverTime:{$gte:1000}}, "
            "{eventDate:{$gte:'2026-01-01T00:00:00.000Z'}})."
        ),
    )
    fields: list[str] | None = Field(
        default=None,
        max_length=50,
        description=(
            "Optional attribute projection (CPQ fields query param). "
            "Examples: id, event, login, serverTime, browserTime, eventDate, component, url."
        ),
    )
    orderby: list[str] | None = Field(
        default=None,
        max_length=10,
        description=(
            "Optional sort specs for CPQ orderby (e.g. serverTime:desc, eventDate:asc)."
        ),
    )

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for name in v:
            if not name or not _FIELD_NAME_PATTERN.match(name) or len(name) > 64:
                raise ValueError(f"Invalid fields entry: {name}")
        return v

    @field_validator("orderby")
    @classmethod
    def validate_orderby(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for spec in v:
            if not spec or not _ORDERBY_PATTERN.match(spec) or len(spec) > 80:
                raise ValueError(f"Invalid orderby entry: {spec}")
        return v


class GetPerformanceLogInput(_StrictModel):
    log_id: str = Field(
        ...,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="Numeric performance log event id.",
    )


class _CommerceCollectionFilters(_StrictModel):
    """Shared collection query filters for commerce document lists."""

    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size (1–1000).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )
    total_results: bool = Field(
        default=True,
        description="When true, request totalResults from CPQ.",
    )
    q_expr: str | None = Field(
        default=None,
        max_length=4000,
        description="Optional MongoDB-style q filter.",
    )
    fields: list[str] | None = Field(
        default=None,
        max_length=80,
        description="Optional attribute projection (comma-joined for CPQ fields param).",
    )
    orderby: list[str] | None = Field(
        default=None,
        max_length=10,
        description="Optional sort specs (e.g. lastUpdatedDate_t:desc).",
    )
    expand: str | None = Field(
        default=None,
        max_length=512,
        description="Optional expand relationships string (CPQ expand query param).",
    )
    exclude_field_types: str | None = Field(
        default=None,
        max_length=256,
        description="Optional excludeFieldTypes query param.",
    )

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for name in v:
            if not name or not _FIELD_NAME_PATTERN.match(name) or len(name) > 128:
                raise ValueError(f"Invalid fields entry: {name}")
        return v

    @field_validator("orderby")
    @classmethod
    def validate_orderby(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for spec in v:
            if not spec or not _ORDERBY_PATTERN.match(spec) or len(spec) > 160:
                raise ValueError(f"Invalid orderby entry: {spec}")
        return v


class ListTransactionsInput(_CommerceCollectionFilters):
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to profile COMMERCE_PROCESS_VAR_NAME.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Main document variable name (default: transaction).",
    )

    @field_validator("process_var_name", "doc_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v


class GetTransactionInput(_StrictModel):
    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="Numeric CPQ transaction id.",
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to profile COMMERCE_PROCESS_VAR_NAME.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Main document variable name (default: transaction).",
    )
    expand: str | None = Field(
        default=None,
        max_length=512,
        description="Optional expand relationships string.",
    )
    exclude_field_types: str | None = Field(
        default=None,
        max_length=256,
        description="Optional excludeFieldTypes query param.",
    )

    @field_validator("process_var_name", "doc_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v


class ListTransactionLinesInput(_CommerceCollectionFilters):
    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="Numeric CPQ transaction id whose lines to list.",
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to profile COMMERCE_PROCESS_VAR_NAME.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Main document variable name (default: transaction).",
    )

    @field_validator("process_var_name", "doc_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v


class GetTransactionLineInput(_StrictModel):
    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="Numeric CPQ transaction id.",
    )
    document_number: str = Field(
        ...,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="Line document number within the transaction.",
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to profile COMMERCE_PROCESS_VAR_NAME.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Main document variable name (default: transaction).",
    )
    expand: str | None = Field(
        default=None,
        max_length=512,
        description="Optional expand relationships string.",
    )
    exclude_field_types: str | None = Field(
        default=None,
        max_length=256,
        description="Optional excludeFieldTypes query param.",
    )

    @field_validator("process_var_name", "doc_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v


class GetDocumentLayoutInput(_StrictModel):
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to profile COMMERCE_PROCESS_VAR_NAME.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Main document variable name for layout (default: transaction).",
    )

    @field_validator("process_var_name", "doc_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v


class GenerateProposalInput(_StrictModel):
    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="Numeric CPQ transaction id.",
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to profile COMMERCE_PROCESS_VAR_NAME.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Main document variable name (default: transaction).",
    )
    body: dict[str, Any] | None = Field(
        default=None,
        description="Optional POST JSON body (criteria, documents, selections, etc.).",
    )
    dry_run: bool = Field(
        default=True,
        description="When true (default), run preflight only and return a confirmation_token.",
    )
    confirmation_token: str | None = Field(
        default=None,
        max_length=512,
        description="Server-issued token required when dry_run=false.",
    )

    @field_validator("process_var_name", "doc_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is not None and len(v) > 50:
            raise ValueError("body has too many fields")
        return v


class ExportAttachmentInput(_StrictModel):
    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="Numeric CPQ transaction id.",
    )
    attribute_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=CPQ_ID_PATTERN,
        description=(
            "Variable name of the commerce attachment attribute to export "
            "(e.g. proposalAttachment_t). Included in the POST body as selections."
        ),
    )
    action_var_name: str = Field(
        default="exportAttachment",
        min_length=1,
        max_length=128,
        pattern=CPQ_ID_PATTERN,
        description=(
            "Variable name of the Export Attachment action in the URL path "
            "(default: exportAttachment). Some sites use a custom name "
            "(e.g. Focalpoint: expAttachment)."
        ),
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to profile COMMERCE_PROCESS_VAR_NAME.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Main document variable name (default: transaction).",
    )
    body: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional POST JSON body (criteria, documents, cacheInstanceId, "
            "delta, skipIntegration, etc.). selections is set/merged from "
            "attribute_var_name."
        ),
    )
    dry_run: bool = Field(
        default=True,
        description="When true (default), run preflight only and return a confirmation_token.",
    )
    confirmation_token: str | None = Field(
        default=None,
        max_length=512,
        description="Server-issued token required when dry_run=false.",
    )

    @field_validator("process_var_name", "doc_var_name", "attribute_var_name", "action_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is not None and len(v) > 50:
            raise ValueError("body has too many fields")
        return v


class CopyTransactionInput(_StrictModel):
    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="Numeric CPQ transaction id to copy.",
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to profile COMMERCE_PROCESS_VAR_NAME.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Main document variable name (default: transaction).",
    )
    body: dict[str, Any] | None = Field(
        default=None,
        description="Optional POST JSON body (copy_sequence_id, criteria, freezePrice, etc.).",
    )
    dry_run: bool = Field(
        default=True,
        description="When true (default), run preflight only and return a confirmation_token.",
    )
    confirmation_token: str | None = Field(
        default=None,
        max_length=512,
        description="Server-issued token required when dry_run=false.",
    )

    @field_validator("process_var_name", "doc_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is not None and len(v) > 50:
            raise ValueError("body has too many fields")
        return v


class CopyTransactionLinesInput(_StrictModel):
    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="Numeric CPQ transaction id that receives copied lines.",
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to profile COMMERCE_PROCESS_VAR_NAME.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Main document variable name (default: transaction).",
    )
    action_name: str = Field(
        default="copyLineItems_t",
        max_length=128,
        description="Commerce action variable name (default copyLineItems_t; site-specific).",
    )
    body: dict[str, Any] | None = Field(
        default=None,
        description="Optional POST JSON body (selections, criteria, documents, etc.).",
    )
    dry_run: bool = Field(
        default=True,
        description="When true (default), run preflight only and return a confirmation_token.",
    )
    confirmation_token: str | None = Field(
        default=None,
        max_length=512,
        description="Server-issued token required when dry_run=false.",
    )

    @field_validator("process_var_name", "doc_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v

    @field_validator("action_name")
    @classmethod
    def validate_action_name(cls, v: str) -> str:
        if not v or not _ACTION_NAME_PATTERN.match(v):
            raise ValueError("action_name has invalid format")
        return v

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is not None and len(v) > 50:
            raise ValueError("body has too many fields")
        return v


class CommerceMetadataInput(_StrictModel):
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to the profile process when omitted.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Main document variable name (default: transaction).",
    )
    expand_all: bool = Field(
        default=False,
        description="When true, request expand=all on the commerce metadata collection.",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size (1–1000).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )

    @field_validator("process_var_name", "doc_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class LineMetadataInput(_StrictModel):
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to the profile process when omitted.",
    )
    doc_var_name: str = Field(
        default="transactionLine",
        max_length=128,
        description="Line document variable name (default: transactionLine).",
    )
    expand_all: bool = Field(
        default=False,
        description="When true, request expand=all on the line metadata collection.",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size (1–1000).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )

    @field_validator("process_var_name", "doc_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class GetCommerceAttributeInput(_StrictModel):
    attribute_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=CPQ_ID_PATTERN,
        description="Commerce attribute variable name (e.g. status_t).",
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to the profile process when omitted.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Document variable name (default: transaction).",
    )
    expand_all: bool = Field(
        default=False,
        description="When true, request expand=all on the attribute resource.",
    )

    @field_validator("process_var_name", "doc_var_name", "attribute_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v


class GetCommerceActionInput(_StrictModel):
    action_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=CPQ_ID_PATTERN,
        description="Commerce action variable name (e.g. generateProposal).",
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to the profile process when omitted.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Document variable name (default: transaction).",
    )
    expand_all: bool = Field(
        default=False,
        description="When true, request expand=all on the actionDef resource.",
    )

    @field_validator("process_var_name", "doc_var_name", "action_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v


class ListCommerceProcessesInput(_StrictModel):
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size (1–1000).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class DownloadAttachmentInput(_StrictModel):
    transaction_id: str = Field(
        ...,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="Numeric CPQ transaction id.",
    )
    attribute_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=CPQ_ID_PATTERN,
        description="Attachment attribute variable name (e.g. proposalAttachment_t).",
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name. Defaults to profile COMMERCE_PROCESS_VAR_NAME.",
    )
    doc_var_name: str = Field(
        default="transaction",
        max_length=128,
        description="Main document variable name (default: transaction).",
    )
    document_number: str = Field(
        default="1",
        min_length=1,
        max_length=32,
        description="Document number for attachment path fallback (default: 1).",
    )

    @field_validator("process_var_name", "doc_var_name", "attribute_var_name")
    @classmethod
    def validate_commerce_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid commerce identifier: {v}")
        return v


class ListDatatableFieldsInput(_StrictModel):
    table_name: str | None = Field(
        default=None,
        max_length=128,
        description="Data table name. When omitted, uses the profile default table.",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size (1–1000).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError("table_name has invalid format")
        return v

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class GetDatatableFieldInput(_StrictModel):
    field_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=CPQ_ID_PATTERN,
        description="Field/column variable name on the data table.",
    )
    table_name: str | None = Field(
        default=None,
        max_length=128,
        description="Data table name. When omitted, uses the profile default table.",
    )

    @field_validator("table_name", "field_name")
    @classmethod
    def validate_names(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError("Invalid table or field name format")
        return v


class GetBmlFunctionInput(_StrictModel):
    function_id: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description=(
            "Util library function id as namespace.variableName "
            "(e.g. util.myFunction) or variableName alone."
        ),
    )

    @field_validator("function_id")
    @classmethod
    def validate_function_id(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z0-9_.-]+$", v):
            raise ValueError("function_id has invalid format")
        return v


class ExportPerformanceLogsInput(_StrictModel):
    log_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="Optional numeric log id; when set, export that single event.",
    )
    body: dict[str, Any] | None = Field(
        default=None,
        description="Optional POST JSON body for collection export filters.",
    )
    dry_run: bool = Field(
        default=True,
        description="When true (default), run preflight only and return a confirmation_token.",
    )
    confirmation_token: str | None = Field(
        default=None,
        max_length=512,
        description="Server-issued token required when dry_run=false.",
    )

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is not None and len(v) > 50:
            raise ValueError("body has too many fields")
        return v


class ListPartsInput(_StrictModel):
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Page size (1–1000).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based offset for pagination.",
    )
    q_expr: str | None = Field(
        default=None,
        max_length=4000,
        description="Optional MongoDB-style q filter on parts.",
    )
    fields: list[str] | None = Field(
        default=None,
        max_length=50,
        description="Optional attribute projection list.",
    )

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for name in v:
            if not name or not _FIELD_NAME_PATTERN.match(name) or len(name) > 128:
                raise ValueError(f"Invalid field name: {name}")
        return v


class GetPartInput(_StrictModel):
    part_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Part id or part number path segment for GET /parts/{id}.",
    )

    @field_validator("part_id")
    @classmethod
    def validate_part_id(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z0-9_.\-]+$", v):
            raise ValueError("part_id has invalid format")
        return v


class SearchPartsInput(_StrictModel):
    body: dict[str, Any] = Field(
        ...,
        description="JSON body for POST /parts/actions/search (criteria per CPQ docs).",
    )

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not v:
            raise ValueError("body must be non-empty")
        if len(v) > 50:
            raise ValueError("body has too many fields")
        return v


_CONFIG_VAR_PATTERN = r"^[A-Za-z0-9_.-]+$"


class CreateDatatableInput(_StrictModel):
    body: dict[str, Any] = Field(
        ...,
        description="POST JSON body for /datatables (must include name).",
    )
    dry_run: bool = Field(
        default=True,
        description="When true (default), run preflight only and return a confirmation_token.",
    )
    confirmation_token: str | None = Field(
        default=None,
        max_length=512,
        description="Server-issued token required when dry_run=false.",
    )

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not v:
            raise ValueError("body must be non-empty")
        if len(v) > 50:
            raise ValueError("body has too many fields")
        name = v.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("body.name is required")
        if not re.match(CPQ_ID_PATTERN, name) or len(name) > 128:
            raise ValueError("body.name has invalid format")
        return v


class ExportDatatablesInput(_StrictModel):
    body: dict[str, Any] | None = Field(
        default=None,
        description="Optional POST JSON body for /datatables/actions/export.",
    )
    dry_run: bool = Field(
        default=True,
        description="When true (default), run preflight only and return a confirmation_token.",
    )
    confirmation_token: str | None = Field(
        default=None,
        max_length=512,
        description="Server-issued token required when dry_run=false.",
    )

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is not None and len(v) > 50:
            raise ValueError("body has too many fields")
        return v


class SearchBmlScriptsInput(_StrictModel):
    q_expr: str | None = Field(
        default=None,
        max_length=4000,
        description="Optional MongoDB-style q filter for BML script search.",
    )
    limit: int = Field(default=100, ge=1, le=1000, description="Page size (1–1000).")
    offset: int = Field(default=0, ge=0, description="Zero-based offset for pagination.")
    orderby: str | None = Field(
        default=None,
        max_length=256,
        description="Optional orderby expression.",
    )
    fields: list[str] | None = Field(
        default=None,
        max_length=50,
        description="Optional attribute projection list.",
    )

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)

    @field_validator("fields")
    @classmethod
    def validate_fields(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for name in v:
            if not name or not _FIELD_NAME_PATTERN.match(name) or len(name) > 128:
                raise ValueError(f"Invalid field name: {name}")
        return v


class ListBmlCommonFunctionsInput(_StrictModel):
    limit: int = Field(default=100, ge=1, le=1000, description="Page size (1–1000).")
    offset: int = Field(default=0, ge=0, description="Zero-based offset for pagination.")

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class GetBmlCommonFunctionInput(_StrictModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Built-in BML common function name (e.g. atoi, len).",
    )


class ListBmlLibraryFoldersInput(_StrictModel):
    limit: int = Field(default=100, ge=1, le=1000, description="Page size (1–1000).")
    offset: int = Field(default=0, ge=0, description="Zero-based offset for pagination.")

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class GetBmlDependentAttributesInput(_StrictModel):
    body: dict[str, Any] | None = Field(
        default=None,
        description="Optional POST body for dependentAttributes (function selections).",
    )

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is not None and len(v) > 50:
            raise ValueError("body has too many fields")
        return v


class ExportBmlLibraryFunctionsInput(_StrictModel):
    body: dict[str, Any] | None = Field(
        default=None,
        description="Optional POST JSON body for util library export.",
    )
    dry_run: bool = Field(
        default=True,
        description="When true (default), run preflight only and return a confirmation_token.",
    )
    confirmation_token: str | None = Field(
        default=None,
        max_length=512,
        description="Server-issued token required when dry_run=false.",
    )

    @field_validator("body")
    @classmethod
    def validate_body(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is not None and len(v) > 50:
            raise ValueError("body has too many fields")
        return v


class GetTaskInput(_StrictModel):
    task_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Task id returned by export actions.",
    )


class DownloadTaskFileInput(_StrictModel):
    task_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Task id returned by export actions.",
    )
    file_name: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="File name from the task payload to download.",
    )

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("file_name must not contain path separators")
        if not re.match(r"^[A-Za-z0-9_.\-]+$", v):
            raise ValueError("file_name has invalid format")
        return v


class ListProductFamiliesInput(_StrictModel):
    limit: int = Field(default=100, ge=1, le=1000, description="Page size (1–1000).")
    offset: int = Field(default=0, ge=0, description="Zero-based offset for pagination.")

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class GetProductFamilyInput(_StrictModel):
    prod_fam_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Product family variable name.",
    )


class ListProductLinesInput(_StrictModel):
    prod_fam_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Product family variable name.",
    )
    limit: int = Field(default=100, ge=1, le=1000, description="Page size (1–1000).")
    offset: int = Field(default=0, ge=0, description="Zero-based offset for pagination.")

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class GetProductLineInput(_StrictModel):
    prod_fam_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Product family variable name.",
    )
    prod_line_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Product line variable name.",
    )


class ListModelsInput(_StrictModel):
    prod_fam_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Product family variable name.",
    )
    prod_line_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Product line variable name.",
    )
    limit: int = Field(default=100, ge=1, le=1000, description="Page size (1–1000).")
    offset: int = Field(default=0, ge=0, description="Zero-based offset for pagination.")

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class GetModelInput(_StrictModel):
    prod_fam_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Product family variable name.",
    )
    prod_line_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Product line variable name.",
    )
    model_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Model variable name.",
    )


class _ConfigScopeBase(_StrictModel):
    scope: Literal["family", "line", "model"] = Field(
        ...,
        description="Hierarchy level: family, line, or model.",
    )
    prod_fam_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Product family variable name.",
    )
    prod_line_var_name: str | None = Field(
        default=None,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Required when scope is line or model.",
    )
    model_var_name: str | None = Field(
        default=None,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Required when scope is model.",
    )


class ListConfigAttributesInput(_ConfigScopeBase):
    limit: int = Field(default=100, ge=1, le=1000, description="Page size (1–1000).")
    offset: int = Field(default=0, ge=0, description="Zero-based offset for pagination.")

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class GetConfigAttributeInput(_ConfigScopeBase):
    attribute_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Configuration attribute variable name.",
    )


class ListArraySetsInput(_ConfigScopeBase):
    limit: int = Field(default=100, ge=1, le=1000, description="Page size (1–1000).")
    offset: int = Field(default=0, ge=0, description="Zero-based offset for pagination.")

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class GetArraySetInput(_ConfigScopeBase):
    array_set_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Array set variable name.",
    )


class ListArraySetAttributesInput(_ConfigScopeBase):
    array_set_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Array set variable name.",
    )
    limit: int = Field(default=100, ge=1, le=1000, description="Page size (1–1000).")
    offset: int = Field(default=0, ge=0, description="Zero-based offset for pagination.")

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class GetArraySetAttributeInput(_ConfigScopeBase):
    array_set_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Array set variable name.",
    )
    attribute_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Array-set attribute variable name.",
    )


class ListConfigMenuItemsInput(_ConfigScopeBase):
    parent_kind: Literal["attribute", "array_set_attribute"] = Field(
        ...,
        description="Menu items under a plain attribute or an array-set attribute.",
    )
    attribute_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Parent attribute variable name.",
    )
    array_set_var_name: str | None = Field(
        default=None,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Required when parent_kind is array_set_attribute.",
    )
    limit: int = Field(default=100, ge=1, le=1000, description="Page size (1–1000).")
    offset: int = Field(default=0, ge=0, description="Zero-based offset for pagination.")

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class GetConfigMenuItemInput(_ConfigScopeBase):
    parent_kind: Literal["attribute", "array_set_attribute"] = Field(
        ...,
        description="Menu items under a plain attribute or an array-set attribute.",
    )
    attribute_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Parent attribute variable name.",
    )
    menu_item_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Menu item id.",
    )
    array_set_var_name: str | None = Field(
        default=None,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Required when parent_kind is array_set_attribute.",
    )


class GetConfigLayoutInput(_ConfigScopeBase):
    layout_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Layout variable name.",
    )


class GetLayoutCacheAttributesInput(_StrictModel):
    prod_fam_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Product family variable name.",
    )
    prod_line_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Product line variable name.",
    )
    model_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        pattern=_CONFIG_VAR_PATTERN,
        description="Model variable name.",
    )


TOOL_INPUT_MODELS: dict[str, type[_StrictModel]] = {
    "list_users": ListUsersInput,
    "export_users_excel": ExportUsersExcelInput,
    "get_user": GetUserInput,
    "get_user_groups": GetUserGroupsInput,
    "update_user": UpdateUserInput,
    "list_groups": ListGroupsInput,
    "get_group": GetGroupInput,
    "list_group_users": ListGroupUsersInput,
    "create_group": CreateGroupInput,
    "list_datatables": ListDatatablesInput,
    "get_datatable": GetDatatableInput,
    "get_datatable_rows": GetDatatableRowsInput,
    "list_datatable_fields": ListDatatableFieldsInput,
    "get_datatable_field": GetDatatableFieldInput,
    "deploy_datatables": DeployDatatablesInput,
    "create_datatable": CreateDatatableInput,
    "export_datatables": ExportDatatablesInput,
    "get_all_bml_code": GetAllBmlCodeInput,
    "get_bml_function": GetBmlFunctionInput,
    "search_bml_scripts": SearchBmlScriptsInput,
    "list_bml_common_functions": ListBmlCommonFunctionsInput,
    "get_bml_common_function": GetBmlCommonFunctionInput,
    "list_bml_library_folders": ListBmlLibraryFoldersInput,
    "get_bml_dependent_attributes": GetBmlDependentAttributesInput,
    "export_bml_library_functions": ExportBmlLibraryFunctionsInput,
    "get_task": GetTaskInput,
    "download_task_file": DownloadTaskFileInput,
    "list_product_families": ListProductFamiliesInput,
    "get_product_family": GetProductFamilyInput,
    "list_product_lines": ListProductLinesInput,
    "get_product_line": GetProductLineInput,
    "list_models": ListModelsInput,
    "get_model": GetModelInput,
    "list_config_attributes": ListConfigAttributesInput,
    "get_config_attribute": GetConfigAttributeInput,
    "list_array_sets": ListArraySetsInput,
    "get_array_set": GetArraySetInput,
    "list_array_set_attributes": ListArraySetAttributesInput,
    "get_array_set_attribute": GetArraySetAttributeInput,
    "list_config_menu_items": ListConfigMenuItemsInput,
    "get_config_menu_item": GetConfigMenuItemInput,
    "get_config_layout": GetConfigLayoutInput,
    "get_layout_cache_attributes": GetLayoutCacheAttributesInput,
    "get_commerce_attributes": CommerceMetadataInput,
    "get_commerce_actions": CommerceMetadataInput,
    "get_commerce_attribute": GetCommerceAttributeInput,
    "get_commerce_action": GetCommerceActionInput,
    "list_commerce_processes": ListCommerceProcessesInput,
    "get_line_attributes": LineMetadataInput,
    "get_line_actions": LineMetadataInput,
    "list_transactions": ListTransactionsInput,
    "get_transaction": GetTransactionInput,
    "list_transaction_lines": ListTransactionLinesInput,
    "get_transaction_line": GetTransactionLineInput,
    "get_document_layout": GetDocumentLayoutInput,
    "generate_proposal": GenerateProposalInput,
    "export_attachment": ExportAttachmentInput,
    "download_attachment": DownloadAttachmentInput,
    "copy_transaction": CopyTransactionInput,
    "copy_transaction_lines": CopyTransactionLinesInput,
    "list_performance_logs": ListPerformanceLogsInput,
    "get_performance_log": GetPerformanceLogInput,
    "export_performance_logs": ExportPerformanceLogsInput,
    "list_parts": ListPartsInput,
    "get_part": GetPartInput,
    "search_parts": SearchPartsInput,
    "discover_tools": DiscoverToolsInput,
}


def validate_tool_input(tool_name: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize tool kwargs; raise ValidationSecurityError on failure."""
    model_cls = TOOL_INPUT_MODELS.get(tool_name)
    if model_cls is None:
        raise ValidationSecurityError(f"No validation model for tool '{tool_name}'.")
    try:
        model = model_cls.model_validate(kwargs)
    except Exception as exc:
        raise ValidationSecurityError(str(exc)) from exc
    return model.model_dump()
