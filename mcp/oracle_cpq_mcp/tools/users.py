"""MCP tools for Oracle CPQ Users APIs."""



from __future__ import annotations



from typing import Any



from fastmcp.utilities.types import File



from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.progress import report_tool_progress
from oracle_cpq_mcp.exporters.users_excel import (

    build_users_workbook,

    export_filename,

    fetch_all_users,

)

from oracle_cpq_mcp.core.responses import build_attachment_lead_envelope
from oracle_cpq_mcp.core.pagination import build_page_params, enrich_pagination_hint

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG

from oracle_cpq_mcp.tools._register import register_tool

from oracle_cpq_mcp.core.preflight import resolve_write_execution, run_update_user_preflight

from oracle_cpq_mcp.core.users_filters import UserStatusFilter, build_users_q





def register_user_tools(mcp: Any, client: CPQClient) -> None:

    """Register user management tools on the FastMCP instance."""



    def list_users(

        limit: int = 100,

        offset: int = 0,

        status_filter: UserStatusFilter = "active",

        q_expr: str | None = None,

    ) -> dict[str, Any]:

        extra: dict[str, Any] = {}

        q = build_users_q(status_filter, q_expr)

        if q:

            extra["q"] = q

        params = build_page_params(limit, offset, extra=extra)

        response = client.get("/users", params=params)

        return enrich_pagination_hint(response, "list_users")



    list_users.__doc__ = TOOL_CATALOG["list_users"].description

    register_tool(mcp, list_users, "list_users")



    def export_users_excel(

        status_filter: UserStatusFilter = "active",

        q_expr: str | None = None,

        columns: list[str] | None = None,

    ) -> list[str | File | dict[str, Any]]:

        report_tool_progress(0, 1, message="Starting CPQ user export")

        fetch_result = fetch_all_users(

            client,

            status_filter=status_filter,

            q_expr=q_expr,

        )

        users = fetch_result.items

        report_tool_progress(0.5, 1, message=f"Building Excel workbook for {len(users)} users")

        xlsx_bytes = build_users_workbook(users, columns=columns)

        report_tool_progress(1, 1, message="User export complete")

        filename = export_filename(

            client.profile.customer_id,

            client.profile.environment,

        )

        if fetch_result.truncated:

            summary = (

                f"Exported {len(users)} users from "

                f"{client.profile.customer_name} ({client.profile.environment}) "

                f"to {filename} (truncated at max_rows={fetch_result.max_items})."

            )

        else:

            summary = (

                f"Exported {len(users)} users from "

                f"{client.profile.customer_name} ({client.profile.environment}) "

                f"to {filename}."

            )

        return [
            build_attachment_lead_envelope(
                "export_users_excel",
                message=summary,
                filename=filename,
                extra={
                    "truncated": fetch_result.truncated,
                    "max_rows": fetch_result.max_items,
                    "row_count": len(users),
                    "has_more": fetch_result.has_more,
                },
            ),
            File(
                data=xlsx_bytes,
                format="xlsx",
                name=filename,
            ),
        ]



    export_users_excel.__doc__ = TOOL_CATALOG["export_users_excel"].description

    register_tool(mcp, export_users_excel, "export_users_excel")



    def get_user(party_number: str) -> dict[str, Any]:

        return client.get(f"/users/{party_number}")



    get_user.__doc__ = TOOL_CATALOG["get_user"].description

    register_tool(mcp, get_user, "get_user")



    def get_user_groups(

        party_number: str,

        limit: int = 100,

        offset: int = 0,

    ) -> dict[str, Any]:

        params = build_page_params(limit, offset)

        response = client.get(f"/users/{party_number}/groups", params=params)

        return enrich_pagination_hint(response, "get_user_groups")



    get_user_groups.__doc__ = TOOL_CATALOG["get_user_groups"].description

    register_tool(mcp, get_user_groups, "get_user_groups")



    def update_user(
        party_number: str,
        patch_body: dict[str, Any],
        dry_run: bool = True,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        return resolve_write_execution(
            read_only=client.profile.read_only,
            dry_run=dry_run,
            confirmation_token=confirmation_token,
            tool="update_user",
            action="update",
            preflight_fn=lambda: run_update_user_preflight(
                client, party_number, patch_body
            ),
            execute_fn=lambda: client.patch(
                f"/users/{party_number}", json_body=patch_body
            ),
        )



    update_user.__doc__ = TOOL_CATALOG["update_user"].description

    register_tool(mcp, update_user, "update_user")

