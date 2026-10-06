"""Tests for CPQ REST collection query param helpers."""

from __future__ import annotations

from oracle_cpq_mcp.core.cpq_collection import (
    cpq_collection_extra,
    cpq_expand_params,
    cpq_list_params,
)


def test_cpq_collection_extra_maps_oracle_params() -> None:
    extra = cpq_collection_extra(
        q_expr="{id:{$gt:1}}",
        fields=["id", "_customer_id"],
        orderby=["id:desc"],
        expand="transactionLine",
        exclude_field_types="html",
        finder="findByKeyword;keyword=Customer",
        only_data=True,
    )
    assert extra == {
        "q": "{id:{$gt:1}}",
        "fields": "id,_customer_id",
        "orderby": "id:desc",
        "expand": "transactionLine",
        "excludeFieldTypes": "html",
        "finder": "findByKeyword;keyword=Customer",
        "onlyData": "true",
    }


def test_cpq_list_params_includes_pagination() -> None:
    params = cpq_list_params(25, 10, total_results=True, q_expr="{a:1}", only_data=False)
    assert params["limit"] == 25
    assert params["offset"] == 10
    assert params["totalResults"] == "true"
    assert params["q"] == "{a:1}"
    assert params["onlyData"] == "false"


def test_cpq_expand_params_only() -> None:
    params = cpq_expand_params(expand="attributes", only_data=True)
    assert params == {"expand": "attributes", "onlyData": "true"}
