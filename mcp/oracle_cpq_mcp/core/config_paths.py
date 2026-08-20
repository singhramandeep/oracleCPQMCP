"""Path builders for Configuration (productFamilies) REST APIs."""

from __future__ import annotations

from typing import Any, Literal

from oracle_cpq_mcp.core.errors import build_tool_error

ConfigScope = Literal["family", "line", "model"]
MenuParentKind = Literal["attribute", "array_set_attribute"]


def _require_var(name: str, value: str | None) -> str | dict[str, Any]:
    if not value or not str(value).strip():
        return build_tool_error(
            "VALIDATION_ERROR",
            f"{name} is required for this configuration scope.",
            hint=f"Pass a non-empty {name}.",
        )
    return str(value).strip()


def config_scope_base(
    scope: ConfigScope,
    *,
    prod_fam_var_name: str,
    prod_line_var_name: str | None = None,
    model_var_name: str | None = None,
) -> str | dict[str, Any]:
    """Build the productFamilies path prefix for family, line, or model scope."""
    fam = _require_var("prod_fam_var_name", prod_fam_var_name)
    if isinstance(fam, dict):
        return fam
    if scope == "family":
        return f"/productFamilies/{fam}"
    line = _require_var("prod_line_var_name", prod_line_var_name)
    if isinstance(line, dict):
        return line
    if scope == "line":
        return f"/productFamilies/{fam}/productLines/{line}"
    model = _require_var("model_var_name", model_var_name)
    if isinstance(model, dict):
        return model
    return f"/productFamilies/{fam}/productLines/{line}/models/{model}"


def config_attributes_path(
    scope: ConfigScope,
    *,
    prod_fam_var_name: str,
    prod_line_var_name: str | None = None,
    model_var_name: str | None = None,
    attribute_var_name: str | None = None,
) -> str | dict[str, Any]:
    base = config_scope_base(
        scope,
        prod_fam_var_name=prod_fam_var_name,
        prod_line_var_name=prod_line_var_name,
        model_var_name=model_var_name,
    )
    if isinstance(base, dict):
        return base
    if attribute_var_name:
        return f"{base}/attributes/{attribute_var_name}"
    return f"{base}/attributes"


def config_array_sets_path(
    scope: ConfigScope,
    *,
    prod_fam_var_name: str,
    prod_line_var_name: str | None = None,
    model_var_name: str | None = None,
    array_set_var_name: str | None = None,
) -> str | dict[str, Any]:
    base = config_scope_base(
        scope,
        prod_fam_var_name=prod_fam_var_name,
        prod_line_var_name=prod_line_var_name,
        model_var_name=model_var_name,
    )
    if isinstance(base, dict):
        return base
    if array_set_var_name:
        return f"{base}/arraySets/{array_set_var_name}"
    return f"{base}/arraySets"


def config_array_set_attributes_path(
    scope: ConfigScope,
    *,
    prod_fam_var_name: str,
    array_set_var_name: str,
    prod_line_var_name: str | None = None,
    model_var_name: str | None = None,
    attribute_var_name: str | None = None,
) -> str | dict[str, Any]:
    aset = config_array_sets_path(
        scope,
        prod_fam_var_name=prod_fam_var_name,
        prod_line_var_name=prod_line_var_name,
        model_var_name=model_var_name,
        array_set_var_name=array_set_var_name,
    )
    if isinstance(aset, dict):
        return aset
    if attribute_var_name:
        return f"{aset}/attributes/{attribute_var_name}"
    return f"{aset}/attributes"


def config_menu_items_path(
    scope: ConfigScope,
    *,
    parent_kind: MenuParentKind,
    prod_fam_var_name: str,
    attribute_var_name: str,
    prod_line_var_name: str | None = None,
    model_var_name: str | None = None,
    array_set_var_name: str | None = None,
    menu_item_id: str | int | None = None,
) -> str | dict[str, Any]:
    if parent_kind == "attribute":
        parent = config_attributes_path(
            scope,
            prod_fam_var_name=prod_fam_var_name,
            prod_line_var_name=prod_line_var_name,
            model_var_name=model_var_name,
            attribute_var_name=attribute_var_name,
        )
    else:
        aset_name = _require_var("array_set_var_name", array_set_var_name)
        if isinstance(aset_name, dict):
            return aset_name
        parent = config_array_set_attributes_path(
            scope,
            prod_fam_var_name=prod_fam_var_name,
            prod_line_var_name=prod_line_var_name,
            model_var_name=model_var_name,
            array_set_var_name=aset_name,
            attribute_var_name=attribute_var_name,
        )
    if isinstance(parent, dict):
        return parent
    if menu_item_id is not None and str(menu_item_id).strip():
        return f"{parent}/menuItems/{menu_item_id}"
    return f"{parent}/menuItems"


def config_layout_path(
    scope: ConfigScope,
    *,
    prod_fam_var_name: str,
    layout_var_name: str,
    prod_line_var_name: str | None = None,
    model_var_name: str | None = None,
) -> str | dict[str, Any]:
    base = config_scope_base(
        scope,
        prod_fam_var_name=prod_fam_var_name,
        prod_line_var_name=prod_line_var_name,
        model_var_name=model_var_name,
    )
    if isinstance(base, dict):
        return base
    layout = _require_var("layout_var_name", layout_var_name)
    if isinstance(layout, dict):
        return layout
    return f"{base}/layouts/{layout}"


def layout_cache_attributes_path(
    prod_fam_var_name: str,
    prod_line_var_name: str,
    model_var_name: str,
) -> str | dict[str, Any]:
    fam = _require_var("prod_fam_var_name", prod_fam_var_name)
    if isinstance(fam, dict):
        return fam
    line = _require_var("prod_line_var_name", prod_line_var_name)
    if isinstance(line, dict):
        return line
    model = _require_var("model_var_name", model_var_name)
    if isinstance(model, dict):
        return model
    return f"/layoutcache/{fam}/{line}/{model}/attributes"
