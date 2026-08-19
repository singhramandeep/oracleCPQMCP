"""Best-effort MCP progress notifications for long-running tools."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


def report_tool_progress(
    progress: float,
    total: float | None = None,
    *,
    message: str | None = None,
) -> None:
    """Send MCP progress when a FastMCP request context is available."""
    try:
        from fastmcp.server.dependencies import get_context
    except ImportError:
        return

    try:
        ctx = get_context()
    except Exception:
        return

    async def _send() -> None:
        await ctx.report_progress(progress, total, message)

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_send())
    except RuntimeError:
        try:
            asyncio.run(_send())
        except Exception:
            logger.debug("Unable to report MCP progress", exc_info=True)
    except Exception:
        logger.debug("Unable to schedule MCP progress", exc_info=True)


def progress_callback(
    total: float | None = None,
) -> Callable[[float, str | None], None]:
    """Build a callback that reports absolute progress values."""

    def _callback(progress: float, message: str | None = None) -> None:
        report_tool_progress(progress, total, message=message)

    return _callback
