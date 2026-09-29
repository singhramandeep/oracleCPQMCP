"""Generate an Oracle Fusion / IDCS OAuth access token (client credentials).

CLI wrapper around ``oracle_cpq_mcp.security.fusion_oauth``. Pass credentials via
flags or ``FUSION_OAUTH_*`` env vars. Never hardcode client secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict

from oracle_cpq_mcp.security.fusion_oauth import (  # noqa: F401 — re-export for CLI/tests
    ENV_CLIENT_ID,
    ENV_CLIENT_SECRET,
    ENV_SCOPE,
    ENV_TOKEN_URL,
    FusionOAuthError,
    FusionOAuthToken,
    get_fusion_access_token,
    validate_oauth_inputs,
)


def _env_or_arg(flag_value: str | None, env_name: str) -> str | None:
    if flag_value is not None and str(flag_value).strip():
        return flag_value
    return os.environ.get(env_name)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Obtain a Fusion/IDCS OAuth access token via client credentials. "
            "Credentials via flags or FUSION_OAUTH_* env vars."
        )
    )
    parser.add_argument("--token-url", default=None, help=f"or ${ENV_TOKEN_URL}")
    parser.add_argument("--client-id", default=None, help=f"or ${ENV_CLIENT_ID}")
    parser.add_argument(
        "--client-secret", default=None, help=f"or ${ENV_CLIENT_SECRET}"
    )
    parser.add_argument("--scope", default=None, help=f"or ${ENV_SCOPE}")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON with access_token, token_type, expires_in, scope",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = get_fusion_access_token(
            token_url=_env_or_arg(args.token_url, ENV_TOKEN_URL) or "",
            client_id=_env_or_arg(args.client_id, ENV_CLIENT_ID) or "",
            client_secret=_env_or_arg(args.client_secret, ENV_CLIENT_SECRET) or "",
            scope=_env_or_arg(args.scope, ENV_SCOPE) or "",
            timeout_seconds=args.timeout,
        )
    except FusionOAuthError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        print(result.access_token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
