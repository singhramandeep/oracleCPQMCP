"""Tests for Commerce metadata path helpers."""

from __future__ import annotations

from oracle_cpq_mcp.core.commerce_paths import (
    commerce_document_path,
    commerce_query_params,
    resolve_process_var_name,
)
from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet


def _profile(*, commerce_names: list[str] | None = None) -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v19",
        commerce_process_var_names=commerce_names or [],
    )


def test_commerce_document_path() -> None:
    path = commerce_document_path("oraclecpqo", "transaction", "attributes")
    assert path == "/commerceProcesses/oraclecpqo/documents/transaction/attributes"


def test_commerce_query_params_expand_all() -> None:
    assert commerce_query_params(expand_all=True) == {"expand": "all*"}
    assert commerce_query_params(expand_all=False) is None


def test_resolve_process_var_name_from_profile() -> None:
    profile = _profile(commerce_names=["oraclecpqo_bmClone_2"])
    assert resolve_process_var_name(profile, None) == "oraclecpqo_bmClone_2"


def test_resolve_process_var_name_from_argument() -> None:
    profile = _profile(commerce_names=["oraclecpqo_bmClone_2"])
    assert resolve_process_var_name(profile, "custom_process") == "custom_process"


def test_resolve_process_var_name_missing_returns_error() -> None:
    profile = _profile()
    result = resolve_process_var_name(profile, None)
    assert isinstance(result, dict)
    assert result["status"] == "error"
    assert result["code"] == "VALIDATION_ERROR"
