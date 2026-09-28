"""Tests for Prompt Studio API log viewer (parse / list / filter / safety)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.prompt_studio import log_viewer
from oracle_cpq_mcp.core.debug_api_log import build_debug_block

SAMPLE_BLOCKS = """\
========== 2026-09-10T12:03:49.018+00:00 ==========
GET /productFamilies
URL: https://dev.example.com/rest/v18/productFamilies?limit=50&offset=0
Status: 200 (756 ms)

CURL:
curl -X GET -u 'user:***' -H 'Accept: application/json' 'https://dev.example.com/rest/v18/productFamilies?limit=50&offset=0'

Parameters:
  query.limit = 50
  query.offset = 0
  body = (none)

========== 2026-09-10T12:04:01.000+00:00 ==========
POST /commerceDocuments
URL: https://dev.example.com/rest/v18/commerceDocuments
Status: 500 (1200 ms)

CURL:
curl -X POST -u 'user:***' 'https://dev.example.com/rest/v18/commerceDocuments'

Parameters:
  body = {}

========== 2026-09-10T12:04:10.000+00:00 ==========
GET /users
URL: https://dev.example.com/rest/v18/users
Status: 404 (90 ms)

CURL:
curl -X GET -u 'user:***' 'https://dev.example.com/rest/v18/users'

Parameters:
  body = (none)
"""


def test_parse_log_text_extracts_fields():
    entries = log_viewer.parse_log_text(SAMPLE_BLOCKS)
    assert len(entries) == 3
    assert entries[0].method == "GET"
    assert entries[0].path == "/productFamilies"
    assert entries[0].status == 200
    assert entries[0].duration_ms == 756.0
    assert "user:***" in entries[0].curl
    assert entries[1].method == "POST"
    assert entries[1].status == 500
    assert entries[2].status == 404


def test_split_profile_env():
    assert log_viewer.split_profile_env("test-dev") == ("test", "dev")
    assert log_viewer.split_profile_env("my-company-prod") == ("my-company", "prod")
    assert log_viewer.split_profile_env("solo") == ("solo", "")


def test_filter_and_summarize():
    entries = log_viewer.parse_log_text(SAMPLE_BLOCKS)
    errors = log_viewer.filter_entries(entries, status="error")
    assert len(errors) == 2
    posts = log_viewer.filter_entries(entries, method="POST")
    assert len(posts) == 1
    slow = log_viewer.filter_entries(entries, min_ms=1000)
    assert len(slow) == 1 and slow[0].status == 500
    path_hits = log_viewer.filter_entries(entries, path_contains="users")
    assert len(path_hits) == 1
    q_hits = log_viewer.filter_entries(entries, q="productfamilies")
    assert len(q_hits) == 1

    summary = log_viewer.summarize_entries(entries)
    assert summary["count"] == 3
    assert summary["error_count"] == 2
    assert summary["status_buckets"]["2xx"] == 1
    assert summary["status_buckets"]["5xx"] == 1
    assert summary["status_buckets"]["4xx"] == 1
    assert summary["method_counts"]["GET"] == 2
    assert summary["p50_ms"] is not None
    assert summary["p95_ms"] is not None
    assert len(summary["latency_histogram"]) == 5


def test_resolve_log_path_rejects_traversal(tmp_path: Path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "ok-dev.log").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        log_viewer.resolve_log_path("../ok-dev.log", logs)
    with pytest.raises(ValueError):
        log_viewer.resolve_log_path("subdir/x.log", logs)
    with pytest.raises(ValueError):
        log_viewer.resolve_log_path("ok-dev.txt", logs)
    with pytest.raises(FileNotFoundError):
        log_viewer.resolve_log_path("missing-dev.log", logs)
    path = log_viewer.resolve_log_path("ok-dev.log", logs)
    assert path.name == "ok-dev.log"


def test_list_log_files_empty_and_populated(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert log_viewer.list_log_files(empty) == []

    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "alpha-dev.log").write_text(SAMPLE_BLOCKS, encoding="utf-8")
    (logs / "beta-test.log").write_text("========== t ==========\nGET /x\n", encoding="utf-8")
    rows = log_viewer.list_log_files(logs)
    assert len(rows) == 2
    assert {r["name"] for r in rows} == {"alpha-dev.log", "beta-test.log"}
    alpha = next(r for r in rows if r["name"] == "alpha-dev.log")
    assert alpha["profile"] == "alpha"
    assert alpha["environment"] == "dev"


def test_parse_matches_build_debug_block():
    block = build_debug_block(
        method="GET",
        path="/parts",
        url="https://example.com/rest/v18/parts",
        curl_command="curl -X GET -u 'u:***' 'https://example.com/rest/v18/parts'",
        params={"limit": 10},
        status=200,
        duration_ms=123.4,
    )
    entries = log_viewer.parse_log_text(block)
    assert len(entries) == 1
    assert entries[0].method == "GET"
    assert entries[0].path == "/parts"
    assert entries[0].status == 200
    assert entries[0].duration_ms == 123.0


@pytest.fixture
def logs_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    prompts_path = tmp_path / "saved_prompts.json"
    studio_path = tmp_path / "prompt_studio.json"
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "test-dev.log").write_text(SAMPLE_BLOCKS, encoding="utf-8")
    monkeypatch.setenv("CPQ_SAVED_PROMPTS_PATH", str(prompts_path))
    monkeypatch.setenv("CPQ_PROMPT_STUDIO_PATH", str(studio_path))
    monkeypatch.setenv("CPQ_DEBUG_LOG_DIR", str(logs_dir))
    from apps.prompt_studio.app import create_app

    return TestClient(create_app()), logs_dir


def test_api_list_and_get_log(logs_client):
    client, _logs_dir = logs_client
    listed = client.get("/api/logs")
    assert listed.status_code == 200
    body = listed.json()
    assert body["count"] == 1
    assert body["files"][0]["name"] == "test-dev.log"

    detail = client.get("/api/logs/test-dev.log", params={"status": "error"})
    assert detail.status_code == 200
    data = detail.json()
    assert data["total_matched"] == 2
    assert data["summary"]["error_count"] == 2
    assert data["truncated"] is False
    assert all(e["status"] in (404, 500) for e in data["entries"])

    filtered = client.get(
        "/api/logs/test-dev.log",
        params={"method": "GET", "path_contains": "product"},
    )
    assert filtered.json()["total_matched"] == 1

    raw = client.get("/api/logs/test-dev.log/raw")
    assert raw.status_code == 200
    assert b"productFamilies" in raw.content


def test_api_rejects_bad_name(logs_client):
    client, _ = logs_client
    # Non-.log names hit our ValueError (400). Path escapes are covered in
    # test_resolve_log_path_rejects_traversal (Starlette may normalize ../ in URLs).
    assert client.get("/api/logs/not-a-log.txt").status_code == 400
    assert client.get("/api/logs/missing-dev.log").status_code == 404


def test_help_mentions_api_logs(logs_client):
    client, _ = logs_client
    help_body = client.get("/api/help").json()
    titles = [s["title"] for s in help_body["sections"]]
    assert "API logs" in titles


def test_index_cache_bust_version(logs_client):
    client, _ = logs_client
    from apps.prompt_studio import __version__ as studio_version

    resp = client.get("/")
    assert resp.status_code == 200
    assert f"?v={studio_version}" in resp.text
    assert studio_version == "0.4.0"
