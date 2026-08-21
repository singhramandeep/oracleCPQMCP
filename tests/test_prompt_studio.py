"""Tests for Prompt Studio placeholders, sidecar store, and API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.prompt_studio.placeholders import extract_placeholders, fill_placeholders
from apps.prompt_studio import store as studio_store
from oracle_cpq_mcp.prompts import saved_library


def test_extract_placeholders_order_unique():
    text = "Hello {{name}} and {{name}} then {{output_format}}"
    assert extract_placeholders(text) == ["name", "output_format"]


def test_fill_placeholders():
    text = "Hi {{name}}, format={{output_format}}"
    assert fill_placeholders(text, {"name": "Ada", "output_format": "json"}) == "Hi Ada, format=json"
    assert fill_placeholders(text, {"name": "Ada"}) == "Hi Ada, format="


def test_sidecar_favorites_suites_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "prompt_studio.json"
    monkeypatch.setenv("CPQ_PROMPT_STUDIO_PATH", str(path))

    assert studio_store.toggle_favorite("p1") is True
    assert studio_store.is_favorite("p1") is True
    assert studio_store.toggle_favorite("p1") is False

    suite = studio_store.create_suite("Daily")
    updated = studio_store.add_prompt_to_suite(suite["id"], "p1")
    assert updated is not None
    assert updated["prompt_ids"] == ["p1"]
    assert studio_store.update_suite(suite["id"], name="Weekly")["name"] == "Weekly"
    assert studio_store.delete_suite(suite["id"]) is True

    hist = studio_store.append_variable_history({"customer": "acme", "empty": "  "})
    assert hist["customer"] == ["acme"]
    hist2 = studio_store.append_variable_history({"customer": "beta"})
    assert hist2["customer"][:2] == ["beta", "acme"]
    # Cap
    for i in range(15):
        studio_store.append_variable_history({"customer": f"c{i}"})
    assert len(studio_store.get_variable_history()["customer"]) == studio_store.HISTORY_CAP


@pytest.fixture
def studio_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    prompts_path = tmp_path / "saved_prompts.json"
    studio_path = tmp_path / "prompt_studio.json"
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(prompts_path))
    monkeypatch.setenv("CPQ_PROMPT_STUDIO_PATH", str(studio_path))

    entry, _ = saved_library.upsert_prompt(
        title="List users",
        original_user_prompt="list users",
        refined_prompt="List users for {{customer}} as {{output_format}}",
        variables={"customer": "focalpoint", "output_format": "chat_text"},
        tags=["users", "read"],
        tools=["list_users"],
        output_format="chat_text",
        path=prompts_path,
    )

    from apps.prompt_studio.app import create_app

    client = TestClient(create_app())
    return client, entry


def test_api_list_search_favorite_generate(studio_client):
    client, entry = studio_client

    listed = client.get("/api/prompts")
    assert listed.status_code == 200
    assert listed.json()["count"] >= 1

    searched = client.get("/api/prompts", params={"q": "users"})
    assert any(p["id"] == entry.id for p in searched.json()["prompts"])

    tagged = client.get("/api/prompts", params={"tag": "users"})
    assert tagged.json()["count"] >= 1

    fav = client.post(f"/api/prompts/{entry.id}/favorite")
    assert fav.json()["favorited"] is True
    fav_only = client.get("/api/prompts", params={"favorites_only": True})
    assert any(p["id"] == entry.id for p in fav_only.json()["prompts"])

    detail = client.get(f"/api/prompts/{entry.id}")
    assert detail.status_code == 200
    assert "customer" in detail.json()["placeholders"]

    suite = client.post("/api/suites", json={"name": "Ops"}).json()
    added = client.post(f"/api/suites/{suite['id']}/prompts", json={"prompt_id": entry.id})
    assert entry.id in added.json()["prompt_ids"]

    gen = client.post(
        "/api/generate",
        json={"prompt_id": entry.id, "values": {"customer": "acme", "output_format": "json"}},
    )
    assert gen.status_code == 200
    assert gen.json()["filled_text"] == "List users for acme as json"

    hist = client.get("/api/variable-history").json()["variable_history"]
    assert hist["customer"][0] == "acme"


def test_api_health(studio_client):
    client, _ = studio_client
    assert client.get("/api/health").json()["status"] == "ok"
