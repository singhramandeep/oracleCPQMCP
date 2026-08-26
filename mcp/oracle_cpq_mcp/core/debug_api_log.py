"""Append-only local debug log for CPQClient HTTP calls (operator-facing)."""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oracle_cpq_mcp.core.config import CPQProfile, find_project_root

logger = logging.getLogger(__name__)

_WRITE_LOCK = threading.Lock()
_warned_write_failure = False


def debug_log_dir() -> Path:
    """Directory for DEBUG_MODE API logs (override with CPQ_DEBUG_LOG_DIR)."""
    if env_dir := os.environ.get("CPQ_DEBUG_LOG_DIR"):
        return Path(env_dir).resolve()
    return find_project_root() / "logs"


def debug_log_path(profile: CPQProfile) -> Path:
    """Path: logs/{customer_id}-{environment}.log."""
    return debug_log_dir() / f"{profile.customer_id}-{profile.environment}.log"


def _format_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str)
    except (TypeError, ValueError):
        return repr(value)


def format_parameter_lines(
    *,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
    accept: str | None = None,
) -> list[str]:
    """Build Parameter: lines for query, optional Accept, and JSON body keys."""
    lines: list[str] = []
    if params:
        for key, value in params.items():
            if value is None:
                continue
            lines.append(f"  query.{key} = {_format_value(value)}")
    if accept is not None:
        lines.append(f"  header.Accept = {accept}")
    if json_body is None:
        lines.append("  body = (none)")
    elif isinstance(json_body, dict):
        if not json_body:
            lines.append("  body = {}")
        else:
            for key, value in json_body.items():
                lines.append(f"  body.{key} = {_format_value(value)}")
    else:
        lines.append(f"  body = {_format_value(json_body)}")
    return lines


def build_debug_block(
    *,
    method: str,
    path: str,
    url: str,
    curl_command: str,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
    accept: str | None = None,
    status: str | int,
    duration_ms: float | None = None,
    timestamp: datetime | None = None,
) -> str:
    """Render one timestamped request block (no response body)."""
    ts = timestamp or datetime.now(timezone.utc)
    stamp = ts.isoformat(timespec="milliseconds")
    rest_path = path if path.startswith("/") else f"/{path}"
    duration_part = f" ({duration_ms:.0f} ms)" if duration_ms is not None else ""
    param_lines = format_parameter_lines(
        params=params, json_body=json_body, accept=accept
    )
    lines = [
        f"========== {stamp} ==========",
        f"{method.upper()} {rest_path}",
        f"URL: {url}",
        f"Status: {status}{duration_part}",
        "",
        "CURL:",
        curl_command,
        "",
        "Parameters:",
        *param_lines,
        "",
    ]
    return "\n".join(lines) + "\n"


def append_api_debug_log(
    profile: CPQProfile,
    *,
    method: str,
    path: str,
    url: str,
    curl_command: str,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
    accept: str | None = None,
    status: str | int,
    duration_ms: float | None = None,
) -> None:
    """Append a debug block when profile.debug_mode is enabled. Never raises."""
    global _warned_write_failure
    if not profile.debug_mode:
        return
    block = build_debug_block(
        method=method,
        path=path,
        url=url,
        curl_command=curl_command,
        params=params,
        json_body=json_body,
        accept=accept,
        status=status,
        duration_ms=duration_ms,
    )
    try:
        target = debug_log_path(profile)
        with _WRITE_LOCK:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as handle:
                handle.write(block)
    except OSError as exc:
        if not _warned_write_failure:
            _warned_write_failure = True
            logger.warning("DEBUG_MODE API log write failed: %s", exc)
