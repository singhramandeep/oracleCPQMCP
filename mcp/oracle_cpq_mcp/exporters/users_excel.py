"""Build Excel workbooks from Oracle CPQ user records."""

from __future__ import annotations

import io
from typing import Any

from openpyxl import Workbook

from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.pagination import iterate_collection
from oracle_cpq_mcp.core.progress import report_tool_progress
from oracle_cpq_mcp.core.users_filters import UserStatusFilter, build_users_q

DEFAULT_COLUMNS = (
    "partyNumber",
    "login",
    "firstName",
    "lastName",
    "email",
    "status",
    "type",
    "language",
    "currency",
    "timeZone",
)

MAX_EXPORT_ROWS = 10_000
PAGE_SIZE = 100


def _display_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        display = value.get("displayValue")
        if display is not None:
            return str(display)
        nested = value.get("value")
        return "" if nested is None else str(nested)
    return str(value)


def _row_value(user: dict[str, Any], column: str) -> str:
    if column in user:
        return _display_value(user[column])
    return ""


def fetch_all_users(
    client: CPQClient,
    *,
    status_filter: UserStatusFilter = "active",
    q_expr: str | None = None,
    page_size: int = PAGE_SIZE,
    max_rows: int = MAX_EXPORT_ROWS,
) -> list[dict[str, Any]]:
    """Paginate GET /users until all rows are collected or max_rows is reached."""
    q = build_users_q(status_filter, q_expr)
    extra: dict[str, Any] = {"q": q} if q else {}

    items = iterate_collection(
        client,
        "/users",
        params=extra or None,
        page_size=page_size,
        max_items=max_rows,
        on_progress=lambda count, message: report_tool_progress(
            float(count),
            float(max_rows),
            message=message or f"Fetching users ({count}/{max_rows})",
        ),
    )
    return items


def build_users_workbook(
    users: list[dict[str, Any]],
    *,
    columns: list[str] | None = None,
) -> bytes:
    """Create an in-memory .xlsx workbook from CPQ user records."""
    selected_columns = list(columns or DEFAULT_COLUMNS)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Users"
    sheet.append(selected_columns)

    for user in users:
        sheet.append([_row_value(user, column) for column in selected_columns])

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def export_filename(customer_id: str, environment: str) -> str:
    safe_customer = customer_id.replace(" ", "_")
    safe_env = environment.replace(" ", "_")
    return f"cpq_users_{safe_customer}_{safe_env}.xlsx"
