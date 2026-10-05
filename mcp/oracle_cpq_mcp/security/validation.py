"""Strict Pydantic input validation for MCP tool arguments."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
        "metrics",
        "collab",
        "admin",
        "sales",
        "prm",
        "service",
        "field_service",
        "subscription",
        "incentive_compensation",
        "all",
    ] = Field(
        default="all",
        description="Filter tools by domain, or all.",
    )
    operation: Literal["read", "write", "all"] = Field(
        default="all",
        description="Filter tools by operation, or all.",
    )
    cx_module: Literal[
        "cpq",
        "sales",
        "prm",
        "service",
        "field_service",
        "subscription",
        "incentive_compensation",
        "meta",
        "all",
    ] = Field(
        default="all",
        description=(
            "Filter tools by product module (cpq, Fusion CX slugs, or meta), or all."
        ),
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Maximum number of matching tools to return.",
    )


class ListSavedPromptsInput(_StrictModel):
    limit: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of saved prompts to return.",
    )


class SearchSavedPromptsInput(_StrictModel):
    query: str | None = Field(
        default=None,
        max_length=200,
        description="Optional substring match against title / prompt text.",
    )
    tag: str | None = Field(
        default=None,
        max_length=64,
        description="Optional tag filter (e.g. users, audit, export).",
    )
    tool_domain: str | None = Field(
        default=None,
        max_length=64,
        description="Optional tool domain filter (e.g. users, groups, commerce).",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum matches to return.",
    )


class GetSavedPromptInput(_StrictModel):
    prompt_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Saved prompt UUID from list_saved_prompts / search_saved_prompts.",
    )


class RecordPromptUseInput(_StrictModel):
    prompt_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Saved prompt UUID to mark as used.",
    )
    duration_ms: int | None = Field(
        default=None,
        ge=0,
        description=(
            "Wall-clock duration of the completed agent run in milliseconds. "
            "Required together with source when recording timed telemetry."
        ),
    )
    source: Literal["cache", "api", "mixed"] | None = Field(
        default=None,
        description=(
            "How site/cache data was obtained for this run: "
            "cache (local data/ only), api (live CPQ tools), or mixed. "
            "Averages are tracked separately per source and never blended. "
            "Required together with duration_ms when recording timed telemetry."
        ),
    )
    profile: str | None = Field(
        default=None,
        max_length=80,
        description="Optional CPQ customer profile for the run (informational).",
    )
    environment: Literal["dev", "test", "prod"] | None = Field(
        default=None,
        description="Optional CPQ environment for the run (informational).",
    )

    @model_validator(mode="after")
    def _duration_and_source_together(self) -> RecordPromptUseInput:
        has_duration = self.duration_ms is not None
        has_source = self.source is not None
        if has_duration != has_source:
            raise ValueError(
                "duration_ms and source must be provided together "
                "(or both omitted for a legacy run-count bump)."
            )
        return self


class SaveRefinedPromptInput(_StrictModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Short one-line title for the saved prompt.",
    )
    original_user_prompt: str = Field(
        ...,
        min_length=1,
        max_length=8000,
        description="The original user request that led to this refined prompt.",
    )
    refined_prompt: str = Field(
        ...,
        min_length=1,
        max_length=20000,
        description="The refined prompt markdown (prose + variables + tools).",
    )
    variables: dict[str, Any] | None = Field(
        default=None,
        description="Placeholder values from this run (secrets are stripped).",
    )
    tags: list[str] | None = Field(
        default=None,
        max_length=20,
        description="Optional tags (allowlisted domains/intents).",
    )
    tools: list[str] | None = Field(
        default=None,
        max_length=50,
        description="MCP tool names used for this task.",
    )
    output_format: Literal["chat_text", "json", "excel_download"] = Field(
        default="chat_text",
        description=(
            "How the answer was shared: chat_text (default), json, or excel_download."
        ),
    )


class OfferSaveRefinedPromptInput(SaveRefinedPromptInput):
    save: bool | None = Field(
        default=None,
        description=(
            "Omit to get a needs_user_input prompt (save once / save+always / skip); "
            "true to save; false to decline."
        ),
    )
    always: bool | None = Field(
        default=None,
        description=(
            "When save=true and always=true, also set AUTO_SAVE_REFINED_PROMPT=true "
            "in the active profile .env via set_auto_save_refined_prompt."
        ),
    )


class SetAutoSaveRefinedPromptInput(_StrictModel):
    enabled: bool = Field(
        ...,
        description=(
            "Write AUTO_SAVE_REFINED_PROMPT=true|false to the active profile .env."
        ),
    )


class StartPromptPickerInput(_StrictModel):
    mode: str | None = Field(
        default=None,
        max_length=32,
        description=(
            "Picker mode: all, search, by_tag, by_tool, last5, by_domain; "
            "omit for top-level menu."
        ),
    )
    query: str | None = Field(
        default=None,
        max_length=200,
        description="Search text when mode=search.",
    )
    tag: str | None = Field(
        default=None,
        max_length=64,
        description="Tag when mode=by_tag.",
    )
    tool_domain: str | None = Field(
        default=None,
        max_length=64,
        description="Tool domain when mode=by_domain.",
    )
    tool: str | None = Field(
        default=None,
        max_length=128,
        description="Exact MCP tool name when mode=by_tool.",
    )
    prompt_id: str | None = Field(
        default=None,
        max_length=64,
        description="Load this saved prompt id and record use (must be enabled).",
    )


class SetSavedPromptEnabledInput(_StrictModel):
    prompt_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Saved prompt UUID to enable or disable.",
    )
    enabled: bool = Field(
        ...,
        description="True to enable; false to hide from list/search/picker.",
    )


class ListLocalDataInput(_StrictModel):
    """No parameters — lists snapshots for the active profile/env."""


class EnsurePromptStudioInput(_StrictModel):
    """No parameters — probe/start local Prompt Studio on localhost."""


class GetCustomerKnowledgeInput(_StrictModel):
    """No parameters — return active profile customer knowledge markdown."""


class EnsureCustomerKnowledgeInput(_StrictModel):
    """No parameters — create stub knowledge file and wire profile field if needed."""


class AppendCustomerKnowledgeInput(_StrictModel):
    summary: str = Field(
        ...,
        min_length=1,
        max_length=8000,
        description=(
            "Concise markdown or bullet summary of discoveries to append. "
            "Do not include passwords, OAuth secrets, or tokens. "
            "Point to data/{profile}/{env}/ for large dumps."
        ),
    )
    title: str | None = Field(
        default=None,
        max_length=200,
        description="Optional section title (default: Discovery).",
    )
    tags: list[str] | None = Field(
        default=None,
        max_length=20,
        description="Optional short tags (e.g. commerce, bml, users).",
    )


class GetLocalDataStatusInput(_StrictModel):
    domain: Literal["users", "groups", "bml", "commerce", "datatables"] = Field(
        ...,
        description="Local snapshot domain to check.",
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Required for commerce snapshots (process variable name).",
    )
    table_name: str | None = Field(
        default=None,
        max_length=128,
        description="Required for datatables snapshots.",
    )


class LoadLocalDataInput(_StrictModel):
    domain: Literal["users", "groups", "bml", "commerce", "datatables"] = Field(
        ...,
        description="Local snapshot domain to load.",
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Required for commerce snapshots.",
    )
    table_name: str | None = Field(
        default=None,
        max_length=128,
        description="Required for datatables snapshots.",
    )
    include_payload: bool = Field(
        default=False,
        description="When true, include selected JSON file contents (can be large).",
    )
    payload_keys: list[str] | None = Field(
        default=None,
        max_length=20,
        description="Optional manifest path keys to include when include_payload=true.",
    )


class OfferUseLocalDataInput(_StrictModel):
    domain: Literal["users", "groups", "bml", "commerce", "datatables"] = Field(
        ...,
        description="Domain the user is about to query.",
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name when domain=commerce.",
    )
    table_name: str | None = Field(
        default=None,
        max_length=128,
        description="Data table name when domain=datatables.",
    )
    choice: Literal["use_cache", "fetch_fresh", "prefer", "never"] | None = Field(
        default=None,
        description=(
            "Omit to get needs_user_input choices; then retry with an explicit choice."
        ),
    )


class SetLocalDataPolicyInput(_StrictModel):
    policy: Literal["ask", "prefer", "never"] = Field(
        ...,
        description="Write LOCAL_DATA_POLICY=ask|prefer|never to the active profile .env.",
    )


class ExportResponseSheetInput(_StrictModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Worksheet / table title (truncated to 31 chars for Excel).",
    )
    columns: list[str] | None = Field(
        default=None,
        max_length=200,
        description="Optional column order; defaults to union of row keys.",
    )
    rows: list[dict[str, Any]] = Field(
        default_factory=list,
        max_length=10_000,
        description="Row objects (dict per row). Total rows across sheets capped at 10k.",
    )


class OfferExportResponseInput(_StrictModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Short title for the export (used in filenames and the offer question).",
    )
    sheets: list[ExportResponseSheetInput] | None = Field(
        default=None,
        max_length=20,
        description="Optional structured tables for context / pending summary (max 20 sheets).",
    )
    notes: str | None = Field(
        default=None,
        max_length=8000,
        description=(
            "Optional prose for Word exports (ignored by Excel). Prefer ## / ### "
            "headings and - / * bullets over one dense paragraph."
        ),
    )
    choice: (
        Literal["excel", "word", "both", "skip", "always_excel", "never"] | None
    ) = Field(
        default=None,
        description=(
            "Omit for needs_user_input; then retry with excel / word / both / skip / "
            "always_excel / never."
        ),
    )


class ExportResponseExcelInput(_StrictModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Export title (used in the .xlsx filename stem).",
    )
    sheets: list[ExportResponseSheetInput] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="One or more sheets: {name, columns?, rows}.",
    )
    notes: str | None = Field(
        default=None,
        max_length=8000,
        description="Optional notes (ignored for Excel; accepted for API symmetry).",
    )


class ExportResponseDiagramInput(_StrictModel):
    """Word-only Mermaid or pre-rendered PNG diagram (ignored by Excel)."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Heading 2 title above the diagram.",
    )
    mermaid: str | None = Field(
        default=None,
        max_length=16_000,
        description=(
            "Mermaid source. Rendered locally via mmdc (@mermaid-js/mermaid-cli) when "
            "on PATH; otherwise skipped (source kept as prose) unless image_path is set."
        ),
    )
    image_path: str | None = Field(
        default=None,
        max_length=500,
        description=(
            "Optional path to a pre-rendered PNG (prefer under tmp/{profile}/{env}/). "
            "Never under .config/template/. Used when mmdc is unavailable or as an override."
        ),
    )
    caption: str | None = Field(
        default=None,
        max_length=500,
        description="Optional caption under the diagram (Normal style).",
    )

    @model_validator(mode="after")
    def _require_mermaid_or_image(self) -> ExportResponseDiagramInput:
        has_mermaid = bool(self.mermaid and str(self.mermaid).strip())
        has_image = bool(self.image_path and str(self.image_path).strip())
        if not has_mermaid and not has_image:
            raise ValueError("Each diagram needs mermaid and/or image_path")
        return self


