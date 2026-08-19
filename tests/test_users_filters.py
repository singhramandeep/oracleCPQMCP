"""Tests for CPQ user query filter builder."""

from __future__ import annotations

from oracle_cpq_mcp.core.users_filters import build_users_q


def test_build_users_q_active_default() -> None:
    assert build_users_q("active") == "{'status.value':{'$eq':1}}"


def test_build_users_q_inactive() -> None:
    assert build_users_q("inactive") == "{'status.value':{'$eq':0}}"


def test_build_users_q_all() -> None:
    assert build_users_q("all") is None


def test_build_users_q_custom_only_when_all() -> None:
    custom = "{'login':{'$like':'%jsmith%'}}"
    assert build_users_q("all", custom) == custom


def test_build_users_q_and_merge_status_with_custom() -> None:
    custom = "{'login':{'$like':'%jsmith%'}}"
    result = build_users_q("active", custom)
    assert result == f"{{$and:[{{'status.value':{{'$eq':1}}}},{custom}]}}"
