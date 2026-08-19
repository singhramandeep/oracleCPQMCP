"""Oracle CPQ collection pagination helpers (limit, offset, hasMore, totalResults)."""

from __future__ import annotations

import logging
from typing import Any

from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.errors import CPQAPIError

logger = logging.getLogger(__name__)

CPQ_MAX_LIMIT = 1000
CPQ_MIN_LIMIT = 1


def clamp_limit(limit: int) -> int:
    """Clamp page size to Oracle CPQ bounds (1..1000)."""
    return max(CPQ_MIN_LIMIT, min(limit, CPQ_MAX_LIMIT))


def build_page_params(
    limit: int,
    offset: int,
    *,
    total_results: bool = True,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build CPQ pagination query params for a single page request."""
    params: dict[str, Any] = {
        "limit": clamp_limit(limit),
        "offset": max(0, offset),
    }
    if total_results:
        params["totalResults"] = "true"
    if extra:
        params.update(extra)
    return params


def next_offset(response: dict[str, Any]) -> int | None:
    """Return the offset for the next page, or None when hasMore is false."""
    if not response.get("hasMore", False):
        return None

    current_offset = response.get("offset", 0)
    page_limit = response.get("limit")
    if page_limit is not None:
        return int(current_offset) + int(page_limit)

    page_count = response.get("count")
    if page_count is not None:
        return int(current_offset) + int(page_count)

    return None


def enrich_pagination_hint(response: dict[str, Any], tool_name: str) -> dict[str, Any]:
    """Add a pagination hint to a CPQ collection response without changing items."""
    enriched = dict(response)
    next_page_offset = next_offset(response)
    if next_page_offset is None:
        return enriched

    page_limit = response.get("limit")
    hint: dict[str, Any] = {"nextOffset": next_page_offset}
    if page_limit is not None:
        hint["suggestedNextCall"] = f"{tool_name}(offset={next_page_offset}, limit={page_limit})"
    else:
        hint["suggestedNextCall"] = f"{tool_name}(offset={next_page_offset})"

    enriched["pagination"] = hint
    return enriched


def iterate_collection(
    client: CPQClient,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    page_size: int = 100,
    max_items: int = 10_000,
) -> list[Any]:
    """Fetch all items from a paginated CPQ collection until hasMore is false."""
    items: list[Any] = []
    offset = 0
    base_params = dict(params or {})

    while True:
        page_params = build_page_params(
            page_size,
            offset,
            total_results=True,
            extra=base_params,
        )
        response = client.get(path, params=page_params)
        if not isinstance(response, dict):
            raise CPQAPIError(
                f"Unexpected CPQ response for {path}: expected object",
                code="INVALID_RESPONSE",
                hint="CPQ returned a non-object payload; verify REST API version and endpoint.",
                path=path,
            )

        batch = response.get("items", [])
        if not isinstance(batch, list):
            raise CPQAPIError(
                f"Unexpected CPQ response for {path}: missing items list",
                code="INVALID_RESPONSE",
                hint="CPQ collection response is missing an items array.",
                path=path,
            )

        items.extend(batch)
        if len(items) >= max_items:
            logger.warning(
                "Collection fetch truncated at %s items (max_items=%s) for %s",
                len(items),
                max_items,
                path,
            )
            return items[:max_items]

        if not response.get("hasMore", False):
            return items

        advanced = next_offset(response)
        if advanced is None:
            return items
        offset = advanced
