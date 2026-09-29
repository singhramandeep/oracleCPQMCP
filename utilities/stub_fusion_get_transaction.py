"""Live stub: obtain Fusion/IDCS OAuth token, then GET a commerce transaction.

Replicates the Postman "Get Transaction" flow (Bearer auth against Fusion-hosted
CPQ under /cpq/rest/v19/...). Uses utilities/fusion_oauth_token.py for the token.
Not wired into MCP or CPQClient.

Example (env or flags):

    set FUSION_OAUTH_TOKEN_URL=https://idcs-….identity.oraclecloud.com/oauth2/v1/token
    set FUSION_OAUTH_CLIENT_ID=…
    set FUSION_OAUTH_CLIENT_SECRET=…
    set FUSION_OAUTH_SCOPE=urn:opc:resource:fusion:YOUR_ENV:cpq/

    python utilities/stub_fusion_get_transaction.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

_UTIL_DIR = Path(__file__).resolve().parent
_OAUTH_PATH = _UTIL_DIR / "fusion_oauth_token.py"

DEFAULT_BASE_URL = "https://example-fusion-dev.fa.ocs.oraclecloud.com"
DEFAULT_TRANSACTION_ID = "REPLACE_TRANSACTION_ID"
DEFAULT_REST_PATH = (
    "/cpq/rest/v19/commerceDocumentsOraclecpqoTransaction"
)

ENV_TOKEN_URL = "FUSION_OAUTH_TOKEN_URL"
ENV_CLIENT_ID = "FUSION_OAUTH_CLIENT_ID"
ENV_CLIENT_SECRET = "FUSION_OAUTH_CLIENT_SECRET"
ENV_SCOPE = "FUSION_OAUTH_SCOPE"


def _load_oauth_module():
    spec = importlib.util.spec_from_file_location("fusion_oauth_token", _OAUTH_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {_OAUTH_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _env_or_arg(flag_value: str | None, env_name: str) -> str:
    if flag_value is not None and str(flag_value).strip():
        return str(flag_value).strip()
    return (os.environ.get(env_name) or "").strip()


def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "…"
    return f"{token[:4]}…{token[-4:]}"


def _build_transaction_url(
    *,
    transaction_url: str | None,
    base_url: str,
    transaction_id: str,
) -> str:
    if transaction_url and transaction_url.strip():
        return transaction_url.strip().rstrip("/")
    base = base_url.rstrip("/")
    return f"{base}{DEFAULT_REST_PATH}/{transaction_id.strip()}"


def _summarize_json(payload: Any, *, max_keys: int = 20) -> str:
    if isinstance(payload, dict):
        keys = list(payload.keys())
        shown = keys[:max_keys]
        more = len(keys) - len(shown)
        parts = [f"keys[{len(keys)}]={shown}"]
        if more > 0:
            parts.append(f"(+{more} more)")
        for hint in ("id", "transactionId", "bs_id", "version", "status", "documents"):
            if hint in payload:
                val = payload[hint]
                if isinstance(val, (str, int, float, bool)) or val is None:
                    parts.append(f"{hint}={val!r}")
        return " ".join(parts)
    if isinstance(payload, list):
        return f"list len={len(payload)}"
    text = str(payload)
    if len(text) > 200:
        return text[:200] + "…"
    return text


def fetch_transaction(
    transaction_url: str,
    access_token: str,
    *,
    timeout_seconds: float = 60.0,
) -> httpx.Response:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    with httpx.Client(timeout=timeout_seconds) as client:
        return client.get(transaction_url, headers=headers)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Obtain Fusion/IDCS access token (client credentials), then GET "
            "commerceDocumentsOraclecpqoTransaction with Bearer auth."
        )
    )
    parser.add_argument("--token-url", default=None, help=f"or ${ENV_TOKEN_URL}")
    parser.add_argument("--client-id", default=None, help=f"or ${ENV_CLIENT_ID}")
    parser.add_argument(
        "--client-secret", default=None, help=f"or ${ENV_CLIENT_SECRET}"
    )
    parser.add_argument("--scope", default=None, help=f"or ${ENV_SCOPE}")
    parser.add_argument(
        "--transaction-url",
        default=None,
        help="Full Get Transaction URL (overrides base-url + transaction-id)",
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--transaction-id", default=DEFAULT_TRANSACTION_ID)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument(
        "--print-body",
        action="store_true",
        help="Print truncated raw response body (default: summary only)",
    )
    args = parser.parse_args(argv)

    token_url = _env_or_arg(args.token_url, ENV_TOKEN_URL)
    client_id = _env_or_arg(args.client_id, ENV_CLIENT_ID)
    client_secret = _env_or_arg(args.client_secret, ENV_CLIENT_SECRET)
    scope = _env_or_arg(args.scope, ENV_SCOPE)

    missing = [
        name
        for name, val in (
            (ENV_TOKEN_URL, token_url),
            (ENV_CLIENT_ID, client_id),
            (ENV_CLIENT_SECRET, client_secret),
            (ENV_SCOPE, scope),
        )
        if not val
    ]
    if missing:
        print(
            "Missing OAuth inputs (set env or pass flags): " + ", ".join(missing),
            file=sys.stderr,
        )
        return 1

    txn_url = _build_transaction_url(
        transaction_url=args.transaction_url,
        base_url=args.base_url,
        transaction_id=args.transaction_id,
    )

    print("Fusion Get Transaction stub (live)")
    print(f"transaction_url={txn_url}")

    oauth = _load_oauth_module()
    try:
        token = oauth.get_fusion_access_token(
            token_url=token_url,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
            timeout_seconds=args.timeout,
        )
    except oauth.FusionOAuthError as exc:
        print(f"[FAIL] OAuth: {exc}", file=sys.stderr)
        return 1

    print(
        f"[OK] token acquired type={token.token_type!r} "
        f"expires_in={token.expires_in} masked={_mask_token(token.access_token)}"
    )

    try:
        response = fetch_transaction(
            txn_url, token.access_token, timeout_seconds=args.timeout
        )
    except httpx.HTTPError as exc:
        print(f"[FAIL] GET request: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"HTTP {response.status_code}")
    try:
        payload = response.json()
    except ValueError:
        body = (response.text or "").replace("\n", " ")[:400]
        print(f"non-JSON body: {body}")
        return 0 if 200 <= response.status_code < 300 else 1

    print(f"summary: {_summarize_json(payload)}")
    if args.print_body:
        dumped = json.dumps(payload, indent=2, default=str)
        if len(dumped) > 2000:
            dumped = dumped[:2000] + "\n…(truncated)"
        print(dumped)

    if 200 <= response.status_code < 300:
        print("[DONE] Get Transaction succeeded")
        return 0
    print("[FAIL] Get Transaction non-2xx", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
