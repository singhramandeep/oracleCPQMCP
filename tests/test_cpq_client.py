"""Unit tests for CPQClient."""

from __future__ import annotations

import httpx
import pytest
import respx

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.core.cpq_client import CPQClient, format_curl_command
from oracle_cpq_mcp.core.errors import CPQAPIError, sanitize_message


@pytest.fixture()
def profile() -> CPQProfile:
    return CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="s3cr3t!")],
        rest_version="v18",
        company_login_name="_host",
        read_only=False,
        debug_mode=False,
    )


@pytest.fixture()
def client(profile: CPQProfile) -> CPQClient:
    return CPQClient(profile)


@respx.mock
def test_get_success(client: CPQClient) -> None:
    route = respx.get("https://dev.example.com/rest/v18/users").mock(
        return_value=httpx.Response(200, json={"items": [], "count": 0})
    )
    result = client.get("/users")
    assert result == {"items": [], "count": 0}
    assert route.called


@respx.mock
def test_get_api_error_sanitizes_password(client: CPQClient, profile: CPQProfile) -> None:
    respx.get("https://dev.example.com/rest/v18/users").mock(
        return_value=httpx.Response(401, text=f"Unauthorized password={profile.password}")
    )
    with pytest.raises(CPQAPIError) as exc_info:
        client.get("/users")
    assert profile.password not in str(exc_info.value)
    assert exc_info.value.status_code == 401
    assert exc_info.value.url == "https://dev.example.com/rest/v18/users"
    assert profile.password not in (exc_info.value.curl_command or "")
    assert "***" in (exc_info.value.curl_command or "")
    payload = exc_info.value.to_dict()
    assert payload["status"] == "error"
    assert payload["code"] == "UNAUTHORIZED"
    assert "details" in payload
    assert "curl" not in payload["details"]
    assert "response" not in payload["details"]
    assert "url" in payload["details"]
    assert "path" in payload["details"]


@respx.mock
def test_get_api_error_includes_curl_with_query_params(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v18/users").mock(
        return_value=httpx.Response(
            401,
            json={"error": "Incorrect user or password"},
        )
    )
    with pytest.raises(CPQAPIError) as exc_info:
        client.get("/users", params={"limit": 5, "offset": 0})
    curl = exc_info.value.curl_command or ""
    assert "limit=5" in curl
    assert "offset=0" in curl
    # Raw CPQ body stays on the exception for server logs, not in LLM tool details.
    assert exc_info.value.body == {"error": "Incorrect user or password"}
    assert "response" not in exc_info.value.to_dict()["details"]


@respx.mock
def test_request_error_includes_curl_without_response(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v18/users").mock(
        side_effect=httpx.ConnectError("connection refused")
    )
    with pytest.raises(CPQAPIError) as exc_info:
        client.get("/users")
    payload = exc_info.value.to_dict()
    assert payload["status"] == "error"
    assert payload["code"] == "NETWORK_ERROR"
    assert "details" in payload
    assert "curl" not in payload["details"]
    assert "url" in payload["details"]
    assert "response" not in payload["details"]
    assert "***" in (exc_info.value.curl_command or "")


def test_format_curl_command_redacts_password() -> None:
    curl = format_curl_command(
        "POST",
        "https://dev.example.com/rest/v18/users",
        username="integration_user",
        json_body={"login": "alice"},
    )
    assert "integration_user:***" in curl
    assert "POST" in curl
    assert "'login': 'alice'" in curl or '"login": "alice"' in curl


def test_sanitize_message_redacts_basic_auth() -> None:
    raw = "Authorization: Basic dXNlcjpwYXNz"
    assert "[REDACTED]" in sanitize_message(raw)


@respx.mock
def test_post_with_json(client: CPQClient) -> None:
    route = respx.post("https://dev.example.com/rest/v18/datatables/actions/deploy").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    result = client.post(
        "/datatables/actions/deploy",
        json_body={"selections": ["Status"]},
    )
    assert result == {"status": "ok"}
    assert route.called
    request = route.calls.last.request
    assert request.content is not None