class ExportResponseWordInput(_StrictModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Document title / .docx filename stem.",
    )
    sheets: list[ExportResponseSheetInput] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="One or more tables: {name, columns?, rows}.",
    )
    notes: str | None = Field(
        default=None,
        max_length=8000,
        description=(
            "Optional intro above tables. Use newlines; ## / ### for headings; "
            "- / * for bullets (lightweight — not full Markdown)."
        ),
    )
    diagrams: list[ExportResponseDiagramInput] | None = Field(
        default=None,
        max_length=8,
        description=(
            "Optional Word-only diagrams (max 8). Each item: title plus mermaid source "
            "and/or image_path (PNG). Placed after notes and tables (best-effort Mermaid). "
            "Excel ignores this."
        ),
    )


class SetPostResponseExportInput(_StrictModel):
    policy: Literal["ask", "never", "always_excel"] = Field(
        ...,
        description=(
            "Write POST_RESPONSE_EXPORT=ask|never|always_excel to the active profile .env."
        ),
    )


class SyncUsersLocalInput(_StrictModel):
    status_filter: UserStatusFilter = Field(
        default="active",
        description="active, inactive, or all users.",
    )
    q_expr: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional CPQ MongoDB-style q expression to further filter users.",
    )
    columns: list[str] | None = Field(
        default=None,
        max_length=50,
        description="Optional Excel column names (defaults to standard user columns).",
    )


