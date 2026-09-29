"""Unit tests for utilities.fusion_oauth_token (no live network)."""

from __future__ import annotations

import base64
import importlib.util
from pathlib import Path

import httpx
import pytest
import respx

_UTIL = (
    Path(__file__).resolve().parents[1] / "utilities" / "fusion_oauth_token.py"
)


def _load_module():
    import sys

    spec = importlib.util.spec_from_file_location("fusion_oauth_token", _UTIL)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Required so @dataclass(slots=True) can resolve the module namespace.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


mod = _load_module()
FusionOAuthError = mod.FusionOAuthError
get_fusion_access_token = mod.get_fusion_access_token
validate_oauth_inputs = mod.validate_oauth_inputs
main = mod.main

TOKEN_URL = "https://idcs-example.identity.oraclecloud.com/oauth2/v1/token"
SCOPE = "urn:opc:resource:fusion:demo:cpq/"


def test_validate_rejects_empty_and_http() -> None:
    with pytest.raises(FusionOAuthError, match="token_url is required"):
        validate_oauth_inputs("", "id", "secret", SCOPE)
    with pytest.raises(FusionOAuthError, match="https"):
        validate_oauth_inputs(
            "http://idcs.example.com/oauth2/v1/token", "id", "secret", SCOPE
        )
    with pytest.raises(FusionOAuthError, match="oauth2/v1/token"):
        validate_oauth_inputs(
            "https://idcs.example.com/oauth2/v1/authorize", "id", "secret", SCOPE
        )
    with pytest.raises(FusionOAuthError, match="placeholder"):
        validate_oauth_inputs(TOKEN_URL, "changeme", "secret", SCOPE)


@respx.mock
def test_get_token_success_and_basic_auth() -> None:
    route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "tok-abc",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": SCOPE,
            },
        )
    )
    result = get_fusion_access_token(
        TOKEN_URL, "my-client", "my-secret", SCOPE, timeout_seconds=5
    )
    assert result.access_token == "tok-abc"
    assert result.token_type == "Bearer"
    assert result.expires_in == 3600
    assert route.called
    request = route.calls.last.request
    expected = "Basic " + base64.b64encode(b"my-client:my-secret").decode("ascii")
    assert request.headers["Authorization"] == expected
    assert "application/x-www-form-urlencoded" in request.headers["Content-Type"]
    body = request.content.decode("utf-8")
    assert "grant_type=client_credentials" in body
    assert "scope=" in body


@respx.mock
def test_get_token_http_401() -> None:
    respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(401, text='{"error":"invalid_client"}')
    )
    with pytest.raises(FusionOAuthError, match="HTTP 401"):
        get_fusion_access_token(TOKEN_URL, "id", "bad-secret", SCOPE)


@respx.mock
def test_get_token_missing_access_token() -> None:
    respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"token_type": "Bearer"})
    )
    with pytest.raises(FusionOAuthError, match="access_token"):
        get_fusion_access_token(TOKEN_URL, "id", "secret", SCOPE)


def test_main_prints_token(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        mod,
        "get_fusion_access_token",
        lambda **_kwargs: mod.FusionOAuthToken(
            access_token="cli-token", token_type="Bearer", expires_in=60
        ),
    )
    code = main(
        [
            "--token-url",
            TOKEN_URL,
            "--client-id",
            "id",
            "--client-secret",
            "secret",
            "--scope",
            SCOPE,
        ]
    )
    assert code == 0
    assert capsys.readouterr().out.strip() == "cli-token"


def test_main_json_and_env(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(mod.ENV_TOKEN_URL, TOKEN_URL)
    monkeypatch.setenv(mod.ENV_CLIENT_ID, "id")
    monkeypatch.setenv(mod.ENV_CLIENT_SECRET, "secret")
    monkeypatch.setenv(mod.ENV_SCOPE, SCOPE)
    monkeypatch.setattr(
        mod,
        "get_fusion_access_token",
        lambda **_kwargs: mod.FusionOAuthToken(
            access_token="env-token", token_type="Bearer", expires_in=120
        ),
    )
    code = main(["--json"])
    assert code == 0
    out = capsys.readouterr().out
    assert "env-token" in out
    assert "expires_in" in out


def test_main_validation_failure_stderr(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        [
            "--token-url",
            "https://example.com/wrong",
            "--client-id",
            "id",
            "--client-secret",
            "secret",
            "--scope",
            SCOPE,
        ]
    )
    assert code == 1
    err = capsys.readouterr().err
    assert "oauth2/v1/token" in err
