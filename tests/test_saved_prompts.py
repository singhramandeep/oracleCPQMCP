"""Tests for the saved refined-prompt library."""

from __future__ import annotations

from pathlib import Path

from oracle_cpq_mcp.prompts.saved_library import (
    UNSCOPED_PROFILE_FILTER,
    content_hash_for,
    delete_prompt,
    get_entry,
    last_used,
    list_entries,
    list_profile_names,
    sanitize_variables,
    saved_prompts_path,
    search_entries,
    set_enabled,
    upsert_prompt,
)
from oracle_cpq_mcp.prompts.tags import tags_for_tools


def test_saved_prompts_path_defaults_to_prompts_dir(monkeypatch) -> None:
    monkeypatch.delenv("CPQ_SAVED_PROMPTS_PATH", raising=False)
    path = saved_prompts_path()
    assert path.name == "saved_prompts.json"
    assert path.parent.name == ".prompts"


def test_saved_prompts_path_ignores_legacy_config_when_prompts_exists(
    tmp_path: Path, monkeypatch
) -> None:
    from oracle_cpq_mcp.prompts import saved_library as lib

    prompts_dir = tmp_path / ".prompts"
    prompts_dir.mkdir()
    canonical = prompts_dir / "saved_prompts.json"
    canonical.write_text('{"version": 1, "prompts": []}', encoding="utf-8")
    legacy = tmp_path / ".config" / "saved_prompts.json"
    legacy.parent.mkdir()
    legacy.write_text('{"version": 1, "prompts": []}', encoding="utf-8")

    monkeypatch.setattr(lib, "find_project_root", lambda: tmp_path)
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(legacy))
    assert saved_prompts_path() == canonical.resolve()


def test_pin_saved_prompts_env_overrides_legacy(tmp_path: Path) -> None:
    from oracle_cpq_mcp.prompts.saved_library import pin_saved_prompts_env

    legacy = str((tmp_path / ".config" / "saved_prompts.json").resolve())
    env = pin_saved_prompts_env(
        tmp_path,
        {"CPQ_SAVED_PROMPTS_PATH": legacy, "CPQ_CONFIG_DIR": str(tmp_path / ".config")},
    )
    assert env["CPQ_SAVED_PROMPTS_PATH"].endswith(
        str(Path(".prompts") / "saved_prompts.json")
    )
    assert Path(env["CPQ_SAVED_PROMPTS_PATH"]).parent.name == ".prompts"


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


def test_delete_prompt_removes_entry(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "saved_prompts.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(path))
    entry, _ = upsert_prompt(
        title="Gone soon",
        original_user_prompt="delete me",
        refined_prompt="Do {{thing}}",
        path=path,
    )
    assert delete_prompt(entry.id, path=path) is True
    assert get_entry(entry.id, path=path) is None
    assert delete_prompt(entry.id, path=path) is False


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


def test_profile_defaults_none_and_round_trip(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "saved_prompts.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(path))
    from oracle_cpq_mcp.prompts.saved_library import SavedPrompt

    legacy = SavedPrompt.from_dict(
        {
            "id": "legacy",
            "title": "Legacy",
            "original_user_prompt": "x",
            "refined_prompt": "y",
            "tools": [],
        }
    )
    assert legacy.profile is None

    entry, created = upsert_prompt(
        title="Drees users",
        original_user_prompt="list users",
        refined_prompt="List users for {{status}}",
        tools=["list_users"],
        profile="drees",
        path=path,
    )
    assert created is True
    assert entry.profile == "drees"
    loaded = get_entry(entry.id, path=path)
    assert loaded is not None
    assert loaded.profile == "drees"


def test_upsert_dedupes_per_profile(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "saved_prompts.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(path))
    body = "List {{status_filter}} users"
    a, created_a = upsert_prompt(
        title="Users A",
        original_user_prompt="list",
        refined_prompt=body,
        tools=["list_users"],
        profile="drees",
        path=path,
    )
    b, created_b = upsert_prompt(
        title="Users B",
        original_user_prompt="list",
        refined_prompt=body,
        tools=["list_users"],
        profile="focalpoint",
        path=path,
    )
    c, created_c = upsert_prompt(
        title="Users A2",
        original_user_prompt="list again",
        refined_prompt=body,
        tools=["list_users"],
        profile="drees",
        path=path,
    )
    assert created_a is True
    assert created_b is True
    assert created_c is False
    assert a.id != b.id
    assert a.id == c.id
    assert len(list_entries(path)) == 2


def test_search_entries_by_profile(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "saved_prompts.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(path))
    upsert_prompt(
        title="Scoped",
        original_user_prompt="a",
        refined_prompt="Scoped body",
        tools=["list_users"],
        profile="drees",
        path=path,
    )
    upsert_prompt(
        title="Unscoped",
        original_user_prompt="b",
        refined_prompt="Unscoped body",
        tools=["list_groups"],
        path=path,
    )
    by_drees = search_entries(profile="drees", path=path)
    assert len(by_drees) == 1
    assert by_drees[0].title == "Scoped"
    unscoped = search_entries(profile=UNSCOPED_PROFILE_FILTER, path=path)
    assert len(unscoped) == 1
    assert unscoped[0].title == "Unscoped"
    names = list_profile_names(path=path)
    assert names["profiles"] == ["drees"]
    assert names["unscoped_count"] == 1