class SyncGroupsLocalInput(_StrictModel):
    """No parameters — syncs all groups for COMPANY_LOGIN_NAME."""


class SyncBmlLocalInput(_StrictModel):
    """No parameters — syncs util library functions with scriptText."""


class SyncCommerceMetadataLocalInput(_StrictModel):
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description="Commerce process variable name (defaults to profile COMMERCE_PROCESS_VAR_NAME).",
    )
    expand_all: bool = Field(
        default=True,
        description="When true, request expand=all* on metadata collections.",
    )


class SyncDatatableLocalInput(_StrictModel):
    table_name: str | None = Field(
        default=None,
        max_length=128,
        description="Data table name (defaults to CUSTOM_DATA_TABLE_NAME).",
    )


class SyncDatatablesLocalInput(_StrictModel):
    table_names: list[str] | None = Field(
        default=None,
        max_length=50,
        description="Tables to sync; defaults to all CUSTOM_DATA_TABLE_NAME* from profile.",
    )


class GetAllBmlCodeInput(_StrictModel):
    delivery: Literal["zip", "json"] = Field(
        default="zip",
        description=(
            "Return a zip attachment (zip) or a JSON summary payload (json). "
            "For large sites prefer start_bml_site_export + get_local_job."
        ),
    )


class StartBmlSiteExportInput(_StrictModel):
    """No parameters — starts a background local job for GET /adminMeta."""


class SearchLocalBmlInput(_StrictModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Substring to find in local .bml/.bmlt/.json files.",
    )
    max_matches: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum matches to return.",
    )
    case_insensitive: bool = Field(
        default=True,
        description="When true, match ignoring case.",
    )
    include_functions: bool = Field(
        default=True,
        description="Also search data/.../bml/functions/ util library extracts.",
    )


class GetLocalJobInput(_StrictModel):
    job_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Job id returned by start_bml_site_export.",
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


_ISO_TS_DESC = (
    "ISO-8601 timestamp (e.g. 2026-08-11T00:00:00.000Z). "
    "Combined into the Metrics API MongoDB-style q parameter."
)


class ListMetricsInput(_StrictModel):
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
        description="When true, request totalResults from CPQ.",
    )
    name: str | None = Field(
        default=None,
        max_length=128,
        description="Optional exact metric name filter (e.g. QUOTES); case-insensitive.",
    )
    start_time: str | None = Field(
        default=None,
        max_length=64,
        description=f"Filter startTime $gte. {_ISO_TS_DESC}",
    )
    end_time: str | None = Field(
        default=None,
        max_length=64,
        description=f"Filter endTime $lte. {_ISO_TS_DESC}",
    )
    date_modified_from: str | None = Field(
        default=None,
        max_length=64,
        description=f"Filter dateModified $gte. {_ISO_TS_DESC}",
    )
    date_modified_to: str | None = Field(
        default=None,
        max_length=64,
        description=f"Filter dateModified $lte. {_ISO_TS_DESC}",
    )
    date_added_from: str | None = Field(
        default=None,
        max_length=64,
        description=f"Filter dateAdded $gte. {_ISO_TS_DESC}",
    )
    date_added_to: str | None = Field(
        default=None,
        max_length=64,
        description=f"Filter dateAdded $lte. {_ISO_TS_DESC}",
    )


class GetCollabOperationQueueInput(_StrictModel):
    bs_id: int = Field(
        ...,
        ge=1,
        description="Commerce document / transaction bs_id for the collab queue.",
    )


class ClearCollabOperationQueueInput(_StrictModel):
    bs_id: int = Field(
        ...,
        ge=1,
        description="Commerce document / transaction bs_id whose queue will be cleared.",
    )
    dry_run: bool = Field(
        default=True,
        description="When true (default), run preflight only and do not clear the queue.",
    )
    confirmation_token: str | None = Field(
        default=None,
        max_length=2048,
        description="Server-issued token required when dry_run=false.",
    )


class GetCommerceUiSettingsInput(_StrictModel):
    """No parameters — GET /commerceUISettings."""


class ListSavedSearchesInput(_StrictModel):
    resource_var_name: str | None = Field(
        default=None,
        max_length=256,
        description=(
            "searchResources path segment (e.g. commerceDocumentsOraclecpqoTransaction). "
            "When omitted, derived from process_var_name / profile."
        ),
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description=(
            "Commerce process variable name used when resource_var_name is omitted. "
            "Defaults to profile COMMERCE_PROCESS_VAR_NAME."
        ),
    )
    show_all: Literal["ALL", "HIDDEN", "VISIBLE", "INACTIVE"] = Field(
        default="VISIBLE",
        description="Maps to CPQ showAll query (ALL|HIDDEN|VISIBLE|INACTIVE).",
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
    total_results: bool = Field(
        default=True,
        description="When true, request totalResults from CPQ.",
    )

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)

    @field_validator("resource_var_name", "process_var_name")
    @classmethod
    def validate_search_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid identifier: {v}")
        return v


