"""Mock stub to exercise fusion_oauth_token without a live IDCS call.

Run from repo root (venv active):

    python utilities/stub_fusion_oauth_token.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import httpx
import respx

_UTIL_DIR = Path(__file__).resolve().parent
_MOD_PATH = _UTIL_DIR / "fusion_oauth_token.py"

TOKEN_URL = "https://idcs-stub.example.identity.oraclecloud.com/oauth2/v1/token"
SCOPE = "urn:opc:resource:fusion:stub:cpq/"
CLIENT_ID = "stub-client-id"
CLIENT_SECRET = "stub-client-secret"
FAKE_TOKEN = "stubtok_ABCDEFGHijklmnopQRSTUVWX"


def _load_oauth_module():
    spec = importlib.util.spec_from_file_location("fusion_oauth_token", _MOD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {_MOD_PATH}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _mask_token(token: str) -> str:
    if len(token) <= 8:
        return "…"
    return f"{token[:4]}…{token[-4:]}"


def _run_success(mod) -> None:
    with respx.mock:
        respx.post(TOKEN_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "access_token": FAKE_TOKEN,
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "scope": SCOPE,
                },
            )
        )
        result = mod.get_fusion_access_token(
            TOKEN_URL, CLIENT_ID, CLIENT_SECRET, SCOPE, timeout_seconds=5
        )
    print("[PASS] success path")
    print(f"  validation + mocked HTTP OK")
    print(f"  token_type={result.token_type}")
    print(f"  expires_in={result.expires_in}")
    print(f"  access_token(masked)={_mask_token(result.access_token)}")
    if result.access_token != FAKE_TOKEN:
        raise AssertionError("unexpected access_token value")


def _run_unauthorized(mod) -> None:
    with respx.mock:
        respx.post(TOKEN_URL).mock(
            return_value=httpx.Response(401, text='{"error":"invalid_client"}')
        )
        try:
            mod.get_fusion_access_token(
                TOKEN_URL, CLIENT_ID, CLIENT_SECRET, SCOPE, timeout_seconds=5
            )
        except mod.FusionOAuthError as exc:
            msg = str(exc)
            print("[PASS] 401 path raised FusionOAuthError as expected")
            print(f"  message={msg}")
            if CLIENT_SECRET in msg:
                raise AssertionError("client secret leaked in error message")
            return
    raise AssertionError("expected FusionOAuthError on HTTP 401")


def main() -> int:
    print("Fusion OAuth stub (mock IDCS — no live credentials)")
    print(f"token_url={TOKEN_URL}")
    try:
        mod = _load_oauth_module()
        _run_success(mod)
        _run_unauthorized(mod)
    except Exception as exc:  # noqa: BLE001 — stub reports failure clearly
        print(f"[FAIL] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print("[DONE] stub checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
