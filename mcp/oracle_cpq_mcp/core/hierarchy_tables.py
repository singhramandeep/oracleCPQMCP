"""Build flat product-hierarchy and commerce-process tables from live CPQ."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.pagination import build_page_params, clamp_limit

DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_FAMILIES = 500

PRODUCT_HIERARCHY_COLUMNS: list[str] = [
    "family_variable_name",
    "family_name",
    "line_variable_name",
    "line_name",
    "model_variable_name",
    "model_name",
    "family_description",
    "line_description",
    "model_description",
]

COMMERCE_PROCESS_COLUMNS: list[str] = [
    "variable_name",
    "name",
    "description",
    "id",
    "label",
]


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def page_all(
    client: CPQClient,
    path: str,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_items: int | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch all items from a paginated CPQ collection.

    Returns ``(items, truncated)``. When ``max_items`` is set, stops once that
    many items are collected; ``truncated`` is True if more remain.
    """
    limit = clamp_limit(page_size)
    offset = 0
    items: list[dict[str, Any]] = []
    truncated = False
    while True:
        remaining = None if max_items is None else max(0, max_items - len(items))
        if remaining is not None and remaining == 0:
            # Cap hit — check whether more exist without consuming them all.
            probe = client.get(
                path, params=build_page_params(1, offset, total_results=False)
            )
            truncated = bool((probe.get("items") or []) or probe.get("hasMore"))
            break
        fetch_limit = limit if remaining is None else min(limit, remaining)
        response = client.get(
            path,
            params=build_page_params(fetch_limit, offset, total_results=False),
        )
        chunk = response.get("items") or []
        for entry in chunk:
            if isinstance(entry, dict):
                items.append(entry)
        has_more = bool(response.get("hasMore"))
        if not chunk:
            break
        offset += len(chunk)
        if max_items is not None and len(items) >= max_items:
            truncated = has_more or len(chunk) == fetch_limit and has_more
            if has_more:
                truncated = True
            break
        if not has_more:
            break
    return items, truncated


def normalize_family(item: dict[str, Any]) -> dict[str, str]:
    return {
        "variable_name": _text(item.get("variableName") or item.get("varName")),
        "name": _text(item.get("label") or item.get("name") or item.get("displayName")),
        "description": _text(
            item.get("description") or item.get("_bm_pfam_description")
        ),
    }


def normalize_line(item: dict[str, Any]) -> dict[str, str]:
    return {
        "variable_name": _text(
            item.get("_bm_pline_variable_name")
            or item.get("variableName")
            or item.get("varName")
        ),
        "name": _text(
            item.get("_bm_pline_name")
            or item.get("label")
            or item.get("name")
            or item.get("displayName")
        ),
        "description": _text(
            item.get("_bm_pline_description") or item.get("description")
        ),
    }


def normalize_model(item: dict[str, Any]) -> dict[str, str]:
    return {
        "variable_name": _text(
            item.get("_bm_model_variable_name")
            or item.get("variableName")
            or item.get("varName")
        ),
        "name": _text(
            item.get("_bm_model_name")
            or item.get("label")
            or item.get("name")
            or item.get("displayName")
        ),
        "description": _text(
            item.get("_bm_model_description") or item.get("description")
        ),
    }


def normalize_commerce_process(item: dict[str, Any]) -> dict[str, Any]:
    name = _text(item.get("name") or item.get("label") or item.get("displayName"))
    label = _text(item.get("label"))
    return {
        "variable_name": _text(item.get("variableName") or item.get("varName")),
        "name": name,
        "description": _text(item.get("description")),
        "id": item.get("id", ""),
        "label": label,
    }


def build_product_hierarchy_table(
    client: CPQClient,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_families: int = DEFAULT_MAX_FAMILIES,
) -> dict[str, Any]:
    """Walk productFamilies → productLines → models into a flat table."""
    families, fam_truncated = page_all(
        client,
        "/productFamilies",
        page_size=page_size,
        max_items=max_families,
    )
    rows: list[dict[str, str]] = []
    line_count = 0
    model_count = 0
    message = ""

    for family in families:
        fam = normalize_family(family)
        fam_var = fam["variable_name"]
        if not fam_var:
            rows.append(
                {
                    "family_variable_name": "",
                    "family_name": fam["name"],
                    "line_variable_name": "",
                    "line_name": "",
                    "model_variable_name": "",
                    "model_name": "",
                    "family_description": fam["description"],
                    "line_description": "",
                    "model_description": "",
                }
            )
            continue
        lines, _ = page_all(
            client,
            f"/productFamilies/{fam_var}/productLines",
            page_size=page_size,
        )
        if not lines:
            rows.append(
                {
                    "family_variable_name": fam_var,
                    "family_name": fam["name"],
                    "line_variable_name": "",
                    "line_name": "",
                    "model_variable_name": "",
                    "model_name": "",
                    "family_description": fam["description"],
                    "line_description": "",
                    "model_description": "",
                }
            )
            continue
        for line in lines:
            line_count += 1
            ln = normalize_line(line)
            line_var = ln["variable_name"]
            if not line_var:
                rows.append(
                    {
                        "family_variable_name": fam_var,
                        "family_name": fam["name"],
                        "line_variable_name": "",
                        "line_name": ln["name"],
                        "model_variable_name": "",
                        "model_name": "",
                        "family_description": fam["description"],
                        "line_description": ln["description"],
                        "model_description": "",
                    }
                )
                continue
            models, _ = page_all(
                client,
                f"/productFamilies/{fam_var}/productLines/{line_var}/models",
                page_size=page_size,
            )
            if not models:
                rows.append(
                    {
                        "family_variable_name": fam_var,
                        "family_name": fam["name"],
                        "line_variable_name": line_var,
                        "line_name": ln["name"],
                        "model_variable_name": "",
                        "model_name": "",
                        "family_description": fam["description"],
                        "line_description": ln["description"],
                        "model_description": "",
                    }
                )
                continue
            for model in models:
                model_count += 1
                md = normalize_model(model)
                rows.append(
                    {
                        "family_variable_name": fam_var,
                        "family_name": fam["name"],
                        "line_variable_name": line_var,
                        "line_name": ln["name"],
                        "model_variable_name": md["variable_name"],
                        "model_name": md["name"],
                        "family_description": fam["description"],
                        "line_description": ln["description"],
                        "model_description": md["description"],
                    }
                )

    if fam_truncated:
        message = (
            f"Stopped after {max_families} product families (max_families cap). "
            "Raise awareness: results are truncated."
        )

    return {
        "columns": list(PRODUCT_HIERARCHY_COLUMNS),
        "rows": rows,
        "counts": {
            "families": len(families),
            "lines": line_count,
            "models": model_count,
            "rows": len(rows),
        },
        "truncated": fam_truncated,
        "message": message,
    }


def build_commerce_processes_table(
    client: CPQClient,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> dict[str, Any]:
    """Page commerce process setups into a flat variable-name table."""
    processes, _ = page_all(
        client,
        "/commerceProcessSetups",
        page_size=page_size,
    )
    rows = [normalize_commerce_process(item) for item in processes]
    return {
        "columns": list(COMMERCE_PROCESS_COLUMNS),
        "rows": rows,
        "counts": {"processes": len(rows), "rows": len(rows)},
        "truncated": False,
        "message": "",
    }