class GetSavedSearchInput(_StrictModel):
    search_id: int = Field(
        ...,
        ge=1,
        description="Numeric saved search id (path searchId).",
    )
    resource_var_name: str | None = Field(
        default=None,
        max_length=256,
        description=(
            "searchResources path segment. When omitted, derived from process_var_name "
            "/ profile."
        ),
    )
    process_var_name: str | None = Field(
        default=None,
        max_length=128,
        description=(
            "Commerce process variable name used when resource_var_name is omitted."
        ),
    )

    @field_validator("resource_var_name", "process_var_name")
    @classmethod
    def validate_search_identifiers(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError(f"Invalid identifier: {v}")
        return v


class ListCertificatesInput(_StrictModel):
    """No parameters — GET /certificates."""


class GetCertificateInput(_StrictModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=256,
        pattern=CPQ_ID_PATTERN,
        description="Certificate name (path segment).",
    )


class GetSsoConfigurationInput(_StrictModel):
    """No parameters — GET /ssoConfiguration."""


class GetFusionAccessTokenInput(_StrictModel):
    include_token: bool = Field(
        default=False,
        description=(
            "When true, also return oauth_access_token (full Bearer value). "
            "Default false returns access_token_masked only."
        ),
    )


class _CxAdaptiveCollectionInput(_StrictModel):
    """Top-level CX list_* via Adaptive Search (not ADF q/finder)."""

    limit: int = Field(
        default=25,
        ge=1,
        le=200,
        description="Page size for Adaptive Search results (1–200).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based starting index for the page.",
    )
    q: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional Adaptive Search query expression object "
            '(e.g. {"op":"$eq","attribute":"PartyUniqueName","value":"Acme"}). '
            "Not ADF SCIM strings like Name LIKE '…'."
        ),
    )
    keywords: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional Adaptive Search keywords string.",
    )
    fields: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional comma-separated Adaptive Search field projection.",
    )
    order_by: str | None = Field(
        default=None,
        max_length=500,
        description=(
            "Optional sort as Attr:asc|desc (mapped to Adaptive Search sort). "
            "Example: PartyUniqueName:asc."
        ),
    )
    only_data: bool = Field(
        default=True,
        description="When true, request onlyData=true on the search call.",
    )
    total_results: bool = Field(
        default=False,
        description="When true, request totalResults=true for estimated row count.",
    )


class ListTerritoriesInput(_CxAdaptiveCollectionInput):
    pass


class _CxAdfCollectionInput(_StrictModel):
    limit: int = Field(
        default=25,
        ge=1,
        le=200,
        description="Page size for the ADF collection (1–200).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Zero-based starting index for the page.",
    )
    q: str | None = Field(default=None, max_length=2000, description="Optional ADF q expression.")
    finder: str | None = Field(default=None, max_length=1000, description="Optional finder string.")
    fields: str | None = Field(default=None, max_length=2000, description="Optional comma-separated field projection.")
    order_by: str | None = Field(default=None, max_length=500, description="Optional orderBy (e.g. Name:asc).")
    only_data: bool = Field(default=True, description="When true, request onlyData=true.")
    total_results: bool = Field(
        default=False,
        description="When true, request totalResults=true for estimated row count.",
    )


class _CxAdfItemInput(_StrictModel):
    fields: str | None = Field(default=None, max_length=2000, description="Optional comma-separated field projection.")
    only_data: bool = Field(default=True, description="When true, request onlyData=true.")
    expand: str | None = Field(default=None, max_length=2000, description="Optional expand clause for child resources.")


class GetTerritoryInput(_CxAdfItemInput):
    territory_version_id: str = Field(..., min_length=1, max_length=200, description="TerritoryVersionId path key.")


class ListAccountsInput(_CxAdaptiveCollectionInput):
    pass


class GetAccountInput(_CxAdfItemInput):
    party_number: str = Field(..., min_length=1, max_length=200, description="Account PartyNumber path key.")


class ListAccountTeamInput(_CxAdfCollectionInput):
    party_number: str = Field(..., min_length=1, max_length=200, description="Account PartyNumber for AccountTeam child.")


class GetAccountTeamMemberInput(_CxAdfItemInput):
    party_number: str = Field(..., min_length=1, max_length=200, description="Account PartyNumber.")
    account_team_uniq_id: str = Field(..., min_length=1, max_length=500, description="AccountTeamUniqId path key.")


class ListContactsInput(_CxAdaptiveCollectionInput):
    pass


class GetContactInput(_CxAdfItemInput):
    party_number: str = Field(..., min_length=1, max_length=200, description="Contact PartyNumber path key.")


class ListLeadsInput(_CxAdaptiveCollectionInput):
    pass


class GetLeadInput(_CxAdfItemInput):
    leads_uniq_id: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Lead uniq id from leads collection links/self href (leadsUniqID).",
    )


class ListLeadOpportunitiesInput(_CxAdfCollectionInput):
    leads_uniq_id: str = Field(..., min_length=1, max_length=500, description="Parent lead leadsUniqID.")


class GetLeadOpportunityInput(_CxAdfItemInput):
    leads_uniq_id: str = Field(..., min_length=1, max_length=500, description="Parent lead leadsUniqID.")
    lead_number: str = Field(..., min_length=1, max_length=200, description="LeadNumber path key.")


class ListProductsInput(_CxAdaptiveCollectionInput):
    pass


