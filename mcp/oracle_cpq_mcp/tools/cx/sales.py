"""MCP tools for Oracle Fusion CX Sales REST APIs."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.cx_client import CXClient
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool
from oracle_cpq_mcp.tools.cx._common import (
    CX_AS_ENTITY_BY_TOOL,
    crm_rest_path,
    cx_adaptive_list,
    cx_get_collection,
    cx_get_item,
    path_segment,
)

_SALES = "Sales"


def register_sales_tools(mcp: Any, client: CXClient) -> None:
    """Register Fusion CX Sales tools on the FastMCP instance."""

    def _register(name: str, fn: Any) -> None:
        fn.__doc__ = TOOL_CATALOG[name].description
        register_tool(mcp, fn, name)

    def _account_child(party_number: str, child: str, *segments: str) -> str:
        path = (
            f"{crm_rest_path('accounts')}/{path_segment(party_number)}/child/{child}"
        )
        for seg in segments:
            path = f"{path}/{path_segment(seg)}"
        return path

    def _opportunity_child(opty_number: str, child: str, *segments: str) -> str:
        path = (
            f"{crm_rest_path('opportunities')}/{path_segment(opty_number)}/child/{child}"
        )
        for seg in segments:
            path = f"{path}/{path_segment(seg)}"
        return path

    def list_territories(
        limit: int = 25,
        offset: int = 0,
        q: dict[str, Any] | None = None,
        keywords: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
    ) -> dict[str, Any]:
        return cx_adaptive_list(
            client,
            "list_territories",
            _SALES,
            CX_AS_ENTITY_BY_TOOL["list_territories"],
            limit=limit,
            offset=offset,
            q=q,
            keywords=keywords,
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
        q: dict[str, Any] | None = None,
        keywords: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
    ) -> dict[str, Any]:
        return cx_adaptive_list(
            client,
            "list_accounts",
            _SALES,
            CX_AS_ENTITY_BY_TOOL["list_accounts"],
            limit=limit,
            offset=offset,
            q=q,
            keywords=keywords,
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
        return cx_get_collection(
            client,
            _account_child(party_number, "AccountTeam"),
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
        return cx_get_item(
            client,
            _account_child(party_number, "AccountTeam", account_team_uniq_id),
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_account_attachments(
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
        return cx_get_collection(
            client,
            _account_child(party_number, "Attachment"),
            "list_account_attachments",
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

    def get_account_attachment(
        party_number: str,
        attachment_uniq_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        return cx_get_item(
            client,
            _account_child(party_number, "Attachment", attachment_uniq_id),
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_account_addresses(
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
        return cx_get_collection(
            client,
            _account_child(party_number, "Address"),
            "list_account_addresses",
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

    def get_account_address(
        party_number: str,
        address_number: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        return cx_get_item(
            client,
            _account_child(party_number, "Address", address_number),
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_account_primary_addresses(
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
        return cx_get_collection(
            client,
            _account_child(party_number, "PrimaryAddress"),
            "list_account_primary_addresses",
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

    def get_account_primary_address(
        party_number: str,
        address_number: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        return cx_get_item(
            client,
            _account_child(party_number, "PrimaryAddress", address_number),
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_contacts(
        limit: int = 25,
        offset: int = 0,
        q: dict[str, Any] | None = None,
        keywords: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
    ) -> dict[str, Any]:
        return cx_adaptive_list(
            client,
            "list_contacts",
            _SALES,
            CX_AS_ENTITY_BY_TOOL["list_contacts"],
            limit=limit,
            offset=offset,
            q=q,
            keywords=keywords,
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
        q: dict[str, Any] | None = None,
        keywords: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
    ) -> dict[str, Any]:
        return cx_adaptive_list(
            client,
            "list_leads",
            _SALES,
            CX_AS_ENTITY_BY_TOOL["list_leads"],
            limit=limit,
            offset=offset,
            q=q,
            keywords=keywords,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
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
        q: dict[str, Any] | None = None,
        keywords: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
    ) -> dict[str, Any]:
        return cx_adaptive_list(
            client,
            "list_products",
            _SALES,
            CX_AS_ENTITY_BY_TOOL["list_products"],
            limit=limit,
            offset=offset,
            q=q,
            keywords=keywords,
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

    def list_opportunities(
        limit: int = 25,
        offset: int = 0,
        q: dict[str, Any] | None = None,
        keywords: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
    ) -> dict[str, Any]:
        return cx_adaptive_list(
            client,
            "list_opportunities",
            _SALES,
            CX_AS_ENTITY_BY_TOOL["list_opportunities"],
            limit=limit,
            offset=offset,
            q=q,
            keywords=keywords,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_opportunity(
        opty_number: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = f"{crm_rest_path('opportunities')}/{path_segment(opty_number)}"
        return cx_get_item(
            client,
            path,
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_opportunity_attachments(
        opty_number: str,
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
            _opportunity_child(opty_number, "Attachment"),
            "list_opportunity_attachments",
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

    def get_opportunity_attachment(
        opty_number: str,
        attachment_uniq_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        return cx_get_item(
            client,
            _opportunity_child(opty_number, "Attachment", attachment_uniq_id),
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_opportunity_contacts(
        opty_number: str,
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
            _opportunity_child(opty_number, "OpportunityContact"),
            "list_opportunity_contacts",
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

    def get_opportunity_contact(
        opty_number: str,
        opty_con_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        return cx_get_item(
            client,
            _opportunity_child(opty_number, "OpportunityContact", opty_con_id),
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_opportunity_revenue_partners(
        opty_number: str,
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
            _opportunity_child(opty_number, "RevenuePartnerPrimary"),
            "list_opportunity_revenue_partners",
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

    def get_opportunity_revenue_partner(
        opty_number: str,
        revn_part_org_party_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        return cx_get_item(
            client,
            _opportunity_child(opty_number, "RevenuePartnerPrimary", revn_part_org_party_id),
            _SALES,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_opportunity_team(
        opty_number: str,
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
            _opportunity_child(opty_number, "OpportunityTeam"),
            "list_opportunity_team",
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

    for tool_name, fn in (
        ("list_territories", list_territories),
        ("get_territory", get_territory),
        ("list_accounts", list_accounts),
        ("get_account", get_account),
        ("list_account_team", list_account_team),
        ("get_account_team_member", get_account_team_member),
        ("list_account_attachments", list_account_attachments),
        ("get_account_attachment", get_account_attachment),
        ("list_account_addresses", list_account_addresses),
        ("get_account_address", get_account_address),
        ("list_account_primary_addresses", list_account_primary_addresses),
        ("get_account_primary_address", get_account_primary_address),
        ("list_contacts", list_contacts),
        ("get_contact", get_contact),
        ("list_leads", list_leads),
        ("get_lead", get_lead),
        ("list_lead_opportunities", list_lead_opportunities),
        ("get_lead_opportunity", get_lead_opportunity),
        ("list_products", list_products),
        ("get_product", get_product),
        ("list_opportunities", list_opportunities),
        ("get_opportunity", get_opportunity),
        ("list_opportunity_attachments", list_opportunity_attachments),
        ("get_opportunity_attachment", get_opportunity_attachment),
        ("list_opportunity_contacts", list_opportunity_contacts),
        ("get_opportunity_contact", get_opportunity_contact),
        ("list_opportunity_revenue_partners", list_opportunity_revenue_partners),
        ("get_opportunity_revenue_partner", get_opportunity_revenue_partner),
        ("list_opportunity_team", list_opportunity_team),
    ):
        _register(tool_name, fn)
