"""HTTP helper for Oracle Fusion CX REST (Sales, Service, etc.).

Not registered as MCP tools. Uses profile ``cx`` connection (Basic or Bearer).
"""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from oracle_cpq_mcp.core.config import CPQProfile
from oracle_cpq_mcp.core.errors import CPQAPIError, classify_http_error, sanitize_message

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 60.0
_TOKEN_SKEW_SECONDS = 60.0


class CXAPIError(CPQAPIError):
    """Raised when Fusion CX REST returns an error."""


class CXClient:
    """Routes Fusion CX REST calls using the profile ``cx`` block."""

    def __init__(self, profile: CPQProfile, *, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.profile = profile
        self.timeout = timeout
        self._cached_token: str | None = None
        self._token_expires_at: float = 0.0

    def _require_cx(self) -> str:
        if not self.profile.cx_enabled or not (self.profile.cx_url or "").strip():
            raise CXAPIError(
                "CX Fusion is not enabled on this profile/environment.",
                code="VALIDATION_ERROR",
                hint="Set environments.<env>.cx.enabled: true with url, auth, and modules.",
            )
        return self.profile.cx_url.rstrip("/")  # type: ignore[union-attr]

    def _sanitize_secret(self) -> str | None:
        if self.profile.cx_auth == "bearer":
            return self.profile.cx_oauth_client_secret
        if self.profile.cx_credentials:
            return self.profile.cx_credentials[0].password
        return None

    def _build_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        base = self._require_cx()
        normalized = path if path.startswith("/") else f"/{path}"
        url = f"{base}{normalized}"
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url = f"{url}?{urlencode(filtered)}"
        return url

    def _ensure_bearer_token(self) -> str:
        now = time.time()
        if self._cached_token and self._token_expires_at > now + _TOKEN_SKEW_SECONDS:
            return self._cached_token
        from oracle_cpq_mcp.security.fusion_oauth import (
            FusionOAuthError,
            get_fusion_access_token,
        )

        if not (
            self.profile.cx_oauth_token_url
            and self.profile.cx_oauth_client_id
            and self.profile.cx_oauth_client_secret
            and self.profile.cx_oauth_scope
        ):
            raise CXAPIError(
                "CX bearer auth is missing oauth_token_url / oauth_client_id / "
                "oauth_client_secret / oauth_scope.",
                code="VALIDATION_ERROR",
                hint="Set oauth_* under environments.<env>.cx.",
                password=self._sanitize_secret(),
            )
        try:
            token = get_fusion_access_token(
                self.profile.cx_oauth_token_url,
                self.profile.cx_oauth_client_id,
                self.profile.cx_oauth_client_secret,
                self.profile.cx_oauth_scope,
                timeout_seconds=min(self.timeout, 60.0),
            )
        except FusionOAuthError as exc:
            raise CXAPIError(
                f"Failed to obtain CX access token: {exc}",
                code="UNAUTHORIZED",
                hint="Verify CX oauth_token_url, client id/secret, and scope.",
                password=self._sanitize_secret(),
            ) from exc
        self._cached_token = token.access_token
        expires = token.expires_in if token.expires_in and token.expires_in > 0 else 3600
        self._token_expires_at = now + float(expires)
        return self._cached_token

    def _auth_and_headers(self) -> tuple[tuple[str, str] | None, dict[str, str]]:
        headers = {"Accept": "application/json"}
        if self.profile.cx_auth == "bearer":
            token = self._ensure_bearer_token()
            headers["Authorization"] = f"Bearer {token}"
            return None, headers
        if not self.profile.cx_credentials:
            raise CXAPIError(
                "CX basic auth requires credentials under environments.<env>.cx.",
                code="VALIDATION_ERROR",
                hint="Add username/password for CX or switch auth to bearer.",
            )
        cred = self.profile.cx_credentials[0]
        return (cred.username, cred.password), headers

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
    ) -> Any:
        url = self._build_url(path, params)
        secret = self._sanitize_secret()
        try:
            auth, headers = self._auth_and_headers()
            with httpx.Client(auth=auth, timeout=self.timeout, headers=headers) as client:
                response = client.request(method.upper(), url, json=json_body)
        except httpx.RequestError as exc:
            message = sanitize_message(str(exc), secret)
            logger.error("CX request failed: %s %s", method.upper(), path)
            raise CXAPIError(
                f"Request to Fusion CX failed: {message}",
                code="NETWORK_ERROR",
                hint="Verify the CX URL, network/VPN, and credentials.",
                method=method.upper(),
                path=path,
                url=url,
                password=secret,
            ) from exc

        if response.status_code < 200 or response.status_code >= 300:
            error_code, error_hint = classify_http_error(
                response.status_code, method=method.upper(), path=path, body=response.text
            )
            body = (response.text or "")[:2000]
            raise CXAPIError(
                sanitize_message(
                    f"CX API error {response.status_code} for {method.upper()} {path}",
                    secret,
                ),
                code=error_code,
                hint=error_hint,
                status_code=response.status_code,
                method=method.upper(),
                path=path,
                url=url,
                body=body,
                password=secret,
            )

        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)
