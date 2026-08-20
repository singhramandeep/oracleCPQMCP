"""Tests for Commerce transaction tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.transactions import _collection_extra, register_transaction_tools


@pytest.fixture()
def profile() -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v18",
        company_login_name="_host",
        read_only=False,
        commerce_process_var_names=["oraclecpqo"],
    )


@pytest.fixture()
def configured(profile: CPQProfile) -> CPQProfile:
    configure_security(
        profile,
        SecuritySettings(
            confirmation_secret="test-secret-key-for-hmac",
            confirmation_ttl_seconds=300,
            schema_integrity_enabled=False,
            max_tool_calls_per_session=50,
            rate_limit_enabled=False,
            audit_enabled=False,
            allow_prod=False,
            max_response_bytes=2_000_000,
            replay_window_seconds=60,
            read_calls_per_minute=120,
            write_calls_per_minute=10,
            privileged_calls_per_minute=5,
        ),
    )
    return profile


class FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):
        def decorator(fn: Any) -> Any:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def test_collection_extra_maps_oracle_params() -> None:
    extra = _collection_extra(
        q_expr="{id:{$gt:1}}",
        fields=["id", "_customer_id"],
        orderby=["id:desc"],
        expand="transactionLine",
        exclude_field_types="html",
    )
    assert extra == {
        "q": "{id:{$gt:1}}",
        "fields": "id,_customer_id",
        "orderby": "id:desc",
        "expand": "transactionLine",
        "excludeFieldTypes": "html",
    }


def test_list_transactions_calls_documents_path(configured: CPQProfile) -> None:
    client = MagicMock()
    client.profile = configured
    client.get.return_value = {"items": [{"id": 1}], "hasMore": False, "offset": 0, "limit": 2}
    mcp = FakeMcp()
    register_transaction_tools(mcp, client)
    result = mcp.tools["list_transactions"](limit=2, offset=0)
    assert result["status"] == "ok"
    path, kwargs = client.get.call_args
    assert path[0] == "/commerceDocumentsOraclecpqoTransaction"
    assert kwargs["params"]["limit"] == 2


def test_generate_proposal_dry_run_does_not_post(configured: CPQProfile) -> None:
    client = MagicMock()
    client.profile = configured
    client.get.return_value = {"id": 42}
    mcp = FakeMcp()
    register_transaction_tools(mcp, client)
    result = mcp.tools["generate_proposal"](transaction_id="42", dry_run=True)
    assert result["status"] == "preflight_ok"
    client.post.assert_not_called()
    client.get.assert_called()


def test_export_attachment_dry_run_does_not_post(configured: CPQProfile) -> None:
    client = MagicMock()
    client.profile = configured
    client.get.return_value = {"id": 42}
    mcp = FakeMcp()
    register_transaction_tools(mcp, client)
    result = mcp.tools["export_attachment"](
        transaction_id="42",
        attribute_var_name="proposalAttachment_t",
        dry_run=True,
    )
    assert result["status"] == "preflight_ok"
    data = result.get("data") or result
    assert (
        data["would_execute"]["path"]
        == "/commerceDocumentsOraclecpqoTransaction/42/actions/exportAttachment"
    )
    assert data["would_execute"]["body"]["selections"] == ["proposalAttachment_t"]
    client.post.assert_not_called()
    client.get.assert_called()


def test_export_attachment_uses_action_and_merges_selections(
    configured: CPQProfile,
) -> None:
    client = MagicMock()
    client.profile = configured
    client.get.return_value = {"id": 42}
    mcp = FakeMcp()
    register_transaction_tools(mcp, client)
    result = mcp.tools["export_attachment"](
        transaction_id="42",
        attribute_var_name="proposalAttachment_t",
        action_var_name="expAttachment",
        body={"selections": ["other_t"], "delta": True},
        dry_run=True,
    )
    data = result.get("data") or result
    assert (
        data["would_execute"]["path"]
        == "/commerceDocumentsOraclecpqoTransaction/42/actions/expAttachment"
    )
    assert data["would_execute"]["body"]["selections"] == [
        "proposalAttachment_t",
        "other_t",
    ]
    assert data["would_execute"]["body"]["delta"] is True


def test_get_document_layout_path(configured: CPQProfile) -> None:
    client = MagicMock()
    client.profile = configured
    client.get.return_value = {"layout": True}
    mcp = FakeMcp()
    register_transaction_tools(mcp, client)
    result = mcp.tools["get_document_layout"]()
    assert result["status"] == "ok"
    client.get.assert_called_once_with("/commerceProcesses/oraclecpqo/layouts/transaction")
