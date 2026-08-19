"""MCP tools for Oracle CPQ Groups APIs."""



from __future__ import annotations



from typing import Any



from oracle_cpq_mcp.core.cpq_client import CPQClient

from oracle_cpq_mcp.core.pagination import build_page_params, enrich_pagination_hint

from oracle_cpq_mcp.core.preflight import resolve_write_execution, run_create_group_preflight

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG

from oracle_cpq_mcp.tools._register import register_tool





def register_group_tools(mcp: Any, client: CPQClient) -> None:

    """Register group management tools on the FastMCP instance."""

    company = client.profile.company_login_name



    def list_groups(limit: int = 100, offset: int = 0) -> dict[str, Any]:

        params = build_page_params(limit, offset)

        response = client.get(f"/companies/{company}/groups", params=params)

        return enrich_pagination_hint(response, "list_groups")



    list_groups.__doc__ = TOOL_CATALOG["list_groups"].description

    register_tool(mcp, list_groups, "list_groups")



    def get_group(group_var_name: str) -> dict[str, Any]:

        return client.get(f"/companies/{company}/groups/{group_var_name}")



    get_group.__doc__ = TOOL_CATALOG["get_group"].description

    register_tool(mcp, get_group, "get_group")



    def list_group_users(

        group_var_name: str,

        limit: int = 100,

        offset: int = 0,

    ) -> dict[str, Any]:

        params = build_page_params(limit, offset)

        response = client.get(

            f"/companies/{company}/groups/{group_var_name}/users",

            params=params,

        )

        return enrich_pagination_hint(response, "list_group_users")



    list_group_users.__doc__ = TOOL_CATALOG["list_group_users"].description

    register_tool(mcp, list_group_users, "list_group_users")



    def create_group(
        group_body: dict[str, Any],
        dry_run: bool = True,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        return resolve_write_execution(
            read_only=client.profile.read_only,
            dry_run=dry_run,
            confirmation_token=confirmation_token,
            tool="create_group",
            action="create",
            preflight_fn=lambda: run_create_group_preflight(client, group_body),
            execute_fn=lambda: client.post(
                f"/companies/{company}/groups", json_body=group_body
            ),
        )



    create_group.__doc__ = TOOL_CATALOG["create_group"].description

    register_tool(mcp, create_group, "create_group")

