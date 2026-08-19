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
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
    status_filter: UserStatusFilter = "active"
    q_expr: str | None = Field(default=None, max_length=2000)

    @field_validator("limit")
    @classmethod
    def clamp_limit_field(cls, v: int) -> int:
        return clamp_limit(v)


class ExportUsersExcelInput(_StrictModel):
    status_filter: UserStatusFilter = "active"
    q_expr: str | None = Field(default=None, max_length=2000)
    columns: list[str] | None = Field(default=None, max_length=50)

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
    party_number: str = Field(..., min_length=1, max_length=64, pattern=CPQ_ID_PATTERN)


class GetUserGroupsInput(_StrictModel):
    party_number: str = Field(..., min_length=1, max_length=64, pattern=CPQ_ID_PATTERN)
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class UpdateUserInput(_StrictModel):
    party_number: str = Field(..., min_length=1, max_length=64, pattern=CPQ_ID_PATTERN)
    patch_body: dict[str, Any] = Field(...)
    dry_run: bool = True
    confirmation_token: str | None = Field(default=None, max_length=512)

    @field_validator("patch_body")
    @classmethod
    def validate_patch_body(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not v:
            raise ValueError("patch_body must be non-empty")
        if len(v) > 50:
            raise ValueError("patch_body has too many fields")
        return v


class ListGroupsInput(_StrictModel):
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class GetGroupInput(_StrictModel):
    group_var_name: str = Field(..., min_length=1, max_length=128, pattern=CPQ_ID_PATTERN)


class ListGroupUsersInput(_StrictModel):
    group_var_name: str = Field(..., min_length=1, max_length=128, pattern=CPQ_ID_PATTERN)
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class CreateGroupInput(_StrictModel):
    group_body: dict[str, Any] = Field(...)
    dry_run: bool = True
    confirmation_token: str | None = Field(default=None, max_length=512)

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
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class GetDatatableInput(_StrictModel):
    table_name: str | None = Field(default=None, max_length=128)

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError("table_name has invalid format")
        return v


class GetDatatableRowsInput(_StrictModel):
    table_name: str | None = Field(default=None, max_length=128)
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str | None) -> str | None:
        if v is not None and not re.match(CPQ_ID_PATTERN, v):
            raise ValueError("table_name has invalid format")
        return v


class DeployDatatablesInput(_StrictModel):
    table_names: list[str] = Field(..., min_length=1, max_length=20)
    dry_run: bool = True
    confirmation_token: str | None = Field(default=None, max_length=512)

    @field_validator("table_names")
    @classmethod
    def validate_table_names(cls, v: list[str]) -> list[str]:
        for name in v:
            if not name or not re.match(CPQ_ID_PATTERN, name) or len(name) > 128:
                raise ValueError(f"Invalid table name: {name}")
        return v


class DiscoverToolsInput(_StrictModel):
    query: str | None = Field(default=None, max_length=500)
    domain: Literal["users", "groups", "datatables", "bml", "all"] = "all"
    operation: Literal["read", "write", "all"] = "all"
    limit: int = Field(default=20, ge=1, le=50)


class GetAllBmlCodeInput(_StrictModel):
    delivery: Literal["zip", "json"] = "zip"


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
    "deploy_datatables": DeployDatatablesInput,
    "get_all_bml_code": GetAllBmlCodeInput,
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
