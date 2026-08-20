"""Tests for Oracle CPQ pagination helpers."""

from __future__ import annotations

import httpx
import pytest
import respx

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.pagination import (
    build_page_params,
    clamp_limit,
    enrich_pagination_hint,
    iterate_collection,
    next_offset,
)


@pytest.fixture()
def profile() -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="mycompany",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="pass")],
        rest_version="v18",
    )


@pytest.fixture()
def client(profile: CPQProfile) -> CPQClient:
    return CPQClient(profile)


def test_clamp_limit_bounds() -> None:
    assert clamp_limit(0) == 1
    assert clamp_limit(1500) == 1000
    assert clamp_limit(100) == 100


def test_build_page_params_includes_total_results() -> None:
    params = build_page_params(100, 0, extra={"q": "login eq 'alice'"})
    assert params == {
        "limit": 100,
        "offset": 0,
        "totalResults": "true",
        "q": "login eq 'alice'",
    }


def test_build_page_params_clamps_limit_and_offset() -> None:
    params = build_page_params(5000, -5)
    assert params["limit"] == 1000
    assert params["offset"] == 0
    assert params["totalResults"] == "true"


def test_build_page_params_can_disable_total_results() -> None:
    params = build_page_params(50, 10, total_results=False)
    assert "totalResults" not in params
    assert params["limit"] == 50
    assert params["offset"] == 10


def test_next_offset_when_has_more() -> None:
    response = {"hasMore": True, "offset": 0, "count": 25, "limit": 25}
    assert next_offset(response) == 25


def test_next_offset_prefers_limit_over_count() -> None:
    response = {"hasMore": True, "offset": 0, "count": 1, "limit": 100}
    assert next_offset(response) == 100


def test_next_offset_uses_count_when_limit_missing() -> None:
    response = {"hasMore": True, "offset": 100, "count": 50}
    assert next_offset(response) == 150


def test_next_offset_none_when_no_more() -> None:
    response = {"hasMore": False, "offset": 100, "count": 5, "limit": 100}
    assert next_offset(response) is None


def test_enrich_pagination_hint_adds_next_page() -> None:
    response = {
        "items": [{"id": 1}],
        "hasMore": True,
        "offset": 0,
        "count": 100,
        "limit": 100,
        "totalResults": 250,
    }
    enriched = enrich_pagination_hint(response, "list_users")
    assert enriched["items"] == [{"id": 1}]
    assert enriched["pagination"] == {
        "nextOffset": 100,
        "suggestedNextCall": "list_users(offset=100, limit=100)",
    }


def test_enrich_pagination_hint_omits_when_complete() -> None:
    response = {"items": [], "hasMore": False, "offset": 0, "count": 0, "limit": 100}
    enriched = enrich_pagination_hint(response, "list_users")
    assert "pagination" not in enriched


@respx.mock
def test_iterate_collection_paginates(client: CPQClient) -> None:
    route = respx.get("https://dev.example.com/rest/v18/users").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "items": [{"login": "alice"}],
                    "hasMore": True,
                    "offset": 0,
                    "count": 1,
                    "limit": 100,
                },
            ),
            httpx.Response(
                200,
                json={
                    "items": [{"login": "bob"}],
                    "hasMore": False,
                    "offset": 100,
                    "count": 1,
                    "limit": 100,
                },
            ),
        ]
    )

    items = iterate_collection(client, "/users", page_size=100)
    assert len(items.items) == 2
    assert items.items[0]["login"] == "alice"
    assert items.items[1]["login"] == "bob"
    assert items.truncated is False
    assert items.has_more is False
    assert route.call_count == 2
    assert route.calls[0].request.url.params["totalResults"] == "true"
    assert route.calls[1].request.url.params["offset"] == "100"


@respx.mock
def test_iterate_collection_respects_max_items(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v18/users").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"login": f"user{i}"} for i in range(5)],
                "hasMore": True,
                "offset": 0,
                "count": 5,
                "limit": 5,
            },
        )
    )

    result = iterate_collection(client, "/users", page_size=5, max_items=3)
    assert len(result.items) == 3
    assert result.truncated is True
    assert result.has_more is True
    assert result.max_items == 3