@respx.mock
def test_mutating_request_blocked_when_read_only(profile: CPQProfile) -> None:
    read_only_profile = CPQProfile(
        customer_name=profile.customer_name,
        customer_id=profile.customer_id,
        environment=profile.environment,
        base_url=profile.base_url,
        credentials=profile.credentials,
        rest_version=profile.rest_version,
        company_login_name=profile.company_login_name,
        read_only=True,
        debug_mode=False,
    )
    client = CPQClient(read_only_profile)
    patch_route = respx.patch("https://dev.example.com/rest/v18/users/12345").mock(
        return_value=httpx.Response(200, json={"partyNumber": "12345"})
    )

    with pytest.raises(CPQAPIError, match="READ_ONLY mode"):
        client.patch("/users/12345", json_body={"email": "new@b.com"})

    assert not patch_route.called


@respx.mock
def test_parts_search_allowed_when_read_only(profile: CPQProfile) -> None:
    read_only_profile = CPQProfile(
        customer_name=profile.customer_name,
        customer_id=profile.customer_id,
        environment=profile.environment,
        base_url=profile.base_url,
        credentials=profile.credentials,
        rest_version=profile.rest_version,
        company_login_name=profile.company_login_name,
        read_only=True,
        debug_mode=False,
    )
    client = CPQClient(read_only_profile)
    route = respx.post("https://dev.example.com/rest/v18/parts/actions/search").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    result = client.post("/parts/actions/search", json_body={"criteria": {}})
    assert result == {"items": []}
    assert route.called


@respx.mock
def test_get_not_found_returns_structured_error(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v18/users/99999").mock(
        return_value=httpx.Response(404, json={"title": "Not found"})
    )
    with pytest.raises(CPQAPIError) as exc_info:
        client.get("/users/99999")
    payload = exc_info.value.to_tool_error()
    assert payload["status"] == "error"
    assert payload["code"] == "NOT_FOUND"
    assert "hint" in payload
    assert payload["details"]["status_code"] == 404


@respx.mock
def test_get_bytes_success(client: CPQClient) -> None:
    route = respx.get("https://dev.example.com/rest/v18/adminMeta").mock(
        return_value=httpx.Response(200, content=b"PK\x03\x04fake-zip")
    )
    result = client.get_bytes("/adminMeta")
    assert result == b"PK\x03\x04fake-zip"
    assert route.called
    request = route.calls.last.request
    assert request.headers.get("accept") == "application/zip"


@respx.mock
def test_get_bytes_api_error(client: CPQClient) -> None:
    respx.get("https://dev.example.com/rest/v18/adminMeta").mock(
        return_value=httpx.Response(403, json={"title": "Forbidden"})
    )
    with pytest.raises(CPQAPIError) as exc_info:
        client.get_bytes("/adminMeta")
    assert exc_info.value.status_code == 403


@respx.mock
def test_debug_mode_writes_redacted_log_with_query_params(
    profile: CPQProfile, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CPQ_DEBUG_LOG_DIR", str(tmp_path))
    debug_profile = profile.model_copy(update={"debug_mode": True})
    client = CPQClient(debug_profile)
    respx.get("https://dev.example.com/rest/v18/metrics").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    client.get("/metrics", params={"name": "QUOTES", "limit": 100})

    log_path = tmp_path / "test-dev.log"
    assert log_path.is_file()
    text = log_path.read_text(encoding="utf-8")
    assert "CURL:" in text
    assert "Parameters:" in text
    assert "query.name = QUOTES" in text
    assert "query.limit = 100" in text
    assert "body = (none)" in text
    assert "user:***" in text
    assert profile.password not in text
    assert "GET" in text
    assert "Status: 200" in text


@respx.mock
def test_debug_mode_disabled_writes_no_log(
    profile: CPQProfile, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CPQ_DEBUG_LOG_DIR", str(tmp_path))
    client = CPQClient(profile)
    respx.get("https://dev.example.com/rest/v18/users").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    client.get("/users")
    assert not (tmp_path / "test-dev.log").exists()


@respx.mock
def test_debug_mode_logs_post_body_keys(
    profile: CPQProfile, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CPQ_DEBUG_LOG_DIR", str(tmp_path))
    debug_profile = profile.model_copy(update={"debug_mode": True})
    client = CPQClient(debug_profile)
    respx.post("https://dev.example.com/rest/v18/datatables/actions/deploy").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client.post(
        "/datatables/actions/deploy",
        json_body={"selections": ["Status"], "nested": {"a": 1}},
    )
    text = (tmp_path / "test-dev.log").read_text(encoding="utf-8")
    assert "body.selections =" in text
    assert "body.nested =" in text
    assert profile.password not in text
