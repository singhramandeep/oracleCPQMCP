"""Oracle Fusion / IDCS OAuth client-credentials helper (security module).

Used by CPQClient (fusion mode) and the get_fusion_access_token MCP tool.
Never log or echo client secrets.
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

_TOKEN_PATH = "/oauth2/v1/token"
_PLACEHOLDERS = frozenset(
    {
        "changeme",
        "your_client_id",
        "your_client_secret",
        "client_id",
        "client_secret",
        "<client_id>",
        "<client_secret>",
        "your_client_id".upper(),
        "YOUR_CLIENT_ID",
        "YOUR_CLIENT_SECRET",
        "YOUR_TEST_CLIENT_ID",
        "YOUR_TEST_CLIENT_SECRET",
        "YOUR_PROD_CLIENT_ID",
        "YOUR_PROD_CLIENT_SECRET",
    }
)

ENV_TOKEN_URL = "FUSION_OAUTH_TOKEN_URL"
ENV_CLIENT_ID = "FUSION_OAUTH_CLIENT_ID"
ENV_CLIENT_SECRET = "FUSION_OAUTH_CLIENT_SECRET"
ENV_SCOPE = "FUSION_OAUTH_SCOPE"


class FusionOAuthError(Exception):
    """Raised when OAuth input validation or the token request fails."""


@dataclass(frozen=True, slots=True)
class FusionOAuthToken:
    """Parsed token response."""

    access_token: str
    token_type: str | None = None
    expires_in: int | None = None
    scope: str | None = None


def mask_access_token(token: str) -> str:
    """Mask a Bearer access token for agent-facing responses."""
    if len(token) <= 8:
        return "…"
    return f"{token[:4]}…{token[-4:]}"


def _require_nonempty(name: str, value: str | None) -> str:
    text = (value or "").strip()
    if not text:
        raise FusionOAuthError(f"{name} is required and must be non-empty")
    if text.lower() in {p.lower() for p in _PLACEHOLDERS}:
        raise FusionOAuthError(f"{name} looks like a placeholder; provide a real value")
    return text


def validate_oauth_inputs(
    token_url: str,
    client_id: str,
    client_secret: str,
    scope: str,
) -> tuple[str, str, str, str]:
    """Validate and normalize OAuth inputs. Returns stripped values."""
    url = _require_nonempty("token_url", token_url)
    cid = _require_nonempty("client_id", client_id)
    secret = _require_nonempty("client_secret", client_secret)
    sc = _require_nonempty("scope", scope)

    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise FusionOAuthError("token_url must use https://")
    if not parsed.netloc:
        raise FusionOAuthError("token_url is missing a host")
    path = (parsed.path or "").rstrip("/")
    if not path.endswith(_TOKEN_PATH):
        raise FusionOAuthError(
            f"token_url must end with {_TOKEN_PATH} (got path {parsed.path!r})"
        )
    return url, cid, secret, sc


def _basic_auth_header(client_id: str, client_secret: str) -> str:
    raw = f"{client_id}:{client_secret}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _sanitize_error_body(text: str, *, limit: int = 300) -> str:
    cleaned = (text or "").replace("\n", " ").strip()
    if len(cleaned) > limit:
        return cleaned[:limit] + "…"
    return cleaned


def _parse_token_response(payload: dict[str, Any]) -> FusionOAuthToken:
    token = payload.get("access_token")
    if not isinstance(token, str) or not token.strip():
        raise FusionOAuthError("OAuth response missing non-empty access_token")
    expires_raw = payload.get("expires_in")
    expires_in: int | None
    try:
        expires_in = int(expires_raw) if expires_raw is not None else None
    except (TypeError, ValueError):
        expires_in = None
    token_type = payload.get("token_type")
    scope = payload.get("scope")
    return FusionOAuthToken(
        access_token=token.strip(),
        token_type=str(token_type) if token_type else None,
        expires_in=expires_in,
        scope=str(scope) if scope else None,
    )


def get_fusion_access_token(
    token_url: str,
    client_id: str,
    client_secret: str,
    scope: str,
    *,
    timeout_seconds: float = 30.0,
    client: httpx.Client | None = None,
) -> FusionOAuthToken:
    """POST client_credentials grant; return access token (+ metadata)."""
    url, cid, secret, sc = validate_oauth_inputs(
        token_url, client_id, client_secret, scope
    )
    if timeout_seconds <= 0:
        raise FusionOAuthError("timeout_seconds must be positive")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": _basic_auth_header(cid, secret),
    }
    data = {"grant_type": "client_credentials", "scope": sc}
    owns_client = client is None
    http = client or httpx.Client(timeout=timeout_seconds)
    try:
        response = http.post(url, headers=headers, data=data)
    except httpx.HTTPError as exc:
        logger.error("Fusion OAuth request failed: %s", type(exc).__name__)
        raise FusionOAuthError(f"OAuth request failed: {type(exc).__name__}") from exc
    finally:
        if owns_client:
            http.close()

    if response.status_code < 200 or response.status_code >= 300:
        detail = _sanitize_error_body(response.text)
        raise FusionOAuthError(
            f"OAuth token endpoint returned HTTP {response.status_code}: {detail}"
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise FusionOAuthError("OAuth response is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise FusionOAuthError("OAuth response JSON must be an object")
    return _parse_token_response(payload)
