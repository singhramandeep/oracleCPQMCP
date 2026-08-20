"""HTTP client for Oracle CPQ REST APIs."""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.parse import urlencode

import httpx

from oracle_cpq_mcp.core.config import CPQProfile
from oracle_cpq_mcp.core.errors import CPQAPIError, classify_http_error, sanitize_message

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 60.0
_MUTATING_METHODS = frozenset({"POST", "PATCH", "PUT", "DELETE"})
_SAFE_READ_POST_SUFFIXES = frozenset(
    {
        "/parts/actions/search",
        "/bml/library/functions/actions/dependentAttributes",
    }
)


def _is_safe_read_post(method: str, path: str) -> bool:
    """Allow specific non-mutating POST search endpoints under READ_ONLY."""
    if method.upper() != "POST":
        return False
    normalized = path if path.startswith("/") else f"/{path}"
    return any(normalized.rstrip("/").endswith(suffix) for suffix in _SAFE_READ_POST_SUFFIXES)


def format_curl_command(
    method: str,
    url: str,
    *,
    username: str,
    json_body: Any = None,
) -> str:
    """Build a redacted curl command equivalent to the CPQ REST request."""
    parts = [
        "curl",
        "-X",
        method.upper(),
        "-u",
        f"'{username}:***'",
        "-H",
        "'Content-Type: application/json'",
        "-H",
        "'Accept: application/json'",
    ]
    if json_body is not None:
        serialized = json.dumps(json_body) if not isinstance(json_body, str) else json_body
        parts.extend(["-d", f"'{serialized}'"])
    parts.append(f"'{url}'")
    return " ".join(parts)


