"""Tests for prompt ratings, comments, and cache/API/mixed run telemetry."""

from __future__ import annotations

from pathlib import Path

import pytest

from oracle_cpq_mcp.prompts import saved_library as lib


@pytest.fixture
def prompts_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "saved_prompts.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(path))
    return path


def _make_prompt(path: Path, *, title: str = "Users") -> lib.SavedPrompt:
    entry, _ = lib.upsert_prompt(
        title=title,
        original_user_prompt="list users",
        refined_prompt=f"List users for {title}",
        tools=["list_users"],
        path=path,
    )
    return entry


def test_upsert_does_not_count_as_completed_run(prompts_path: Path) -> None:
    first, created1 = lib.upsert_prompt(
        title="Active users",
        original_user_prompt="list active users",
        refined_prompt="List {{status_filter}} users",
        variables={"status_filter": "active"},
        tags=["users"],
        tools=["list_users"],
        path=prompts_path,
    )
    second, created2 = lib.upsert_prompt(
        title="Active users v2",
        original_user_prompt="list active users again",
        refined_prompt="List {{status_filter}} users",
        variables={"status_filter": "active"},
        tags=["audit"],
        tools=["list_users"],
        path=prompts_path,
    )
    assert created1 is True
    assert created2 is False
    assert first.id == second.id
    assert second.run_count == 0
    assert second.last_run_at == ""
    assert "audit" in second.tags


def test_rating_validation_and_persist(prompts_path: Path) -> None:
    entry = _make_prompt(prompts_path)
    updated = lib.set_rating(entry.id, 8, path=prompts_path)
    assert updated is not None
    assert updated.rating == 8
    loaded = lib.get_entry(entry.id, path=prompts_path)
    assert loaded is not None
    assert loaded.rating == 8

    with pytest.raises(lib.UpdatePromptError):
        lib.set_rating(entry.id, 0, path=prompts_path)
    with pytest.raises(lib.UpdatePromptError):
        lib.set_rating(entry.id, 11, path=prompts_path)

    cleared = lib.set_rating(entry.id, None, path=prompts_path)
    assert cleared is not None
    assert cleared.rating is None


def test_comment_crud(prompts_path: Path) -> None:
    entry = _make_prompt(prompts_path)
    with_comment = lib.add_comment(entry.id, "Needs clearer tags", path=prompts_path)
    assert with_comment is not None
    assert len(with_comment.comments) == 1
    comment_id = with_comment.comments[0]["id"]
    assert with_comment.comments[0]["text"] == "Needs clearer tags"

    edited = lib.update_comment(
        entry.id, comment_id, "Needs clearer tags and tools", path=prompts_path
    )
    assert edited is not None
    assert edited.comments[0]["text"] == "Needs clearer tags and tools"
    assert edited.comments[0]["updated_at"]

    removed = lib.delete_comment(entry.id, comment_id, path=prompts_path)
    assert removed is not None
    assert removed.comments == []


def test_record_use_tracks_source_averages_separately(prompts_path: Path) -> None:
    entry = _make_prompt(prompts_path)
    r1 = lib.record_use(
        entry.id,
        duration_ms=1000,
        source="cache",
        path=prompts_path,
    )
    r2 = lib.record_use(
        entry.id,
        duration_ms=3000,
        source="cache",
        path=prompts_path,
    )
    r3 = lib.record_use(
        entry.id,
        duration_ms=5000,
        source="api",
        path=prompts_path,
    )
    assert r1 is not None and r2 is not None and r3 is not None
    assert r3.run_count == 3
    cache = r3.stats["cache"]
    api = r3.stats["api"]
    mixed = r3.stats["mixed"]
    assert cache["count"] == 2
    assert cache["last_duration_ms"] == 3000
    assert cache["avg_duration_ms"] == 2000.0
    assert api["count"] == 1
    assert api["last_duration_ms"] == 5000
    assert api["avg_duration_ms"] == 5000.0
    assert mixed["count"] == 0
    assert mixed["avg_duration_ms"] is None
    # Never blend sources into one average field.
    assert "combined" not in r3.stats
    assert len(r3.run_history) == 3
    assert r3.run_history[-1]["source"] == "api"


def test_record_use_rejects_bad_source(prompts_path: Path) -> None:
    entry = _make_prompt(prompts_path)
    with pytest.raises(lib.UpdatePromptError):
        lib.record_use(entry.id, duration_ms=10, source="live", path=prompts_path)


def test_import_preserves_rating_comments_and_stats(prompts_path: Path) -> None:
    source = _make_prompt(prompts_path, title="Importable")
    lib.set_rating(source.id, 9, path=prompts_path)
    lib.add_comment(source.id, "Great prompt", path=prompts_path)
    lib.record_use(source.id, duration_ms=1200, source="api", path=prompts_path)
    lib.record_use(source.id, duration_ms=800, source="cache", path=prompts_path)
    original = lib.get_entry(source.id, path=prompts_path)
    assert original is not None

    payload = original.to_dict()
    # Simulate a fresh library receiving an import of the same content hash.
    other = prompts_path.parent / "other_library.json"
    imported, created = lib.import_prompt(payload, path=other)
    assert created is True
    assert imported.rating == 9
    assert len(imported.comments) == 1
    assert imported.comments[0]["text"] == "Great prompt"
    assert imported.run_count == 2
    assert imported.stats["api"]["count"] == 1
    assert imported.stats["cache"]["count"] == 1
    assert imported.stats["api"]["avg_duration_ms"] == 1200.0
    assert imported.stats["cache"]["avg_duration_ms"] == 800.0

    # Re-import must preserve stats and not bump run_count.
    again, created2 = lib.import_prompt(payload, path=other)
    assert created2 is False
    assert again.run_count == 2
    assert again.rating == 9
