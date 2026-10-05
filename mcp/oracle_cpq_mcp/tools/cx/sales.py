"""MCP tools for Oracle Fusion CX Sales REST APIs."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.cx_client import CXClient
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool
from oracle_cpq_mcp.tools.cx._common import crm_rest_path, cx_get_collection, cx_get_item, path_segment

_SALES = "Sales"


def register_sales_tools(mcp: Any, client: CXClient) -> None:
    """Register Fusion CX Sales tools on the FastMCP instance."""

    def _register(name: str, fn: Any) -> None:
        fn.__doc__ = TOOL_CATALOG[name].description
        register_tool(mcp, fn, name)

    def list_territories(
        limit: int = 25,
        offset: int = 0,
        q: str | None = None,
        finder: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
    ) -> dict[str, Any]:
        return cx_get_collection(
            client,
            crm_rest_path("territories"),
            "list_territories",
            _SALES,
            limit=limit,
            offset=offset,
            q=q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_territory(
        territory_version_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = f"{crm_rest_path('territories')}/{path_segment(territory_version_id)}"
        return cx_get_item(
            client,
            path,
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_accounts(
        limit: int = 25,
        offset: int = 0,
        q: str | None = None,
        finder: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
    ) -> dict[str, Any]:
        return cx_get_collection(
            client,
            crm_rest_path("accounts"),
            "list_accounts",
            _SALES,
            limit=limit,
            offset=offset,
            q=q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_account(
        party_number: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = f"{crm_rest_path('accounts')}/{path_segment(party_number)}"
        return cx_get_item(
            client,
            path,
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_account_team(
        party_number: str,
        limit: int = 25,
        offset: int = 0,
        q: str | None = None,
        finder: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
    ) -> dict[str, Any]:
        path = (
            f"{crm_rest_path('accounts')}/{path_segment(party_number)}/child/AccountTeam"
        )
        return cx_get_collection(
            client,
            path,
            "list_account_team",
            _SALES,
            limit=limit,
            offset=offset,
            q=q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_account_team_member(
        party_number: str,
        account_team_uniq_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = (
            f"{crm_rest_path('accounts')}/{path_segment(party_number)}"
            f"/child/AccountTeam/{path_segment(account_team_uniq_id)}"
        )
        return cx_get_item(
            client,
            path,
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_contacts(
        limit: int = 25,
        offset: int = 0,
        q: str | None = None,
        finder: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
    ) -> dict[str, Any]:
        return cx_get_collection(
            client,
            crm_rest_path("contacts"),
            "list_contacts",
            _SALES,
            limit=limit,
            offset=offset,
            q=q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_contact(
        party_number: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = f"{crm_rest_path('contacts')}/{path_segment(party_number)}"
        return cx_get_item(
            client,
            path,
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_leads(
        limit: int = 25,
        offset: int = 0,
        q: str | None = None,
        finder: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
        effective_date: str | None = None,
    ) -> dict[str, Any]:
        return cx_get_collection(
            client,
            crm_rest_path("leads"),
            "list_leads",
            _SALES,
            limit=limit,
            offset=offset,
            q=q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
            effective_date=effective_date,
        )

    def get_lead(
        leads_uniq_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = f"{crm_rest_path('leads')}/{path_segment(leads_uniq_id)}"
        return cx_get_item(
            client,
            path,
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_lead_opportunities(
        leads_uniq_id: str,
        limit: int = 25,
        offset: int = 0,
        q: str | None = None,
        finder: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
    ) -> dict[str, Any]:
        path = (
            f"{crm_rest_path('leads')}/{path_segment(leads_uniq_id)}/child/LeadOpportunity"
        )
        return cx_get_collection(
            client,
            path,
            "list_lead_opportunities",
            _SALES,
            limit=limit,
            offset=offset,
            q=q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_lead_opportunity(
        leads_uniq_id: str,
        lead_number: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = (
            f"{crm_rest_path('leads')}/{path_segment(leads_uniq_id)}"
            f"/child/LeadOpportunity/{path_segment(lead_number)}"
        )
        return cx_get_item(
            client,
            path,
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_products(
        limit: int = 25,
        offset: int = 0,
        q: str | None = None,
        finder: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
    ) -> dict[str, Any]:
        return cx_get_collection(
            client,
            crm_rest_path("products"),
            "list_products",
            _SALES,
            limit=limit,
            offset=offset,
            q=q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_product(
        inventory_item_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = f"{crm_rest_path('products')}/{path_segment(inventory_item_id)}"
        return cx_get_item(
            client,
            path,
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    for tool_name, fn in (
        ("list_territories", list_territories),
        ("get_territory", get_territory),
        ("list_accounts", list_accounts),
        ("get_account", get_account),
        ("list_account_team", list_account_team),
        ("get_account_team_member", get_account_team_member),
        ("list_contacts", list_contacts),
        ("get_contact", get_contact),
        ("list_leads", list_leads),
        ("get_lead", get_lead),
        ("list_lead_opportunities", list_lead_opportunities),
        ("get_lead_opportunity", get_lead_opportunity),
        ("list_products", list_products),
        ("get_product", get_product),
    ):
        _register(tool_name, fn)