class CPQClient:
    """Routes all Oracle CPQ REST calls with Basic Auth and safe errors."""

    def __init__(self, profile: CPQProfile, *, timeout: float = DEFAULT_TIMEOUT) -> None:
        self.profile = profile
        self.timeout = timeout
        self._verbose = os.environ.get("CPQ_VERBOSE", "").lower() in ("1", "true", "yes")

    def _build_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        normalized = path if path.startswith("/") else f"/{path}"
        url = f"{self.profile.rest_base}{normalized}"
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url = f"{url}?{urlencode(filtered)}"
        return url

    def _log_request(self, method: str, url: str, body: Any = None) -> None:
        if not self._verbose:
            return
        logger.info("CPQ %s %s", method.upper(), url)
        curl = self._to_curl(method, url, body)
        logger.info("Equivalent curl: %s", curl)

    def _to_curl(self, method: str, url: str, body: Any = None) -> str:
        return format_curl_command(
            method,
            url,
            username=self.profile.username,
            json_body=body,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
    ) -> Any:
        method_upper = method.upper()
        if (
            self.profile.read_only
            and method_upper in _MUTATING_METHODS
            and not _is_safe_read_post(method_upper, path)
        ):
            url = self._build_url(path, params)
            curl_command = self._to_curl(method, url, json_body)
            message = (
                f"READ_ONLY mode — {method_upper} {path} is blocked. "
                "Set READ_ONLY=false in the profile .env to allow DML."
            )
            logger.error("CPQ request blocked — curl: %s", curl_command)
            raise CPQAPIError(
                message,
                code="READ_ONLY_BLOCKED",
                hint="Set READ_ONLY=false in the profile .env to allow create/update/deploy operations.",
                method=method_upper,
                path=path,
                url=url,
                curl_command=curl_command,
                password=self.profile.password,
            )

        url = self._build_url(path, params)
        curl_command = self._to_curl(method, url, json_body)
        self._log_request(method, url, json_body)

        try:
            with httpx.Client(
                auth=(self.profile.username, self.profile.password),
                timeout=self.timeout,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            ) as client:
                response = client.request(method.upper(), url, json=json_body)
        except httpx.RequestError as exc:
            message = sanitize_message(str(exc), self.profile.password)
            logger.error(
                "CPQ request failed — curl: %s — response: (none)",
                curl_command,
            )
            raise CPQAPIError(
                f"Request to CPQ failed: {message}",
                code="NETWORK_ERROR",
                hint="Verify the CPQ base URL, network/VPN connectivity, and site availability.",
                method=method.upper(),
                path=path,
                url=url,
                curl_command=curl_command,
                password=self.profile.password,
            ) from exc

        if response.status_code >= 400:
            body: Any
            try:
                body = response.json()
            except ValueError:
                body = response.text[:2000]
            error_code, error_hint = classify_http_error(
                response.status_code,
                method=method.upper(),
                path=path,
                body=body,
            )
            message = sanitize_message(
                f"CPQ API error {response.status_code} for {method.upper()} {path}",
                self.profile.password,
            )
            logger.error(
                "CPQ request failed — curl: %s — response: %s",
                curl_command,
                body,
            )
            raise CPQAPIError(
                message,
                code=error_code,
                hint=error_hint,
                status_code=response.status_code,
                method=method.upper(),
                path=path,
                url=url,
                curl_command=curl_command,
                body=body,
                password=self.profile.password,
            )

        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def get_bytes(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        accept: str = "application/zip",
    ) -> bytes:
        """Fetch a binary GET response (e.g. Developer Toolkit BML export zip)."""
        method_upper = "GET"
        url = self._build_url(path, params)
        curl_command = self._to_curl(method_upper, url)
        self._log_request(method_upper, url)

        try:
            with httpx.Client(
                auth=(self.profile.username, self.profile.password),
                timeout=self.timeout,
                headers={
                    "Accept": accept,
                },
            ) as client:
                response = client.get(url)
        except httpx.RequestError as exc:
            message = sanitize_message(str(exc), self.profile.password)
            logger.error(
                "CPQ binary request failed — curl: %s — response: (none)",
                curl_command,
            )
            raise CPQAPIError(
                f"Request to CPQ failed: {message}",
                code="NETWORK_ERROR",
                hint="Verify the CPQ base URL, network/VPN connectivity, and site availability.",
                method=method_upper,
                path=path,
                url=url,
                curl_command=curl_command,
                password=self.profile.password,
            ) from exc

        if response.status_code >= 400:
            body: Any
            try:
                body = response.json()
            except ValueError:
                body = response.text[:2000]
            error_code, error_hint = classify_http_error(
                response.status_code,
                method=method_upper,
                path=path,
                body=body,
            )
            message = sanitize_message(
                f"CPQ API error {response.status_code} for GET {path}",
                self.profile.password,
            )
            logger.error(
                "CPQ binary request failed — curl: %s — response: %s",
                curl_command,
                body,
            )
            raise CPQAPIError(
                message,
                code=error_code,
                hint=error_hint,
                status_code=response.status_code,
                method=method_upper,
                path=path,
                url=url,
                curl_command=curl_command,
                body=body,
                password=self.profile.password,
            )

        return response.content

    def post_bytes(
        self,
        path: str,
        *,
        json_body: Any = None,
        params: dict[str, Any] | None = None,
        accept: str = "*/*",
    ) -> bytes:
        """POST and return raw response bytes (e.g. export downloads)."""
        method_upper = "POST"
        if (
            self.profile.read_only
            and not _is_safe_read_post(method_upper, path)
        ):
            url = self._build_url(path, params)
            curl_command = self._to_curl(method_upper, url, json_body)
            raise CPQAPIError(
                f"READ_ONLY mode — POST {path} is blocked. "
                "Set READ_ONLY=false in the profile .env to allow DML.",
                code="READ_ONLY_BLOCKED",
                hint="Set READ_ONLY=false in the profile .env to allow create/update/deploy operations.",
                method=method_upper,
                path=path,
                url=url,
                curl_command=curl_command,
                password=self.profile.password,
            )

        url = self._build_url(path, params)
        curl_command = self._to_curl(method_upper, url, json_body)
        self._log_request(method_upper, url, json_body)

        try:
            with httpx.Client(
                auth=(self.profile.username, self.profile.password),
                timeout=self.timeout,
                headers={
                    "Accept": accept,
                    "Content-Type": "application/json",
                },
            ) as client:
                response = client.post(url, json=json_body)
        except httpx.RequestError as exc:
            message = sanitize_message(str(exc), self.profile.password)
            logger.error(
                "CPQ binary POST failed — curl: %s — response: (none)",
                curl_command,
            )
            raise CPQAPIError(
                f"Request to CPQ failed: {message}",
                code="NETWORK_ERROR",
                hint="Verify the CPQ base URL, network/VPN connectivity, and site availability.",
                method=method_upper,
                path=path,
                url=url,
                curl_command=curl_command,
                password=self.profile.password,
            ) from exc

        if response.status_code >= 400:
            body: Any
            try:
                body = response.json()
            except ValueError:
                body = response.text[:2000]
            error_code, error_hint = classify_http_error(
                response.status_code,
                method=method_upper,
                path=path,
                body=body,
            )
            message = sanitize_message(
                f"CPQ API error {response.status_code} for POST {path}",
                self.profile.password,
            )
            logger.error(
                "CPQ binary POST failed — curl: %s — response: %s",
                curl_command,
                body,
            )
            raise CPQAPIError(
                message,
                code=error_code,
                hint=error_hint,
                status_code=response.status_code,
                method=method_upper,
                path=path,
                url=url,
                curl_command=curl_command,
                body=body,
                password=self.profile.password,
            )

        return response.content

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, params=params)

    def post(self, path: str, *, json_body: Any = None, params: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, params=params, json_body=json_body)

    def patch(self, path: str, *, json_body: Any) -> Any:
        return self.request("PATCH", path, json_body=json_body)

    def put(self, path: str, *, json_body: Any) -> Any:
        return self.request("PUT", path, json_body=json_body)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)
