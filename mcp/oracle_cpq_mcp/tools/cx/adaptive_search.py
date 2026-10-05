"""MCP tools for Fusion CX Adaptive Search discovery and Smart Suggest."""

from __future__ import annotations

from typing import Any, Literal

from oracle_cpq_mcp.core.cx_client import CXClient
from oracle_cpq_mcp.core.pagination import enrich_pagination_hint
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool
from oracle_cpq_mcp.tools.cx._common import (
    crm_search_path,
    cx_adaptive_get,
    cx_adaptive_suggest,
    path_segment,
    require_any_cx_module,
)


def register_adaptive_search_tools(mcp: Any, client: CXClient) -> None:
    """Register Adaptive Search discovery/suggest tools (any CX module enabled)."""

    def _register(name: str, fn: Any) -> None:
        fn.__doc__ = TOOL_CATALOG[name].description
        register_tool(mcp, fn, name)

    def _collection_params(
        *,
        limit: int,
        offset: int,
        only_data: bool,
        meta_model_uuid: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "onlyData": "true" if only_data else "false",
        }
        if meta_model_uuid:
            params["metaModelUuid"] = meta_model_uuid
        return params

    def list_adaptive_search_metamodels(
        limit: int = 25,
        offset: int = 0,
        only_data: bool = True,
    ) -> dict[str, Any]:
        require_any_cx_module(client)
        response = client.get(
            crm_search_path("metaModels"),
            params=_collection_params(limit=limit, offset=offset, only_data=only_data),
        )
        if isinstance(response, dict) and ("hasMore" in response or "items" in response):
            return enrich_pagination_hint(response, "list_adaptive_search_metamodels")
        return response if isinstance(response, dict) else {"items": [], "raw": response}

    def list_adaptive_search_entities(
        meta_model_uuid: str | None = None,
        limit: int = 25,
        offset: int = 0,
        only_data: bool = True,
    ) -> dict[str, Any]:
        response = cx_adaptive_get(
            client,
            crm_search_path("entities"),
            params=_collection_params(
                limit=limit,
                offset=offset,
                only_data=only_data,
                meta_model_uuid=meta_model_uuid,
            ),
        )
        if isinstance(response, dict) and ("hasMore" in response or "items" in response):
            return enrich_pagination_hint(response, "list_adaptive_search_entities")
        return response if isinstance(response, dict) else {"items": [], "raw": response}

    def get_adaptive_search_entity(
        entity: str,
        meta_model_uuid: str | None = None,
        only_data: bool = True,
    ) -> Any:
        params: dict[str, Any] = {"onlyData": "true" if only_data else "false"}
        if meta_model_uuid:
            params["metaModelUuid"] = meta_model_uuid
        return cx_adaptive_get(
            client,
            f"{crm_search_path('entities')}/{path_segment(entity)}",
            params=params,
        )

    def list_adaptive_search_entity_attributes(
        entity: str,
        meta_model_uuid: str | None = None,
        limit: int = 25,
        offset: int = 0,
        only_data: bool = True,
    ) -> dict[str, Any]:
        path = (
            f"{crm_search_path('entities')}/{path_segment(entity)}/attributes"
        )
        response = cx_adaptive_get(
            client,
            path,
            params=_collection_params(
                limit=limit,
                offset=offset,
                only_data=only_data,
                meta_model_uuid=meta_model_uuid,
            ),
        )
        if isinstance(response, dict) and ("hasMore" in response or "items" in response):
            return enrich_pagination_hint(
                response, "list_adaptive_search_entity_attributes"
            )
        return response if isinstance(response, dict) else {"items": [], "raw": response}

    def list_adaptive_search_entity_fields(
        entity: str,
        meta_model_uuid: str | None = None,
        limit: int = 25,
        offset: int = 0,
        only_data: bool = True,
    ) -> dict[str, Any]:
        path = f"{crm_search_path('entities')}/{path_segment(entity)}/fields"
        response = cx_adaptive_get(
            client,
            path,
            params=_collection_params(
                limit=limit,
                offset=offset,
                only_data=only_data,
                meta_model_uuid=meta_model_uuid,
            ),
        )
        if isinstance(response, dict) and ("hasMore" in response or "items" in response):
            return enrich_pagination_hint(response, "list_adaptive_search_entity_fields")
        return response if isinstance(response, dict) else {"items": [], "raw": response}

    def list_adaptive_search_operators(
        limit: int = 25,
        offset: int = 0,
        only_data: bool = True,
    ) -> dict[str, Any]:
        require_any_cx_module(client)
        response = client.get(
            crm_search_path("searchOperators"),
            params=_collection_params(limit=limit, offset=offset, only_data=only_data),
        )
        if isinstance(response, dict) and ("hasMore" in response or "items" in response):
            return enrich_pagination_hint(response, "list_adaptive_search_operators")
        return response if isinstance(response, dict) else {"items": [], "raw": response}

    def suggest_adaptive_search(
        entity: str,
        suggestion_type: Literal["filter", "field"] = "filter",
        keyword: str = "",
        keywords: str | None = None,
        q: dict[str, Any] | None = None,
        fields: str | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> dict[str, Any]:
        return cx_adaptive_suggest(
            client,
            entity=entity,
            suggestions={"type": suggestion_type, "keyword": keyword},
            keywords=keywords,
            q=q,
            fields=fields,
            limit=limit,
            offset=offset,
        )

    for name, fn in (
        ("list_adaptive_search_metamodels", list_adaptive_search_metamodels),
        ("list_adaptive_search_entities", list_adaptive_search_entities),
        ("get_adaptive_search_entity", get_adaptive_search_entity),
        ("list_adaptive_search_entity_attributes", list_adaptive_search_entity_attributes),
        ("list_adaptive_search_entity_fields", list_adaptive_search_entity_fields),
        ("list_adaptive_search_operators", list_adaptive_search_operators),
        ("suggest_adaptive_search", suggest_adaptive_search),
    ):
        _register(name, fn)
