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


def test_api_list_includes_original_preview(studio_client):
    client, entry = studio_client
    listed = client.get("/api/prompts").json()
    match = next(p for p in listed["prompts"] if p["id"] == entry.id)
    assert match["original_user_prompt"] == "list users"
    assert "list users" in match["original_preview"]


def test_api_library_info(studio_client, tmp_path: Path):
    client, _ = studio_client
    info = client.get("/api/library_info").json()
    assert info["exists"] is True
    assert info["enabled_count"] >= 1
    assert info["total_count"] >= info["enabled_count"]
    assert info["path"].endswith("saved_prompts.json")
    assert info["last_modified"] is not None
    assert "T" in info["last_modified"] and info["last_modified"].endswith("Z")


def test_api_delete_prompt(studio_client):
    client, entry = studio_client
    studio_store.toggle_favorite(entry.id)
    suite = studio_store.create_suite("with prompt")
    studio_store.add_prompt_to_suite(suite["id"], entry.id)

    deleted = client.delete(f"/api/prompts/{entry.id}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    ids = {p["id"] for p in client.get("/api/prompts").json()["prompts"]}
    assert entry.id not in ids
    assert entry.id not in (studio_store.load_store().get("favorites") or [])
    updated_suite = studio_store.get_suite(suite["id"])
    assert updated_suite is not None
    assert entry.id not in (updated_suite.get("prompt_ids") or [])

    again = client.delete(f"/api/prompts/{entry.id}")
    assert again.status_code == 404


def test_api_download_prompts_library(studio_client):
    client, entry = studio_client

    resp = client.get("/api/prompts/download")
    assert resp.status_code == 200
    assert "attachment" in (resp.headers.get("content-disposition") or "").lower()
    assert "saved_prompts_" in (resp.headers.get("content-disposition") or "")
    assert "application/json" in (resp.headers.get("content-type") or "")
    payload = resp.json()
    assert "prompts" in payload
    ids = [p.get("id") for p in payload["prompts"] if isinstance(p, dict)]
    assert entry.id in ids

    index_html = client.get("/").text
    assert 'id="downloadAllBtn"' in index_html
    js = client.get("/static/app.js").text
    assert "/api/prompts/download" in js


def test_run_modal_expandable_prompt_blocks(studio_client):
    client, _ = studio_client

    index_html = client.get("/").text
    assert 'id="toggleOriginal"' in index_html
    assert 'id="toggleTemplate"' in index_html
    assert 'aria-controls="modalOriginal"' in index_html
    assert 'aria-controls="modalTemplate"' in index_html
    assert "is-collapsed" in index_html

    css = client.get("/static/styles.css").text
    assert ".code-block.is-collapsed" in css
    assert ".code-block-original.is-collapsed" in css
    assert "flex: none" in css
    assert ".field-head" in css
    assert ".field-toggle" in css


def test_sidebar_total_prompts_markup(studio_client):
    client, _ = studio_client

    index_html = client.get("/").text
    assert 'id="sidebarTotalCount"' in index_html
    assert "prompts available" in index_html
    assert 'class="sidebar-total"' in index_html
    assert "tags-section" in index_html

    css = client.get("/static/styles.css").text
    assert ".sidebar-total" in css
    assert ".sidebar-total-number" in css
    assert "margin-top: auto" in css
    assert "max-height: min(42vh, 260px)" in css
    assert ".action-menu-panel" in css
    assert ".card-meta-line" in css

    js = client.get("/static/app.js").text
    assert "updateSidebarTotal" in js
    assert "total_count" in js
    assert "await refreshLibrary()" in js
    assert "updateResultCount" in js
    assert "matching" in js
    assert "secondaryActionsHtml" in js
    assert "cardMetaHtml" in js
    assert "el.title" in js
    assert "LOADED" not in js
    assert "from ${info.path}" not in js
