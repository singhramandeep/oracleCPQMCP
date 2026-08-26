"""Unit tests for site admin MCP tools (certificates, SSO)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.security.context import reset_session_tool_calls
from oracle_cpq_mcp.security.rate_limit import reset_rate_limits
from oracle_cpq_mcp.security.replay import reset_replay_store
from oracle_cpq_mcp.security.sanitization import redact_sensitive_data
from oracle_cpq_mcp.security.settings import SecuritySettings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.admin import register_admin_tools


class _FakeMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):  # noqa: ANN201
        def decorator(fn):  # noqa: ANN001, ANN202
            self.tools[fn.__name__] = fn
            return fn

        return decorator


def _profile() -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v19",
        read_only=True,
    )


def _configure(profile: CPQProfile) -> None:
    reset_session_tool_calls()
    reset_rate_limits()
    reset_replay_store()
    configure_security(
        profile,
        SecuritySettings(
            confirmation_secret="test-secret-key-for-hmac",
            confirmation_ttl_seconds=300,
            schema_integrity_enabled=False,
            max_tool_calls_per_session=100,
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


def test_redact_certificate_pem_fields() -> None:
    payload = {
        "name": "testCertificate",
        "certificate": "-----BEGIN CERTIFICATE-----\nMIID\n-----END CERTIFICATE-----",
        "idProviderCertificate": "base64encodecertvalue",
        "samlRequestKeyStore": "base64encodedcertvalue",
        "ssoMethod": "Federated Authentication",
    }
    redacted = redact_sensitive_data(payload)
    assert redacted["name"] == "testCertificate"
    assert redacted["ssoMethod"] == "Federated Authentication"
    assert redacted["certificate"] == "[REDACTED]"
    assert redacted["idProviderCertificate"] == "[REDACTED]"
    assert redacted["samlRequestKeyStore"] == "[REDACTED]"


def test_list_certificates_calls_api() -> None:
    profile = _profile()
    _configure(profile)
    client = MagicMock()
    client.profile = profile
    client.get.return_value = {
        "items": [{"name": "testCertificate", "certificate": "PEMDATA"}]
    }
    mcp = _FakeMcp()
    register_admin_tools(mcp, client)  # type: ignore[arg-type]
    result = mcp.tools["list_certificates"]()
    assert result["status"] == "ok"
    client.get.assert_called_with("/certificates")
    # Wrapper sanitizes tool output — PEM must not leak
    items = result["data"].get("items") or []
    if items:
        assert items[0].get("certificate") == "[REDACTED]"


def test_get_certificate_calls_api() -> None:
    profile = _profile()
    _configure(profile)
    client = MagicMock()
    client.profile = profile
    client.get.return_value = {"name": "testCertificate", "certificate": "PEMDATA"}
    mcp = _FakeMcp()
    register_admin_tools(mcp, client)  # type: ignore[arg-type]
    result = mcp.tools["get_certificate"](name="testCertificate")
    assert result["status"] == "ok"
    client.get.assert_called_with("/certificates/testCertificate")
    assert result["data"].get("certificate") == "[REDACTED]"


def test_get_sso_configuration_calls_api() -> None:
    profile = _profile()
    _configure(profile)
    client = MagicMock()
    client.profile = profile
    client.get.return_value = {
        "ssoMethod": "None",
        "idProviderCertificate": "SECRETPEM",
    }
    mcp = _FakeMcp()
    register_admin_tools(mcp, client)  # type: ignore[arg-type]
    result = mcp.tools["get_sso_configuration"]()
    assert result["status"] == "ok"
    client.get.assert_called_with("/ssoConfiguration")
    assert result["data"].get("idProviderCertificate") == "[REDACTED]"
