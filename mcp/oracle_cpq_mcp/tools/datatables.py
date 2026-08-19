"""MCP tools for Oracle CPQ Data Tables APIs."""



from __future__ import annotations



from typing import Any



from oracle_cpq_mcp.core.cpq_client import CPQClient

from oracle_cpq_mcp.core.errors import build_tool_error

from oracle_cpq_mcp.core.pagination import build_page_params, enrich_pagination_hint

from oracle_cpq_mcp.core.preflight import (

    resolve_write_execution,

    run_deploy_datatables_preflight,

)

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG

from oracle_cpq_mcp.tools._register import register_tool





def register_datatable_tools(mcp: Any, client: CPQClient) -> None:

    """Register data table tools on the FastMCP instance."""

    default_table = client.profile.custom_data_table_name



    def list_datatables(limit: int = 100, offset: int = 0) -> dict[str, Any]:

        params = build_page_params(limit, offset)

        response = client.get("/datatables", params=params)

        return enrich_pagination_hint(response, "list_datatables")



    list_datatables.__doc__ = TOOL_CATALOG["list_datatables"].description

    register_tool(mcp, list_datatables, "list_datatables")



    def get_datatable(table_name: str | None = None) -> dict[str, Any]:

        name = table_name or default_table

        if not name:

            return build_tool_error(

                "VALIDATION_ERROR",

                "table_name is required (no CUSTOM_DATA_TABLE_NAME in profile)",

                hint="Set CUSTOM_DATA_TABLE_NAME in the profile .env or pass table_name.",

            )

        return client.get(f"/datatables/{name}")



    get_datatable.__doc__ = TOOL_CATALOG["get_datatable"].description

    register_tool(mcp, get_datatable, "get_datatable")



    def get_datatable_rows(

        table_name: str | None = None,

        limit: int = 50,

        offset: int = 0,

    ) -> dict[str, Any]:

        name = table_name or default_table

        if not name:

            return build_tool_error(

                "VALIDATION_ERROR",

                "table_name is required (no CUSTOM_DATA_TABLE_NAME in profile)",

                hint="Set CUSTOM_DATA_TABLE_NAME in the profile .env or pass table_name.",

            )

        params = build_page_params(limit, offset)

        response = client.get(f"/adminCustom{name}", params=params)

        return enrich_pagination_hint(response, "get_datatable_rows")



    get_datatable_rows.__doc__ = TOOL_CATALOG["get_datatable_rows"].description

    register_tool(mcp, get_datatable_rows, "get_datatable_rows")



    def deploy_datatables(
        table_names: list[str],
        dry_run: bool = True,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        return resolve_write_execution(
            read_only=client.profile.read_only,
            dry_run=dry_run,
            confirmation_token=confirmation_token,
            tool="deploy_datatables",
            action="deploy",
            preflight_fn=lambda: run_deploy_datatables_preflight(client, table_names),
            execute_fn=lambda: client.post(
                "/datatables/actions/deploy",
                json_body={"selections": table_names},
            ),
        )



    deploy_datatables.__doc__ = TOOL_CATALOG["deploy_datatables"].description

    register_tool(mcp, deploy_datatables, "deploy_datatables")

