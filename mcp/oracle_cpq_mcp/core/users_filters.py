"""Build Oracle CPQ MongoDB q expressions for user list queries."""

from __future__ import annotations

from typing import Literal

UserStatusFilter = Literal["active", "inactive", "all"]

STATUS_ACTIVE = 1
STATUS_INACTIVE = 0

_STATUS_Q: dict[UserStatusFilter, str | None] = {
    "active": "{'status.value':{'$eq':1}}",
    "inactive": "{'status.value':{'$eq':0}}",
    "all": None,
}


def build_users_q(
    status_filter: UserStatusFilter = "active",
    q_expr: str | None = None,
) -> str | None:
    """Return CPQ q parameter for user status and optional custom MongoDB query."""
    status_q = _STATUS_Q[status_filter]

    if status_q and q_expr:
        return f"{{$and:[{status_q},{q_expr}]}}"
    if status_q:
        return status_q
    if q_expr:
        return q_expr
    return None
