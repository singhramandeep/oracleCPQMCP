"""Elicitation helper with chat-fallback when the host does not support it."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ElicitOutcome:
    """Normalized elicitation / fallback result."""

    status: Literal["accepted", "declined", "cancelled", "unsupported", "error"]
    data: dict[str, Any] | None = None
    message: str | None = None
    needs_user_input: bool = False
    question: str | None = None
    choices: list[str] | None = None


async def elicit_or_fallback(
    ctx: Any | None,
    *,
    message: str,
    response_type: type[Any],
    choices: list[str] | None = None,
) -> ElicitOutcome:
    """Try FastMCP ctx.elicit; on failure return a chat-relay payload."""
    if ctx is None or not hasattr(ctx, "elicit"):
        return ElicitOutcome(
            status="unsupported",
            needs_user_input=True,
            question=message,
            choices=choices,
            message="Elicitation unavailable; ask the user in chat and retry with explicit args.",
        )
    try:
        result = await ctx.elicit(message=message, response_type=response_type)
    except Exception as exc:  # noqa: BLE001 — host capability varies
        logger.info("Elicitation failed (%s); using chat fallback", type(exc).__name__)
        return ElicitOutcome(
            status="unsupported",
            needs_user_input=True,
            question=message,
            choices=choices,
            message=str(exc)[:300],
        )

    action = getattr(result, "action", None)
    if action == "accept":
        data = getattr(result, "data", None)
        if hasattr(data, "__dict__") and not isinstance(data, dict):
            raw = {k: getattr(data, k) for k in getattr(data, "__dataclass_fields__", {})}
            if not raw and hasattr(data, "__dict__"):
                raw = dict(vars(data))
            data = raw
        return ElicitOutcome(status="accepted", data=data if isinstance(data, dict) else {"value": data})
    if action == "decline":
        return ElicitOutcome(status="declined")
    return ElicitOutcome(status="cancelled")


def fallback_payload(outcome: ElicitOutcome) -> dict[str, Any]:
    """Structured payload for agents when elicitation is unsupported."""
    return {
        "needs_user_input": True,
        "question": outcome.question,
        "choices": outcome.choices or [],
        "hint": outcome.message
        or "Ask the user in chat, then call the tool again with their answer as arguments.",
    }
