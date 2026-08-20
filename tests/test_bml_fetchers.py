"""Tests for BML fetch helpers."""

from __future__ import annotations

import httpx
import pytest
import respx

from oracle_cpq_mcp.core.bml_fetchers import (
    bml_export_filename,
    fetch_all_util_library_code,
    library_function_resource_id,
)
from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.core.cpq_client import CPQClient


@pytest.fixture()
def profile() -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="acme",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v19",
        company_login_name="_host",
        read_only=True,
    )


@pytest.fixture()
def client(profile: CPQProfile) -> CPQClient:
    return CPQClient(profile)


def test_bml_export_filename(profile: CPQProfile) -> None:
    assert bml_export_filename(profile) == "acme_dev_bml_export.zip"


def test_library_function_resource_id_from_self_link() -> None:
    item = {
        "variableName": "concatString",
        "links": [
            {
                "rel": "self",
                "href": "https://dev.example.com/rest/v19/bml/library/functions/nameSpace11.concatString",
            }
        ],
    }
    assert library_function_resource_id(item) == "nameSpace11.concatString"


def test_library_function_resource_id_from_namespace() -> None:
    item = {"variableName": "concatString", "namespace": "nameSpace11"}
    assert library_function_resource_id(item) == "nameSpace11.concatString"


@respx.mock
def test_fetch_all_util_library_code(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v19/bml/library/functions").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "variableName": "concatString",
                        "links": [
                            {
                                "rel": "self",
                                "href": "https://dev.example.com/rest/v19/bml/library/functions/concatString",
                            }
                        ],
                    }
                ],
                "offset": 0,
                "limit": 100,
                "count": 1,
                "hasMore": False,
            },
        )
    )
    respx.get(
        "https://dev.example.com/rest/v19/bml/library/functions/concatString"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "name": "ConcatString",
                "variableName": "concatString",
                "folderName": "util",
                "scriptText": 'return stringOne + " " + stringTwo;',
                "isDeployed": True,
            },
        )
    )

    functions, truncated, has_more = fetch_all_util_library_code(client)
    assert len(functions) == 1
    assert functions[0]["resourceId"] == "concatString"
    assert functions[0]["scriptText"] == 'return stringOne + " " + stringTwo;'
    assert truncated is False
    assert has_more is False
