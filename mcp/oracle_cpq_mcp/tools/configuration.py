"""MCP tools for Oracle CPQ Configuration (productFamilies) APIs."""

from __future__ import annotations

from typing import Any, Literal

from oracle_cpq_mcp.core.config_paths import (
    config_array_set_attributes_path,
    config_array_sets_path,
    config_attributes_path,
    config_layout_path,
    config_menu_items_path,
    layout_cache_attributes_path,
)
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.pagination import build_page_params, enrich_pagination_hint
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool

ConfigScope = Literal["family", "line", "model"]
MenuParentKind = Literal["attribute", "array_set_attribute"]


def register_configuration_tools(mcp: Any, client: CPQClient) -> None:
    """Register productFamilies / layoutcache configuration tools."""

    def list_product_families(limit: int = 100, offset: int = 0) -> dict[str, Any]:
        params = build_page_params(limit, offset)
        response = client.get("/productFamilies", params=params)
        return enrich_pagination_hint(response, "list_product_families")

    list_product_families.__doc__ = TOOL_CATALOG["list_product_families"].description
    register_tool(mcp, list_product_families, "list_product_families")

    def get_product_family(prod_fam_var_name: str) -> dict[str, Any]:
        return client.get(f"/productFamilies/{prod_fam_var_name}")

    get_product_family.__doc__ = TOOL_CATALOG["get_product_family"].description
    register_tool(mcp, get_product_family, "get_product_family")

    def list_product_lines(
        prod_fam_var_name: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params = build_page_params(limit, offset)
        response = client.get(
            f"/productFamilies/{prod_fam_var_name}/productLines",
            params=params,
        )
        return enrich_pagination_hint(response, "list_product_lines")

    list_product_lines.__doc__ = TOOL_CATALOG["list_product_lines"].description
    register_tool(mcp, list_product_lines, "list_product_lines")

    def get_product_line(
        prod_fam_var_name: str,
        prod_line_var_name: str,
    ) -> dict[str, Any]:
        return client.get(
            f"/productFamilies/{prod_fam_var_name}/productLines/{prod_line_var_name}"
        )

    get_product_line.__doc__ = TOOL_CATALOG["get_product_line"].description
    register_tool(mcp, get_product_line, "get_product_line")

    def list_models(
        prod_fam_var_name: str,
        prod_line_var_name: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params = build_page_params(limit, offset)
        response = client.get(
            f"/productFamilies/{prod_fam_var_name}/productLines/"
            f"{prod_line_var_name}/models",
            params=params,
        )
        return enrich_pagination_hint(response, "list_models")

    list_models.__doc__ = TOOL_CATALOG["list_models"].description
    register_tool(mcp, list_models, "list_models")

    def get_model(
        prod_fam_var_name: str,
        prod_line_var_name: str,
        model_var_name: str,
    ) -> dict[str, Any]:
        return client.get(
            f"/productFamilies/{prod_fam_var_name}/productLines/"
            f"{prod_line_var_name}/models/{model_var_name}"
        )

    get_model.__doc__ = TOOL_CATALOG["get_model"].description
    register_tool(mcp, get_model, "get_model")

    def list_config_attributes(
        scope: ConfigScope,
        prod_fam_var_name: str,
        prod_line_var_name: str | None = None,
        model_var_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        path = config_attributes_path(
            scope,
            prod_fam_var_name=prod_fam_var_name,
            prod_line_var_name=prod_line_var_name,
            model_var_name=model_var_name,
        )
        if isinstance(path, dict):
            return path
        params = build_page_params(limit, offset)
        response = client.get(path, params=params)
        return enrich_pagination_hint(response, "list_config_attributes")

    list_config_attributes.__doc__ = TOOL_CATALOG["list_config_attributes"].description
    register_tool(mcp, list_config_attributes, "list_config_attributes")

    def get_config_attribute(
        scope: ConfigScope,
        prod_fam_var_name: str,
        attribute_var_name: str,
        prod_line_var_name: str | None = None,
        model_var_name: str | None = None,
    ) -> dict[str, Any]:
        path = config_attributes_path(
            scope,
            prod_fam_var_name=prod_fam_var_name,
            prod_line_var_name=prod_line_var_name,
            model_var_name=model_var_name,
            attribute_var_name=attribute_var_name,
        )
        if isinstance(path, dict):
            return path
        return client.get(path)

    get_config_attribute.__doc__ = TOOL_CATALOG["get_config_attribute"].description
    register_tool(mcp, get_config_attribute, "get_config_attribute")

    def list_array_sets(
        scope: ConfigScope,
        prod_fam_var_name: str,
        prod_line_var_name: str | None = None,
        model_var_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        path = config_array_sets_path(
            scope,
            prod_fam_var_name=prod_fam_var_name,
            prod_line_var_name=prod_line_var_name,
            model_var_name=model_var_name,
        )
        if isinstance(path, dict):
            return path
        params = build_page_params(limit, offset)
        response = client.get(path, params=params)
        return enrich_pagination_hint(response, "list_array_sets")

    list_array_sets.__doc__ = TOOL_CATALOG["list_array_sets"].description
    register_tool(mcp, list_array_sets, "list_array_sets")

    def get_array_set(
        scope: ConfigScope,
        prod_fam_var_name: str,
        array_set_var_name: str,
        prod_line_var_name: str | None = None,
        model_var_name: str | None = None,
    ) -> dict[str, Any]:
        path = config_array_sets_path(
            scope,
            prod_fam_var_name=prod_fam_var_name,
            prod_line_var_name=prod_line_var_name,
            model_var_name=model_var_name,
            array_set_var_name=array_set_var_name,
        )
        if isinstance(path, dict):
            return path
        return client.get(path)

    get_array_set.__doc__ = TOOL_CATALOG["get_array_set"].description
    register_tool(mcp, get_array_set, "get_array_set")

    def list_array_set_attributes(
        scope: ConfigScope,
        prod_fam_var_name: str,
        array_set_var_name: str,
        prod_line_var_name: str | None = None,
        model_var_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        path = config_array_set_attributes_path(
            scope,
            prod_fam_var_name=prod_fam_var_name,
            prod_line_var_name=prod_line_var_name,
            model_var_name=model_var_name,
            array_set_var_name=array_set_var_name,
        )
        if isinstance(path, dict):
            return path
        params = build_page_params(limit, offset)
        response = client.get(path, params=params)
        return enrich_pagination_hint(response, "list_array_set_attributes")

    list_array_set_attributes.__doc__ = TOOL_CATALOG["list_array_set_attributes"].description
    register_tool(mcp, list_array_set_attributes, "list_array_set_attributes")

    def get_array_set_attribute(
        scope: ConfigScope,
        prod_fam_var_name: str,
        array_set_var_name: str,
        attribute_var_name: str,
        prod_line_var_name: str | None = None,
        model_var_name: str | None = None,
    ) -> dict[str, Any]:
        path = config_array_set_attributes_path(
            scope,
            prod_fam_var_name=prod_fam_var_name,
            prod_line_var_name=prod_line_var_name,
            model_var_name=model_var_name,
            array_set_var_name=array_set_var_name,
            attribute_var_name=attribute_var_name,
        )
        if isinstance(path, dict):
            return path
        return client.get(path)

    get_array_set_attribute.__doc__ = TOOL_CATALOG["get_array_set_attribute"].description
    register_tool(mcp, get_array_set_attribute, "get_array_set_attribute")

    def list_config_menu_items(
        scope: ConfigScope,
        parent_kind: MenuParentKind,
        prod_fam_var_name: str,
        attribute_var_name: str,
        prod_line_var_name: str | None = None,
        model_var_name: str | None = None,
        array_set_var_name: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        path = config_menu_items_path(
            scope,
            parent_kind=parent_kind,
            prod_fam_var_name=prod_fam_var_name,
            attribute_var_name=attribute_var_name,
            prod_line_var_name=prod_line_var_name,
            model_var_name=model_var_name,
            array_set_var_name=array_set_var_name,
        )
        if isinstance(path, dict):
            return path
        params = build_page_params(limit, offset)
        response = client.get(path, params=params)
        return enrich_pagination_hint(response, "list_config_menu_items")

    list_config_menu_items.__doc__ = TOOL_CATALOG["list_config_menu_items"].description
    register_tool(mcp, list_config_menu_items, "list_config_menu_items")

    def get_config_menu_item(
        scope: ConfigScope,
        parent_kind: MenuParentKind,
        prod_fam_var_name: str,
        attribute_var_name: str,
        menu_item_id: str,
        prod_line_var_name: str | None = None,
        model_var_name: str | None = None,
        array_set_var_name: str | None = None,
    ) -> dict[str, Any]:
        path = config_menu_items_path(
            scope,
            parent_kind=parent_kind,
            prod_fam_var_name=prod_fam_var_name,
            attribute_var_name=attribute_var_name,
            prod_line_var_name=prod_line_var_name,
            model_var_name=model_var_name,
            array_set_var_name=array_set_var_name,
            menu_item_id=menu_item_id,
        )
        if isinstance(path, dict):
            return path
        return client.get(path)

    get_config_menu_item.__doc__ = TOOL_CATALOG["get_config_menu_item"].description
    register_tool(mcp, get_config_menu_item, "get_config_menu_item")

    def get_config_layout(
        scope: ConfigScope,
        prod_fam_var_name: str,
        layout_var_name: str,
        prod_line_var_name: str | None = None,
        model_var_name: str | None = None,
    ) -> dict[str, Any]:
        path = config_layout_path(
            scope,
            prod_fam_var_name=prod_fam_var_name,
            layout_var_name=layout_var_name,
            prod_line_var_name=prod_line_var_name,
            model_var_name=model_var_name,
        )
        if isinstance(path, dict):
            return path
        return client.get(path)

    get_config_layout.__doc__ = TOOL_CATALOG["get_config_layout"].description
    register_tool(mcp, get_config_layout, "get_config_layout")

    def get_layout_cache_attributes(
        prod_fam_var_name: str,
        prod_line_var_name: str,
        model_var_name: str,
    ) -> dict[str, Any]:
        path = layout_cache_attributes_path(
            prod_fam_var_name,
            prod_line_var_name,
            model_var_name,
        )
        if isinstance(path, dict):
            return path
        return client.get(path)

    get_layout_cache_attributes.__doc__ = TOOL_CATALOG[
        "get_layout_cache_attributes"
    ].description
    register_tool(mcp, get_layout_cache_attributes, "get_layout_cache_attributes")
