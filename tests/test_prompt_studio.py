"""Tests for Prompt Studio placeholders, sidecar store, and API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.prompt_studio.placeholders import (
    extract_placeholders,
    fill_placeholders,
    reconcile_variables,
    suggest_var_name,
    validate_var_name,
    wrap_selection,
)
from apps.prompt_studio import store as studio_store
from oracle_cpq_mcp.prompts import saved_library


def test_extract_placeholders_order_unique():
    text = "Hello {{name}} and {{name}} then {{output_format}}"
    assert extract_placeholders(text) == ["name", "output_format"]


def test_fill_placeholders():
    text = "Hi {{name}}, format={{output_format}}"
    assert fill_placeholders(text, {"name": "Ada", "output_format": "json"}) == "Hi Ada, format=json"
    assert fill_placeholders(text, {"name": "Ada"}) == "Hi Ada, format="


def test_wrap_selection_and_suggest_var_name():
    text = "Search for OCL , FPL in all BML"
    name = suggest_var_name("OCL , FPL", {"output_format"})
    assert validate_var_name(name) == name
    updated = wrap_selection(text, 11, 20, name)
    assert "{{" + name + "}}" in updated
    assert "OCL , FPL" not in updated


def test_reconcile_variables():
    merged = reconcile_variables(
        "Hi {{name}} as {{output_format}}",
        {"name": "Ada", "old_var": "drop me"},
    )
    assert merged == {"name": "Ada", "output_format": ""}


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
    assert "disabled_count" in info
    assert "help" in info
    assert "config_dir" in info


def test_api_sort_recent_first(studio_client, tmp_path: Path):
    client, entry = studio_client
    prompts_path = tmp_path / "saved_prompts.json"
    saved_library.upsert_prompt(
        title="Older prompt",
        original_user_prompt="old",
        refined_prompt="Old {{output_format}}",
        variables={"output_format": "chat_text"},
        tags=["meta"],
        tools=[],
        path=prompts_path,
    )
    listed = client.get("/api/prompts", params={"sort": "recent"}).json()
    ids = [p["id"] for p in listed["prompts"]]
    assert ids[0] == entry.id


def test_api_include_disabled(studio_client):
    client, entry = studio_client
    saved_library.set_enabled(entry.id, False)
    hidden = client.get("/api/prompts").json()
    assert entry.id not in {p["id"] for p in hidden["prompts"]}
    shown = client.get("/api/prompts", params={"include_disabled": True}).json()
    match = next(p for p in shown["prompts"] if p["id"] == entry.id)
    assert match["enabled"] is False
    saved_library.set_enabled(entry.id, True)


def test_api_patch_prompt(studio_client):
    client, entry = studio_client
    patched = client.patch(
        f"/api/prompts/{entry.id}",
        json={
            "title": "Renamed users prompt",
            "refined_prompt": "List users for {{customer}} in {{environment}} as {{output_format}}",
            "variables": {
                "customer": "focalpoint",
                "environment": "dev",
                "output_format": "chat_text",
            },
        },
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["title"] == "Renamed users prompt"
    assert "environment" in body["placeholders"]


def test_api_make_variable(studio_client):
    client, entry = studio_client
    text = "Search OCL , FPL in BML for {{customer}}"
    start = text.index("OCL")
    end = text.index("FPL") + 3
    resp = client.post(
        f"/api/prompts/{entry.id}/make-variable",
        json={
            "field": "refined_prompt",
            "start": start,
            "end": end,
            "var_name": "search_tokens",
            "text": text,
            "variables": {"customer": "focalpoint"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "{{search_tokens}}" in data["refined_prompt"]
    assert data["variables"]["search_tokens"] == "OCL , FPL"


def test_update_prompt_hash_collision(studio_client, tmp_path: Path):
    _, entry = studio_client
    prompts_path = tmp_path / "saved_prompts.json"
    other, _ = saved_library.upsert_prompt(
        title="Other",
        original_user_prompt="other",
        refined_prompt="Different body {{output_format}}",
        variables={"output_format": "chat_text"},
        tags=[],
        tools=["list_users"],
        output_format="chat_text",
        path=prompts_path,
    )
    with pytest.raises(saved_library.UpdatePromptError):
        saved_library.update_prompt(
            entry.id,
            refined_prompt=other.refined_prompt,
            tools=other.tools,
            output_format=other.output_format,
            path=prompts_path,
        )


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
    assert 'id="modalTitleDisplay"' in index_html
    assert 'id="modalEnabledToggle"' in index_html
    assert 'id="editBtn"' in index_html
    assert 'id="showDisabledToggle"' in index_html
    assert "?v=" in index_html
    assert "/static/app.js?v=" in index_html
    assert 'aria-controls="modalOriginal"' in index_html
    assert 'aria-controls="modalTemplate"' in index_html
    assert "is-collapsed" in index_html

    css = client.get("/static/styles.css").text
    assert ".code-block.is-collapsed" in css
    assert ".code-block-original.is-collapsed" in css
    assert "flex: none" in css
    assert ".field-head" in css
    assert ".field-toggle" in css

    js = client.get("/static/app.js").text
    assert "data-edit" in js
    assert "openRunSafe" in js
    assert "resetRunModalState" in js
    assert 'closest("[data-run]")' in js


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
    assert "openRunSafe" in js
    assert "LOADED" not in js
    assert "from ${info.path}" not in js


def test_index_cache_control(studio_client):
    client, _ = studio_client
    resp = client.get("/")
    assert resp.status_code == 200
    assert "no-cache" in (resp.headers.get("cache-control") or "").lower()
    assert "?v=0.2.0" not in resp.text
    assert f"?v=" in resp.text
    from apps.prompt_studio import __version__ as studio_version

    assert f"?v={studio_version}" in resp.text
    js_resp = client.get("/static/app.js")
    assert js_resp.status_code == 200
    assert "no-cache" in (js_resp.headers.get("cache-control") or "").lower()
    assert "bindClick(\"refreshBtn\"" in js_resp.text or "bindClick('refreshBtn'" in js_resp.text
    assert "loadProfiles" in js_resp.text
    assert "profileFilter" in js_resp.text


def test_api_profile_filter(studio_client):
    client, entry = studio_client
    created = client.post(
        "/api/prompts",
        json={
            "title": "Profile scoped",
            "original_user_prompt": "scoped",
            "refined_prompt": "Do {{thing}} for profile filter test",
            "tags": ["profile-test"],
            "profile": "drees",
        },
    )
    assert created.status_code == 200
    assert created.json()["profile"] == "drees"

    profiles = client.get("/api/profiles")
    assert profiles.status_code == 200
    body = profiles.json()
    assert "drees" in body["profiles"]
    assert body["unscoped_count"] >= 1  # fixture entry has no profile

    filtered = client.get("/api/prompts", params={"profile": "drees"})
    assert filtered.status_code == 200
    titles = [p["title"] for p in filtered.json()["prompts"]]
    assert "Profile scoped" in titles
    assert entry.title not in titles

    unscoped = client.get("/api/prompts", params={"profile": "__unscoped__"})
    assert unscoped.status_code == 200
    unscoped_titles = [p["title"] for p in unscoped.json()["prompts"]]
    assert entry.title in unscoped_titles
    assert "Profile scoped" not in unscoped_titles


def test_api_create_import_export_help(studio_client):
    client, entry = studio_client

    info = client.get("/api/library_info")
    assert info.status_code == 200
    assert info.json()["path"]
    assert "commands" in info.json()
    assert "restart" in info.json()["commands"]

    help_resp = client.get("/api/help")
    assert help_resp.status_code == 200
    help_body = help_resp.json()
    assert help_body["library_path"]
    assert len(help_body["sections"]) >= 4
    assert "restart" in help_body["commands"]

    created = client.post(
        "/api/prompts",
        json={
            "title": "Manual prompt",
            "original_user_prompt": "do the thing",
            "refined_prompt": "Do {{thing}} as {{output_format}}",
            "tags": ["manual"],
            "output_format": "chat_text",
        },
    )
    assert created.status_code == 200
    assert created.json()["created"] is True
    assert created.json()["title"] == "Manual prompt"

    payload = {
        "version": 1,
        "prompts": [
            {
                "title": "Imported A",
                "original_user_prompt": "a",
                "refined_prompt": "Import body A unique {{output_format}}",
                "tags": ["x"],
                "tools": [],
                "output_format": "chat_text",
            },
            {
                "title": "Imported B",
                "original_user_prompt": "b",
                "refined_prompt": "Import body B unique {{output_format}}",
                "tags": [],
                "tools": [],
                "output_format": "json",
            },
            {
                "title": "Empty refined",
                "refined_prompt": "   ",
            },
        ],
    }
    preview = client.post("/api/prompts/import/preview", json={"data": payload})
    assert preview.status_code == 200
    assert preview.json()["count"] == 3
    assert preview.json()["candidates"][2]["empty_refined"] is True

    applied = client.post(
        "/api/prompts/import",
        json={
            "import_label": "Teammate Export Sep25",
            "indices": [0, 1, 2],
            "prompts": payload["prompts"],
        },
    )
    assert applied.status_code == 200
    body = applied.json()
    assert body["imported"] == 2
    assert body["skipped_empty"] == 1
    assert "imported" in body["import_tags"]
    assert "import:teammate_export_sep25" in body["import_tags"]

    tagged = client.get("/api/prompts", params={"tag": "import:teammate_export_sep25"})
    assert tagged.json()["count"] >= 2

    export = client.post(
        "/api/prompts/export",
        json={"ids": [entry.id]},
    )
    assert export.status_code == 200
    assert "attachment" in (export.headers.get("content-disposition") or "").lower()
    exported = export.json()
    assert exported["prompts"]
    assert exported["prompts"][0]["id"] == entry.id


def test_import_batch_slug_helpers():
    assert saved_library.import_batch_slug("Hello World!") == "hello_world"
    assert saved_library.import_batch_tags("Batch One") == [
        "imported",
        "import:batch_one",
    ]
    rows = saved_library.normalize_import_payload(
        {"prompts": [{"title": "t", "refined_prompt": "r"}]}
    )
    assert len(rows) == 1
    single = saved_library.normalize_import_payload(
        {"title": "t", "refined_prompt": "r"}
    )
    assert len(single) == 1