class GetProductInput(_CxAdfItemInput):
    inventory_item_id: str = Field(..., min_length=1, max_length=200, description="InventoryItemId path key.")


class ListAccountAttachmentsInput(_CxAdfCollectionInput):
    party_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Account PartyNumber for Attachment child.",
    )


class GetAccountAttachmentInput(_CxAdfItemInput):
    party_number: str = Field(..., min_length=1, max_length=200, description="Account PartyNumber.")
    attachment_uniq_id: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="AttachmentUniqID from Attachment collection links — do not invent.",
    )


class ListAccountAddressesInput(_CxAdfCollectionInput):
    party_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Account PartyNumber for Address child.",
    )


class GetAccountAddressInput(_CxAdfItemInput):
    party_number: str = Field(..., min_length=1, max_length=200, description="Account PartyNumber.")
    address_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="AddressNumber path key from Address collection.",
    )


class ListAccountPrimaryAddressesInput(_CxAdfCollectionInput):
    party_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Account PartyNumber for PrimaryAddress child.",
    )


class GetAccountPrimaryAddressInput(_CxAdfItemInput):
    party_number: str = Field(..., min_length=1, max_length=200, description="Account PartyNumber.")
    address_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="AddressNumber path key from PrimaryAddress collection.",
    )


class ListOpportunitiesInput(_CxAdaptiveCollectionInput):
    pass


class GetOpportunityInput(_CxAdfItemInput):
    opty_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="OptyNumber path key for the opportunity.",
    )


class ListOpportunityAttachmentsInput(_CxAdfCollectionInput):
    opty_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="OptyNumber for opportunity Attachment child.",
    )


class GetOpportunityAttachmentInput(_CxAdfItemInput):
    opty_number: str = Field(..., min_length=1, max_length=200, description="OptyNumber.")
    attachment_uniq_id: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="AttachmentUniqID from opportunity Attachment collection links — do not invent.",
    )


class ListOpportunityContactsInput(_CxAdfCollectionInput):
    opty_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="OptyNumber for OpportunityContact child.",
    )


class GetOpportunityContactInput(_CxAdfItemInput):
    opty_number: str = Field(..., min_length=1, max_length=200, description="OptyNumber.")
    opty_con_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="OptyConId path key from OpportunityContact collection.",
    )


class ListOpportunityRevenuePartnersInput(_CxAdfCollectionInput):
    opty_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="OptyNumber for RevenuePartnerPrimary child.",
    )


class GetOpportunityRevenuePartnerInput(_CxAdfItemInput):
    opty_number: str = Field(..., min_length=1, max_length=200, description="OptyNumber.")
    revn_part_org_party_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="RevnPartOrgPartyId path key from RevenuePartnerPrimary collection.",
    )


class ListOpportunityTeamInput(_CxAdfCollectionInput):
    opty_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="OptyNumber for OpportunityTeam child.",
    )


class ListPartnersInput(_CxAdaptiveCollectionInput):
    pass


class GetPartnerInput(_CxAdfItemInput):
    company_number: str = Field(..., min_length=1, max_length=200, description="CompanyNumber path key.")


class ListPartnerLovInput(_CxAdfCollectionInput):
    company_number: str = Field(..., min_length=1, max_length=200, description="CompanyNumber path key.")
    lov_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        pattern=r"^[A-Za-z][A-Za-z0-9_]*$",
        description=(
            "ADF LOV collection name (e.g. PartnerProfilePEO_LOVVA_For_gnx_sls_Status_c). "
            "Do not invent names; take from partner links rel=lov."
        ),
    )
    lookup_code: str | None = Field(
        default=None,
        max_length=200,
        pattern=r"^[A-Za-z0-9_]+$",
        description=(
            "Optional LookupCode filter. When set and q is omitted, the tool sends "
            'q=LookupCode="{lookup_code}". Ignored when q is provided.'
        ),
    )


class ListPartnerContactsInput(_CxAdaptiveCollectionInput):
    pass


class GetPartnerContactInput(_CxAdfItemInput):
    party_number: str = Field(..., min_length=1, max_length=200, description="Partner contact PartyNumber.")


class ListDealsInput(_CxAdaptiveCollectionInput):
    pass


class GetDealInput(_CxAdfItemInput):
    deals_uniq_id: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Deal uniq id from deals collection links/self href (dealsUniqID).",
    )


class ListPartnerContactAddressesInput(_CxAdfCollectionInput):
    party_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Partner contact PartyNumber for addresses child.",
    )


class GetPartnerContactAddressInput(_CxAdfItemInput):
    party_number: str = Field(..., min_length=1, max_length=200, description="Partner contact PartyNumber.")
    address_number: str = Field(..., min_length=1, max_length=200, description="AddressNumber path key.")


class ListPartnerContactAttachmentsInput(_CxAdfCollectionInput):
    party_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Partner contact PartyNumber for attachments child.",
    )


class GetPartnerContactAttachmentInput(_CxAdfItemInput):
    party_number: str = Field(..., min_length=1, max_length=200, description="Partner contact PartyNumber.")
    attachments_uniq_id: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="attachmentsUniqID from attachments collection links — do not invent.",
    )


class ListPartnerContactContactPointsInput(_CxAdfCollectionInput):
    party_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Partner contact PartyNumber for contactPoints child.",
    )


class GetPartnerContactContactPointInput(_CxAdfItemInput):
    party_number: str = Field(..., min_length=1, max_length=200, description="Partner contact PartyNumber.")
    contact_point_id: str = Field(
        ...,
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="Numeric ContactPointId path key.",
    )


class ListPartnerContactUserDetailsInput(_CxAdfCollectionInput):
    party_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Partner contact PartyNumber for userdetails child.",
    )


