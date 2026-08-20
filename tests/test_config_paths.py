"""Tests for Configuration (productFamilies) path helpers."""

from __future__ import annotations

from oracle_cpq_mcp.core.config_paths import (
    config_array_set_attributes_path,
    config_array_sets_path,
    config_attributes_path,
    config_layout_path,
    config_menu_items_path,
    config_scope_base,
    layout_cache_attributes_path,
)


def test_config_scope_base_family() -> None:
    assert config_scope_base("family", prod_fam_var_name="fam") == "/productFamilies/fam"


def test_config_scope_base_line_requires_line() -> None:
    err = config_scope_base("line", prod_fam_var_name="fam")
    assert isinstance(err, dict)
    assert err["status"] == "error"


def test_config_scope_base_model() -> None:
    path = config_scope_base(
        "model",
        prod_fam_var_name="fam",
        prod_line_var_name="line",
        model_var_name="mod",
    )
    assert path == "/productFamilies/fam/productLines/line/models/mod"


def test_config_attributes_path() -> None:
    assert (
        config_attributes_path("family", prod_fam_var_name="fam", attribute_var_name="color")
        == "/productFamilies/fam/attributes/color"
    )


def test_config_array_set_attributes_path() -> None:
    path = config_array_set_attributes_path(
        "line",
        prod_fam_var_name="fam",
        prod_line_var_name="line",
        array_set_var_name="opts",
        attribute_var_name="qty",
    )
    assert path == (
        "/productFamilies/fam/productLines/line/arraySets/opts/attributes/qty"
    )


def test_config_menu_items_attribute_parent() -> None:
    path = config_menu_items_path(
        "family",
        parent_kind="attribute",
        prod_fam_var_name="fam",
        attribute_var_name="color",
        menu_item_id="1",
    )
    assert path == "/productFamilies/fam/attributes/color/menuItems/1"


def test_config_menu_items_array_set_parent() -> None:
    path = config_menu_items_path(
        "model",
        parent_kind="array_set_attribute",
        prod_fam_var_name="fam",
        prod_line_var_name="line",
        model_var_name="mod",
        array_set_var_name="opts",
        attribute_var_name="color",
    )
    assert path == (
        "/productFamilies/fam/productLines/line/models/mod"
        "/arraySets/opts/attributes/color/menuItems"
    )


def test_config_layout_path() -> None:
    path = config_layout_path(
        "family",
        prod_fam_var_name="fam",
        layout_var_name="default",
    )
    assert path == "/productFamilies/fam/layouts/default"


def test_layout_cache_attributes_path() -> None:
    assert (
        layout_cache_attributes_path("fam", "line", "mod")
        == "/layoutcache/fam/line/mod/attributes"
    )


def test_config_array_sets_collection() -> None:
    assert (
        config_array_sets_path("family", prod_fam_var_name="fam")
        == "/productFamilies/fam/arraySets"
    )
