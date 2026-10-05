"""MCP tools for Oracle Fusion CX PRM REST APIs."""

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

_PRM = "PRM"


def register_prm_tools(mcp: Any, client: CXClient) -> None:
    """Register Fusion CX PRM tools on the FastMCP instance."""

    def _register(name: str, fn: Any) -> None:
        fn.__doc__ = TOOL_CATALOG[name].description
        register_tool(mcp, fn, name)

    def list_partners(
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
            "list_partners",
            _PRM,
            CX_AS_ENTITY_BY_TOOL["list_partners"],
            limit=limit,
            offset=offset,
            q=q,
            keywords=keywords,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_partner(
        company_number: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = f"{crm_rest_path('partners')}/{path_segment(company_number)}"
        return cx_get_item(
            client,
            path,
            _PRM,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_partner_contacts(
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
            "list_partner_contacts",
            _PRM,
            CX_AS_ENTITY_BY_TOOL["list_partner_contacts"],
            limit=limit,
            offset=offset,
            q=q,
            keywords=keywords,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_partner_contact(
        party_number: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = f"{crm_rest_path('partnerContacts')}/{path_segment(party_number)}"
        return cx_get_item(
            client,
            path,
            _PRM,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_deals(
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
            "list_deals",
            _PRM,
            CX_AS_ENTITY_BY_TOOL["list_deals"],
            limit=limit,
            offset=offset,
            q=q,
            keywords=keywords,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_deal(
        deals_uniq_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = f"{crm_rest_path('deals')}/{path_segment(deals_uniq_id)}"
        return cx_get_item(
            client,
            path,
            _PRM,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def _pc_child(party_number: str, child: str, *segments: str) -> str:
        path = (
            f"{crm_rest_path('partnerContacts')}/{path_segment(party_number)}"
            f"/child/{child}"
        )
        for segment in segments:
            path = f"{path}/{path_segment(segment)}"
        return path

    def _partner_child(company_number: str, child: str, *segments: str) -> str:
        path = (
            f"{crm_rest_path('partners')}/{path_segment(company_number)}"
            f"/child/{child}"
        )
        for segment in segments:
            path = f"{path}/{path_segment(segment)}"
        return path

    def _partner_lov(company_number: str, lov_name: str) -> str:
        return (
            f"{crm_rest_path('partners')}/{path_segment(company_number)}"
            f"/lov/{path_segment(lov_name)}"
        )

    def list_partner_lov(
        company_number: str,
        lov_name: str,
        limit: int = 25,
        offset: int = 0,
        q: str | None = None,
        finder: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        only_data: bool = True,
        total_results: bool = False,
        lookup_code: str | None = None,
    ) -> dict[str, Any]:
        effective_q = q
        if effective_q is None and lookup_code:
            effective_q = f'LookupCode="{lookup_code}"'
        return cx_get_collection(
            client,
            _partner_lov(company_number, lov_name),
            "list_partner_lov",
            _PRM,
            limit=limit,
            offset=offset,
            q=effective_q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def list_partner_contact_addresses(
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
            _pc_child(party_number, "addresses"),
            "list_partner_contact_addresses",
            _PRM,
            limit=limit,
            offset=offset,
            q=q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_partner_contact_address(
        party_number: str,
        address_number: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        return cx_get_item(
            client,
            _pc_child(party_number, "addresses", address_number),
            _PRM,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_partner_contact_attachments(
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
            _pc_child(party_number, "attachments"),
            "list_partner_contact_attachments",
            _PRM,
            limit=limit,
            offset=offset,
            q=q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_partner_contact_attachment(
        party_number: str,
        attachments_uniq_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        return cx_get_item(
            client,
            _pc_child(party_number, "attachments", attachments_uniq_id),
            _PRM,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_partner_contact_contact_points(
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
            _pc_child(party_number, "contactPoints"),
            "list_partner_contact_contact_points",
            _PRM,
            limit=limit,
            offset=offset,
            q=q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_partner_contact_contact_point(
        party_number: str,
        contact_point_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        return cx_get_item(
            client,
            _pc_child(party_number, "contactPoints", contact_point_id),
            _PRM,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_partner_contact_user_details(
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
            _pc_child(party_number, "userdetails"),
            "list_partner_contact_user_details",
            _PRM,
            limit=limit,
            offset=offset,
            q=q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_partner_contact_user_detail(
        party_number: str,
        username: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        return cx_get_item(
            client,
            _pc_child(party_number, "userdetails", username),
            _PRM,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_partner_programs(
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
            "list_partner_programs",
            _PRM,
            CX_AS_ENTITY_BY_TOOL["list_partner_programs"],
            limit=limit,
            offset=offset,
            q=q,
            keywords=keywords,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_partner_program(
        program_number: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = f"{crm_rest_path('partnerPrograms')}/{path_segment(program_number)}"
        return cx_get_item(
            client,
            path,
            _PRM,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_partner_tiers(
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
            "list_partner_tiers",
            _PRM,
            CX_AS_ENTITY_BY_TOOL["list_partner_tiers"],
            limit=limit,
            offset=offset,
            q=q,
            keywords=keywords,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_partner_tier(
        tier_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        path = f"{crm_rest_path('partnerTiers')}/{path_segment(tier_id)}"
        return cx_get_item(
            client,
            path,
            _PRM,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    def list_partner_geographies(
        company_number: str,
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
            _partner_child(company_number, "geographies"),
            "list_partner_geographies",
            _PRM,
            limit=limit,
            offset=offset,
            q=q,
            finder=finder,
            fields=fields,
            order_by=order_by,
            only_data=only_data,
            total_results=total_results,
        )

    def get_partner_geography(
        company_number: str,
        partner_dim_members_id: str,
        fields: str | None = None,
        only_data: bool = True,
        expand: str | None = None,
    ) -> Any:
        return cx_get_item(
            client,
            _partner_child(company_number, "geographies", partner_dim_members_id),
            _PRM,
            fields=fields,
            only_data=only_data,
            expand=expand,
        )

    for tool_name, fn in (
        ("list_partners", list_partners),
        ("get_partner", get_partner),
        ("list_partner_lov", list_partner_lov),
        ("list_partner_contacts", list_partner_contacts),
        ("get_partner_contact", get_partner_contact),
        ("list_deals", list_deals),
        ("get_deal", get_deal),
        ("list_partner_contact_addresses", list_partner_contact_addresses),
        ("get_partner_contact_address", get_partner_contact_address),
        ("list_partner_contact_attachments", list_partner_contact_attachments),
        ("get_partner_contact_attachment", get_partner_contact_attachment),
        ("list_partner_contact_contact_points", list_partner_contact_contact_points),
        ("get_partner_contact_contact_point", get_partner_contact_contact_point),
        ("list_partner_contact_user_details", list_partner_contact_user_details),
        ("get_partner_contact_user_detail", get_partner_contact_user_detail),
        ("list_partner_programs", list_partner_programs),
        ("get_partner_program", get_partner_program),
        ("list_partner_tiers", list_partner_tiers),
        ("get_partner_tier", get_partner_tier),
        ("list_partner_geographies", list_partner_geographies),
        ("get_partner_geography", get_partner_geography),
    ):
        _register(tool_name, fn)
