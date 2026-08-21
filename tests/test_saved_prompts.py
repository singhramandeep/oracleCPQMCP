"""Tests for the saved refined-prompt library."""

from __future__ import annotations

from pathlib import Path

from oracle_cpq_mcp.prompts.saved_library import (
    content_hash_for,
    get_entry,
    last_used,
    list_entries,
    sanitize_variables,
    search_entries,
    set_enabled,
    upsert_prompt,
)
from oracle_cpq_mcp.prompts.tags import tags_for_tools


def test_sanitize_variables_strips_secrets() -> None:
    cleaned = sanitize_variables(
        {
            "status_filter": "active",
            "password": "secret",
            "confirmation_token": "abc",
            "limit": 100,
        }
    )
    assert cleaned == {"status_filter": "active", "limit": 100}


def test_tags_for_tools_includes_domain_and_intent() -> None:
    tags = tags_for_tools(["list_users", "export_users_excel", "update_user"])
    assert "users" in tags
    assert "export" in tags
    assert "write" in tags
    assert "read" in tags


def test_upsert_dedupes_by_hash(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "saved_prompts.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(path))

    first, created1 = upsert_prompt(
        title="Active users",
        original_user_prompt="list active users",
        refined_prompt="List {{status_filter}} users",
        variables={"status_filter": "active"},
        tags=["users"],
        tools=["list_users"],
        path=path,
    )
    second, created2 = upsert_prompt(
        title="Active users v2",
        original_user_prompt="list active users again",
        refined_prompt="List {{status_filter}} users",
        variables={"status_filter": "active"},
        tags=["audit"],
        tools=["list_users"],
        path=path,
    )
    assert created1 is True
    assert created2 is False
    assert first.id == second.id
    assert second.run_count == 2
    assert "audit" in second.tags
    assert "users" in second.tags
    assert len(list_entries(path)) == 1


def test_search_and_last_used(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "saved_prompts.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(path))
    upsert_prompt(
        title="Group audit",
        original_user_prompt="audit groups",
        refined_prompt="Audit groups {{q}}",
        tags=["groups", "audit"],
        tools=["list_groups"],
        path=path,
    )
    upsert_prompt(
        title="User export",
        original_user_prompt="export users",
        refined_prompt="Export {{status_filter}} users",
        tags=["users", "export"],
        tools=["export_users_excel"],
        path=path,
    )
    found = search_entries(query="export", path=path)
    assert len(found) == 1
    assert found[0].title == "User export"
    by_tag = search_entries(tag="audit", path=path)
    assert len(by_tag) == 1
    recent = last_used(1, path=path)
    assert len(recent) == 1


def test_content_hash_stable() -> None:
    a = content_hash_for("Hello   World", ["list_users", "get_user"])
    b = content_hash_for("hello world", ["get_user", "list_users"])
    assert a == b


def test_content_hash_includes_output_format() -> None:
    a = content_hash_for("Same body", ["list_users"], "chat_text")
    b = content_hash_for("Same body", ["list_users"], "json")
    assert a != b


def test_output_format_defaults_and_round_trip(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "saved_prompts.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(path))
    entry, created = upsert_prompt(
        title="Users",
        original_user_prompt="list users",
        refined_prompt="List users",
        tools=["list_users"],
        path=path,
    )
    assert created is True
    assert entry.output_format == "chat_text"
    loaded = get_entry(entry.id, path=path)
    assert loaded is not None
    assert loaded.output_format == "chat_text"

    # Legacy JSON without output_format still loads as chat_text
    from oracle_cpq_mcp.prompts.saved_library import SavedPrompt

    legacy = SavedPrompt.from_dict(
        {
            "id": "legacy-id",
            "title": "Legacy",
            "original_user_prompt": "x",
            "refined_prompt": "y",
            "tools": [],
        }
    )
    assert legacy.output_format == "chat_text"

    json_entry, created_json = upsert_prompt(
        title="Users JSON",
        original_user_prompt="list users as json",
        refined_prompt="List users",
        tools=["list_users"],
        output_format="json",
        path=path,
    )
    assert created_json is True
    assert json_entry.id != entry.id
    assert json_entry.output_format == "json"


def test_get_entry_missing(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "saved_prompts.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(path))
    assert get_entry("missing", path=path) is None


def test_enabled_defaults_true_and_filters_lists(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "saved_prompts.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(path))
    entry, _ = upsert_prompt(
        title="Keep me",
        original_user_prompt="x",
        refined_prompt="Do {{thing}}",
        tags=["users"],
        tools=["list_users"],
        path=path,
    )
    assert entry.enabled is True
    assert len(list_entries(path)) == 1

    disabled = set_enabled(entry.id, False, path=path)
    assert disabled is not None
    assert disabled.enabled is False
    assert list_entries(path) == []
    assert len(list_entries(path, include_disabled=True)) == 1
    assert search_entries(query="Keep", path=path) == []
    assert search_entries(query="Keep", path=path, include_disabled=True)
    loaded = get_entry(entry.id, path=path)
    assert loaded is not None and loaded.enabled is False


def test_search_by_tool(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "saved_prompts.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(path))
    upsert_prompt(
        title="Users",
        original_user_prompt="u",
        refined_prompt="List users",
        tools=["list_users"],
        path=path,
    )
    upsert_prompt(
        title="Groups",
        original_user_prompt="g",
        refined_prompt="List groups",
        tools=["list_groups"],
        path=path,
    )
    found = search_entries(tool="list_groups", path=path)
    assert len(found) == 1
    assert found[0].title == "Groups"


def test_upsert_preserves_enabled_on_dedupe(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "saved_prompts.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(path))
    entry, _ = upsert_prompt(
        title="A",
        original_user_prompt="a",
        refined_prompt="Same body",
        tools=["list_users"],
        path=path,
    )
    set_enabled(entry.id, False, path=path)
    again, created = upsert_prompt(
        title="A2",
        original_user_prompt="a2",
        refined_prompt="Same body",
        tools=["list_users"],
        path=path,
    )
    assert created is False
    assert again.enabled is False
