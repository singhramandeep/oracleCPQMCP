"""HMAC-bound confirmation tokens for state-changing operations."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import UTC, datetime
from typing import Any

from oracle_cpq_mcp.security.context import SecurityContext
from oracle_cpq_mcp.security.exceptions import ConfirmationInvalidError
from oracle_cpq_mcp.security.settings import SecuritySettings

_TOKEN_VERSION = "v1"


def hash_arguments(tool: str, arguments: dict[str, Any]) -> str:
    """Stable hash of tool name + arguments for confirmation binding."""
    filtered = {
        k: v for k, v in arguments.items() if k not in ("confirmation_token", "confirmed")
    }
    payload = {"tool": tool, "arguments": _normalize_for_hash(filtered)}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _normalize_for_hash(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _normalize_for_hash(v) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_normalize_for_hash(v) for v in value]
    return value


def issue_confirmation_token(
    tool: str,
    arguments: dict[str, Any],
    *,
    context: SecurityContext,
    settings: SecuritySettings,
) -> dict[str, Any]:
    """Issue an HMAC confirmation token bound to tool + args + tenant context."""
    secret = settings.confirmation_secret
    if not secret:
        raise ConfirmationInvalidError(
            "CPQ_CONFIRMATION_SECRET is not configured — "
            "required for write operations when READ_ONLY=false."
        )

    args_hash = hash_arguments(tool, arguments)
    expires_at = int(time.time()) + settings.confirmation_ttl_seconds
    payload = "|".join(
        [
            _TOKEN_VERSION,
            tool,
            context.customer_id,
            context.environment,
            args_hash,
            str(expires_at),
        ]
    )
    signature = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    token = f"{payload}|{signature}"

    return {
        "confirmation_token": token,
        "confirmation_expires_at": datetime.fromtimestamp(
            expires_at, tz=UTC
        ).isoformat(),
        "confirmation_binding": {
            "tool": tool,
            "args_hash": args_hash,
            "customer_id": context.customer_id,
            "environment": context.environment,
        },
    }


def validate_confirmation_token(
    tool: str,
    arguments: dict[str, Any],
    token: str | None,
    *,
    context: SecurityContext,
    settings: SecuritySettings,
) -> None:
    """Validate confirmation token matches tool, args, and context."""
    if not token:
        raise ConfirmationInvalidError("confirmation_token is required for execution.")

    secret = settings.confirmation_secret
    if not secret:
        raise ConfirmationInvalidError("CPQ_CONFIRMATION_SECRET is not configured.")

    parts = token.split("|")
    if len(parts) != 7:
        raise ConfirmationInvalidError("Malformed confirmation token.")

    version, token_tool, customer_id, environment, args_hash, expires_str, signature = parts
    if version != _TOKEN_VERSION:
        raise ConfirmationInvalidError("Unsupported confirmation token version.")
    if token_tool != tool:
        raise ConfirmationInvalidError("Confirmation token does not match tool.")
    if customer_id != context.customer_id or environment != context.environment:
        raise ConfirmationInvalidError("Confirmation token does not match security context.")

    expected_hash = hash_arguments(tool, arguments)
    if args_hash != expected_hash:
        raise ConfirmationInvalidError(
            "Confirmation token does not match current arguments."
        )

    expires_at = int(expires_str)
    if time.time() > expires_at:
        raise ConfirmationInvalidError("Confirmation token has expired.")

    payload = "|".join(parts[:6])
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        raise ConfirmationInvalidError("Invalid confirmation token signature.")