class GetPartnerContactUserDetailInput(_CxAdfItemInput):
    party_number: str = Field(..., min_length=1, max_length=200, description="Partner contact PartyNumber.")
    username: str = Field(
        ...,
        min_length=1,
        max_length=320,
        description="Username path key for partner contact userdetails.",
    )


class ListPartnerProgramsInput(_CxAdaptiveCollectionInput):
    pass


class GetPartnerProgramInput(_CxAdfItemInput):
    program_number: str = Field(..., min_length=1, max_length=200, description="ProgramNumber path key.")


class ListPartnerTiersInput(_CxAdaptiveCollectionInput):
    pass


class GetPartnerTierInput(_CxAdfItemInput):
    tier_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="TierId path key from partnerTiers collection.",
    )


class ListPartnerGeographiesInput(_CxAdfCollectionInput):
    company_number: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Partner CompanyNumber for geographies child.",
    )


class GetPartnerGeographyInput(_CxAdfItemInput):
    company_number: str = Field(..., min_length=1, max_length=200, description="Partner CompanyNumber.")
    partner_dim_members_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="PartnerDimMembersId path key from geographies collection.",
    )


class ListAdaptiveSearchMetamodelsInput(_StrictModel):
    limit: int = Field(default=25, ge=1, le=200, description="Page size (1–200).")
    offset: int = Field(default=0, ge=0, description="Zero-based page offset.")
    only_data: bool = Field(default=True, description="When true, request onlyData=true.")


class ListAdaptiveSearchEntitiesInput(_StrictModel):
    meta_model_uuid: str | None = Field(
        default=None,
        max_length=200,
        description="Optional metaModelUuid; omit to use the active metamodel.",
    )
    limit: int = Field(default=25, ge=1, le=200, description="Page size (1–200).")
    offset: int = Field(default=0, ge=0, description="Zero-based page offset.")
    only_data: bool = Field(default=True, description="When true, request onlyData=true.")


class GetAdaptiveSearchEntityInput(_StrictModel):
    entity: str = Field(..., min_length=1, max_length=200, description="Adaptive Search entity name (e.g. Account).")
    meta_model_uuid: str | None = Field(
        default=None,
        max_length=200,
        description="Optional metaModelUuid query parameter.",
    )
    only_data: bool = Field(default=True, description="When true, request onlyData=true.")


class ListAdaptiveSearchEntityAttributesInput(_StrictModel):
    entity: str = Field(..., min_length=1, max_length=200, description="Adaptive Search entity name.")
    meta_model_uuid: str | None = Field(
        default=None,
        max_length=200,
        description="Optional metaModelUuid query parameter.",
    )
    limit: int = Field(default=25, ge=1, le=200, description="Page size (1–200).")
    offset: int = Field(default=0, ge=0, description="Zero-based page offset.")
    only_data: bool = Field(default=True, description="When true, request onlyData=true.")


class ListAdaptiveSearchEntityFieldsInput(_StrictModel):
    entity: str = Field(..., min_length=1, max_length=200, description="Adaptive Search entity name.")
    meta_model_uuid: str | None = Field(
        default=None,
        max_length=200,
        description="Optional metaModelUuid query parameter.",
    )
    limit: int = Field(default=25, ge=1, le=200, description="Page size (1–200).")
    offset: int = Field(default=0, ge=0, description="Zero-based page offset.")
    only_data: bool = Field(default=True, description="When true, request onlyData=true.")


class ListAdaptiveSearchOperatorsInput(_StrictModel):
    limit: int = Field(default=25, ge=1, le=200, description="Page size (1–200).")
    offset: int = Field(default=0, ge=0, description="Zero-based page offset.")
    only_data: bool = Field(default=True, description="When true, request onlyData=true.")


class SuggestAdaptiveSearchInput(_StrictModel):
    entity: str = Field(..., min_length=1, max_length=200, description="Adaptive Search entity name for suggestions.")
    suggestion_type: Literal["filter", "field"] = Field(
        default="filter",
        description="Smart Suggest type: filter or field.",
    )
    keyword: str = Field(
        default="",
        max_length=500,
        description="Keyword for field suggestions (often empty for filter type).",
    )
    keywords: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional keywords on the suggest request body.",
    )
    q: dict[str, Any] | None = Field(
        default=None,
        description="Optional Adaptive Search query expression on the suggest request.",
    )
    fields: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional comma-separated fields for filter suggestions.",
    )
    limit: int = Field(default=25, ge=1, le=200, description="Page size (1–200).")
    offset: int = Field(default=0, ge=0, description="Zero-based page offset.")



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


class CreateTransactionInput(_StrictModel):
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
        description="Optional POST JSON body for the new transaction/quote documents payload.",
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


class NewTransactionInput(CreateTransactionInput):
    """POST .../actions/_new_transaction — same fields as create_transaction."""


class TransactionIdActionInput(_StrictModel):
    """Shared shape for POST .../{id}/actions/{action} tools."""

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
        description="Optional POST JSON body (documents, selections, criteria, etc.).",
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


class AddFromFavoritesInput(TransactionIdActionInput):
    action_var_name: str = Field(
        default="_s_addFromFavorites_t",
        max_length=128,
        description="Commerce action variable name (default _s_addFromFavorites_t; site-specific).",
    )

    @field_validator("action_var_name")
    @classmethod
    def validate_action_var_name(cls, v: str) -> str:
        if not v or not _ACTION_NAME_PATTERN.match(v):
            raise ValueError("action_var_name has invalid format")
        return v


class DisplayTransactionHistoryInput(TransactionIdActionInput):
    action_var_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description=(
            "Required site-specific display-history action variable name "
            "(Oracle docs use displayHistoryActionVarName)."
        ),
    )

    @field_validator("action_var_name")
    @classmethod
    def validate_action_var_name(cls, v: str) -> str:
        if not v or not _ACTION_NAME_PATTERN.match(v):
            raise ValueError("action_var_name has invalid format")
        return v


