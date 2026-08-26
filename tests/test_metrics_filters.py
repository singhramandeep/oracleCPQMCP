"""Tests for Metrics API q filter builder."""

from __future__ import annotations

from oracle_cpq_mcp.core.metrics_filters import build_metrics_q, normalize_metric_name


def test_normalize_metric_name() -> None:
    assert normalize_metric_name("quotes") == "QUOTES"
    assert normalize_metric_name(" Partner-Quotes ") == "PARTNERQUOTES"


def test_build_metrics_q_empty() -> None:
    assert build_metrics_q() is None


def test_build_metrics_q_name_only() -> None:
    assert build_metrics_q(name="quotes") == "{'name':{'$eq':'QUOTES'}}"


def test_build_metrics_q_time_filters() -> None:
    q = build_metrics_q(
        start_time="2026-08-11T00:00:00.000Z",
        end_time="2026-08-25T23:59:59.000Z",
        date_added_from="2026-08-11T00:00:00.000Z",
    )
    assert q is not None
    assert "'startTime':{'$gte':'2026-08-11T00:00:00.000Z'}" in q
    assert "'endTime':{'$lte':'2026-08-25T23:59:59.000Z'}" in q
    assert "'dateAdded':{'$gte':'2026-08-11T00:00:00.000Z'}" in q
    assert q.startswith("{$and:[")


def test_build_metrics_q_date_modified_range() -> None:
    q = build_metrics_q(
        date_modified_from="2026-01-01T00:00:00.000Z",
        date_modified_to="2026-01-31T23:59:59.000Z",
    )
    assert q == (
        "{'dateModified':{'$gte':'2026-01-01T00:00:00.000Z',"
        "'$lte':'2026-01-31T23:59:59.000Z'}}"
    )


def test_build_metrics_q_name_and_added() -> None:
    q = build_metrics_q(name="QUOTES", date_added_from="2026-08-11T00:00:00.000Z")
    assert q == (
        "{$and:[{'name':{'$eq':'QUOTES'}},"
        "{'dateAdded':{'$gte':'2026-08-11T00:00:00.000Z'}}]}"
    )
