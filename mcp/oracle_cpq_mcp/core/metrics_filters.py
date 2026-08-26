"""Build Oracle CPQ MongoDB q expressions for Metrics API queries."""

from __future__ import annotations

import re

_NON_ALNUM = re.compile(r"[^A-Za-z0-9]")


def normalize_metric_name(name: str) -> str:
    """Uppercase metric name with non-alphanumerics stripped (env / CPQ key form)."""
    return _NON_ALNUM.sub("", name.strip()).upper()


def _escape_q_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _eq_clause(field: str, value: str) -> str:
    return f"{{'{field}':{{'$eq':'{_escape_q_string(value)}'}}}}"


def _range_clause(field: str, *, gte: str | None = None, lte: str | None = None) -> str | None:
    parts: list[str] = []
    if gte:
        parts.append(f"'$gte':'{_escape_q_string(gte)}'")
    if lte:
        parts.append(f"'$lte':'{_escape_q_string(lte)}'")
    if not parts:
        return None
    return f"{{'{field}':{{{','.join(parts)}}}}}"


def build_metrics_q(
    name: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    date_modified_from: str | None = None,
    date_modified_to: str | None = None,
    date_added_from: str | None = None,
    date_added_to: str | None = None,
) -> str | None:
    """Return CPQ ``q`` for optional name and timestamp filters on /metrics.

    Timestamp filters map to ``startTime`` / ``endTime`` / ``dateModified`` /
    ``dateAdded`` with ``$gte`` / ``$lte`` as documented for the Metrics API.
    """
    clauses: list[str] = []

    if name and name.strip():
        clauses.append(_eq_clause("name", normalize_metric_name(name)))

    start_clause = _range_clause("startTime", gte=start_time.strip() if start_time else None)
    if start_clause:
        clauses.append(start_clause)

    end_clause = _range_clause("endTime", lte=end_time.strip() if end_time else None)
    if end_clause:
        clauses.append(end_clause)

    # Independent from/to on the same field → one range object when both set.
    modified = _range_clause(
        "dateModified",
        gte=date_modified_from.strip() if date_modified_from else None,
        lte=date_modified_to.strip() if date_modified_to else None,
    )
    if modified:
        clauses.append(modified)

    added = _range_clause(
        "dateAdded",
        gte=date_added_from.strip() if date_added_from else None,
        lte=date_added_to.strip() if date_added_to else None,
    )
    if added:
        clauses.append(added)

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return "{$and:[" + ",".join(clauses) + "]}"