class SaveTransactionInput(TransactionIdActionInput):
    action_var_name: str = Field(
        default="cleanSave_t",
        max_length=128,
        description="Commerce action variable name (default cleanSave_t; site-specific).",
    )

    @field_validator("action_var_name")
    @classmethod
    def validate_action_var_name(cls, v: str) -> str:
        if not v or not _ACTION_NAME_PATTERN.match(v):
            raise ValueError("action_var_name has invalid format")
        return v


class SaveTransactionVersionInput(TransactionIdActionInput):
    action_var_name: str = Field(
        default="versionSave_t",
        max_length=128,
        description="Commerce action variable name (default versionSave_t; site-specific).",
    )

    @field_validator("action_var_name")
    @classmethod
    def validate_action_var_name(cls, v: str) -> str:
        if not v or not _ACTION_NAME_PATTERN.match(v):
            raise ValueError("action_var_name has invalid format")
        return v


class SubmitTransactionInput(TransactionIdActionInput):
    action_var_name: str = Field(
        default="submit_t",
        max_length=128,
        description="Commerce action variable name (default submit_t; site-specific).",
    )

    @field_validator("action_var_name")
    @classmethod
    def validate_action_var_name(cls, v: str) -> str:
        if not v or not _ACTION_NAME_PATTERN.match(v):
            raise ValueError("action_var_name has invalid format")
        return v


class ReconfigureTransactionInput(TransactionIdActionInput):
    """POST .../actions/_reconfigure_action (fixed system action)."""


class CreateTransactionVersionInput(TransactionIdActionInput):
    action_var_name: str = Field(
        default="versionTransaction_t",
        max_length=128,
        description="Commerce action variable name (default versionTransaction_t; site-specific).",
    )

    @field_validator("action_var_name")
    @classmethod
    def validate_action_var_name(cls, v: str) -> str:
        if not v or not _ACTION_NAME_PATTERN.match(v):
            raise ValueError("action_var_name has invalid format")
        return v


class AddTransactionLinesInput(TransactionIdActionInput):
    action_var_name: str = Field(
        default="addLineItem_t",
        max_length=128,
        description="Commerce action variable name (default addLineItem_t; site-specific).",
    )

    @field_validator("action_var_name")
    @classmethod
    def validate_action_var_name(cls, v: str) -> str:
        if not v or not _ACTION_NAME_PATTERN.match(v):
            raise ValueError("action_var_name has invalid format")
        return v


class UpdateTransactionLinesInput(TransactionIdActionInput):
    """POST .../actions/_update_line_items."""


class RemoveTransactionLinesInput(TransactionIdActionInput):
    """POST .../actions/_remove_transactionLine."""


class DeleteTransactionLineInput(_StrictModel):
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
        description="Line documentNumber to delete.",
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


class TransactionLineActionInput(_StrictModel):
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
        description="Line documentNumber.",
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
        description="Optional POST JSON body for the line action.",
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


class InteractTransactionLineInput(TransactionLineActionInput):
    """POST .../transactionLine/{dn}/actions/_interact."""


class ReconfigureTransactionLineInput(TransactionLineActionInput):
    """POST .../transactionLine/{dn}/actions/_reconfigure_action."""


class ReconfigureTransactionLineInboundInput(TransactionLineActionInput):
    """POST .../transactionLine/{dn}/actions/_reconfigure_inbound_action."""


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


class ListProductHierarchyTableInput(_StrictModel):
    page_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="CPQ page size when walking families/lines/models (1–1000).",
    )

    @field_validator("page_size")
    @classmethod
    def clamp_page_size(cls, v: int) -> int:
        return clamp_limit(v)


class ListCommerceProcessesTableInput(_StrictModel):
    page_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="CPQ page size when listing commerce process setups (1–1000).",
    )

    @field_validator("page_size")
    @classmethod
    def clamp_page_size(cls, v: int) -> int:
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
    "start_bml_site_export": StartBmlSiteExportInput,
    "search_local_bml": SearchLocalBmlInput,
    "get_local_job": GetLocalJobInput,
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
    "list_product_hierarchy_table": ListProductHierarchyTableInput,
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
    "list_commerce_processes_table": ListCommerceProcessesTableInput,
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
    "create_transaction": CreateTransactionInput,
    "new_transaction": NewTransactionInput,
    "add_from_favorites": AddFromFavoritesInput,
    "display_transaction_history": DisplayTransactionHistoryInput,
    "save_transaction": SaveTransactionInput,
    "save_transaction_version": SaveTransactionVersionInput,
    "submit_transaction": SubmitTransactionInput,
    "reconfigure_transaction": ReconfigureTransactionInput,
    "create_transaction_version": CreateTransactionVersionInput,
    "add_transaction_lines": AddTransactionLinesInput,
    "update_transaction_lines": UpdateTransactionLinesInput,
    "remove_transaction_lines": RemoveTransactionLinesInput,
    "delete_transaction_line": DeleteTransactionLineInput,
    "interact_transaction_line": InteractTransactionLineInput,
    "reconfigure_transaction_line": ReconfigureTransactionLineInput,
    "reconfigure_transaction_line_inbound": ReconfigureTransactionLineInboundInput,
    "list_performance_logs": ListPerformanceLogsInput,
    "get_performance_log": GetPerformanceLogInput,
    "export_performance_logs": ExportPerformanceLogsInput,
    "list_metrics": ListMetricsInput,
    "get_collab_operation_queue": GetCollabOperationQueueInput,
    "clear_collab_operation_queue": ClearCollabOperationQueueInput,
    "get_commerce_ui_settings": GetCommerceUiSettingsInput,
    "list_saved_searches": ListSavedSearchesInput,
    "get_saved_search": GetSavedSearchInput,
    "list_certificates": ListCertificatesInput,
    "get_certificate": GetCertificateInput,
    "get_sso_configuration": GetSsoConfigurationInput,
    "get_fusion_access_token": GetFusionAccessTokenInput,
    "list_adaptive_search_metamodels": ListAdaptiveSearchMetamodelsInput,
    "list_adaptive_search_entities": ListAdaptiveSearchEntitiesInput,
    "get_adaptive_search_entity": GetAdaptiveSearchEntityInput,
    "list_adaptive_search_entity_attributes": ListAdaptiveSearchEntityAttributesInput,
    "list_adaptive_search_entity_fields": ListAdaptiveSearchEntityFieldsInput,
    "list_adaptive_search_operators": ListAdaptiveSearchOperatorsInput,
    "suggest_adaptive_search": SuggestAdaptiveSearchInput,
    "list_territories": ListTerritoriesInput,

    "get_territory": GetTerritoryInput,
    "list_accounts": ListAccountsInput,
    "get_account": GetAccountInput,
    "list_account_team": ListAccountTeamInput,
    "get_account_team_member": GetAccountTeamMemberInput,
    "list_contacts": ListContactsInput,
    "get_contact": GetContactInput,
    "list_leads": ListLeadsInput,
    "get_lead": GetLeadInput,
    "list_lead_opportunities": ListLeadOpportunitiesInput,
    "get_lead_opportunity": GetLeadOpportunityInput,
    "list_products": ListProductsInput,
    "get_product": GetProductInput,
    "list_account_attachments": ListAccountAttachmentsInput,
    "get_account_attachment": GetAccountAttachmentInput,
    "list_account_addresses": ListAccountAddressesInput,
    "get_account_address": GetAccountAddressInput,
    "list_account_primary_addresses": ListAccountPrimaryAddressesInput,
    "get_account_primary_address": GetAccountPrimaryAddressInput,
    "list_opportunities": ListOpportunitiesInput,
    "get_opportunity": GetOpportunityInput,
    "list_opportunity_attachments": ListOpportunityAttachmentsInput,
    "get_opportunity_attachment": GetOpportunityAttachmentInput,
    "list_opportunity_contacts": ListOpportunityContactsInput,
    "get_opportunity_contact": GetOpportunityContactInput,
    "list_opportunity_revenue_partners": ListOpportunityRevenuePartnersInput,
    "get_opportunity_revenue_partner": GetOpportunityRevenuePartnerInput,
    "list_opportunity_team": ListOpportunityTeamInput,
    "list_partners": ListPartnersInput,
    "get_partner": GetPartnerInput,
    "list_partner_lov": ListPartnerLovInput,
    "list_partner_contacts": ListPartnerContactsInput,
    "get_partner_contact": GetPartnerContactInput,
    "list_deals": ListDealsInput,
    "get_deal": GetDealInput,
    "list_partner_contact_addresses": ListPartnerContactAddressesInput,
    "get_partner_contact_address": GetPartnerContactAddressInput,
    "list_partner_contact_attachments": ListPartnerContactAttachmentsInput,
    "get_partner_contact_attachment": GetPartnerContactAttachmentInput,
    "list_partner_contact_contact_points": ListPartnerContactContactPointsInput,
    "get_partner_contact_contact_point": GetPartnerContactContactPointInput,
    "list_partner_contact_user_details": ListPartnerContactUserDetailsInput,
    "get_partner_contact_user_detail": GetPartnerContactUserDetailInput,
    "list_partner_programs": ListPartnerProgramsInput,
    "get_partner_program": GetPartnerProgramInput,
    "list_partner_tiers": ListPartnerTiersInput,
    "get_partner_tier": GetPartnerTierInput,
    "list_partner_geographies": ListPartnerGeographiesInput,
    "get_partner_geography": GetPartnerGeographyInput,
    "list_parts": ListPartsInput,
    "get_part": GetPartInput,
    "search_parts": SearchPartsInput,
    "discover_tools": DiscoverToolsInput,
    "list_saved_prompts": ListSavedPromptsInput,
    "search_saved_prompts": SearchSavedPromptsInput,
    "get_saved_prompt": GetSavedPromptInput,
    "record_prompt_use": RecordPromptUseInput,
    "save_refined_prompt": SaveRefinedPromptInput,
    "offer_save_refined_prompt": OfferSaveRefinedPromptInput,
    "set_auto_save_refined_prompt": SetAutoSaveRefinedPromptInput,
    "start_prompt_picker": StartPromptPickerInput,
    "set_saved_prompt_enabled": SetSavedPromptEnabledInput,
    "list_local_data": ListLocalDataInput,
    "get_local_data_status": GetLocalDataStatusInput,
    "load_local_data": LoadLocalDataInput,
    "offer_use_local_data": OfferUseLocalDataInput,
    "set_local_data_policy": SetLocalDataPolicyInput,
    "offer_export_response": OfferExportResponseInput,
    "export_response_excel": ExportResponseExcelInput,
    "export_response_word": ExportResponseWordInput,
    "set_post_response_export": SetPostResponseExportInput,
    "ensure_prompt_studio": EnsurePromptStudioInput,
    "get_customer_knowledge": GetCustomerKnowledgeInput,
    "ensure_customer_knowledge": EnsureCustomerKnowledgeInput,
    "append_customer_knowledge": AppendCustomerKnowledgeInput,
    "sync_users_local": SyncUsersLocalInput,
    "sync_groups_local": SyncGroupsLocalInput,
    "sync_bml_local": SyncBmlLocalInput,
    "sync_commerce_metadata_local": SyncCommerceMetadataLocalInput,
    "sync_datatable_local": SyncDatatableLocalInput,
    "sync_datatables_local": SyncDatatablesLocalInput,
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
