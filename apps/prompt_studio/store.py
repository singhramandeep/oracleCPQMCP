"""Atomic read/write for Prompt Studio sidecar state (.config/prompt_studio.json)."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oracle_cpq_mcp.core.config import config_dir

DEFAULT_FILENAME = "prompt_studio.json"
HISTORY_CAP = 10


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def studio_path() -> Path:
    override = os.environ.get("CPQ_PROMPT_STUDIO_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return config_dir() / DEFAULT_FILENAME


def _empty_store() -> dict[str, Any]:
    return {
        "version": 1,
        "favorites": [],
        "suites": [],
        "variable_history": {},
    }


def load_store(path: Path | None = None) -> dict[str, Any]:
    target = path or studio_path()
    if not target.exists():
        return _empty_store()
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_store()
    if not isinstance(raw, dict):
        return _empty_store()
    store = _empty_store()
    favs = raw.get("favorites") or []
    if isinstance(favs, list):
        store["favorites"] = [str(x) for x in favs if x]
    suites = raw.get("suites") or []
    if isinstance(suites, list):
        cleaned = []
        for s in suites:
            if not isinstance(s, dict) or not s.get("id"):
                continue
            prompt_ids = s.get("prompt_ids") or []
            cleaned.append(
                {
                    "id": str(s["id"]),
                    "name": str(s.get("name") or "Untitled suite")[:120],
                    "prompt_ids": [str(p) for p in prompt_ids if p],
                    "created_at": str(s.get("created_at") or ""),
                    "updated_at": str(s.get("updated_at") or ""),
                }
            )
        store["suites"] = cleaned
    hist = raw.get("variable_history") or {}
    if isinstance(hist, dict):
        cleaned_hist: dict[str, list[str]] = {}
        for key, vals in hist.items():
            if not isinstance(vals, list):
                continue
            cleaned_hist[str(key)] = [str(v) for v in vals if v is not None][:HISTORY_CAP]
        store["variable_history"] = cleaned_hist
    return store


def save_store(data: dict[str, Any], path: Path | None = None) -> Path:
    target = path or studio_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    payload = {
        "version": int(data.get("version") or 1),
        "favorites": list(data.get("favorites") or []),
        "suites": list(data.get("suites") or []),
        "variable_history": dict(data.get("variable_history") or {}),
    }
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(target)
    return target


def is_favorite(prompt_id: str, path: Path | None = None) -> bool:
    store = load_store(path)
    return prompt_id in set(store.get("favorites") or [])


def toggle_favorite(prompt_id: str, path: Path | None = None) -> bool:
    """Toggle favorite; return new favorite state (True = favorited)."""
    store = load_store(path)
    favs: list[str] = list(store.get("favorites") or [])
    if prompt_id in favs:
        favs = [f for f in favs if f != prompt_id]
        favorited = False
    else:
        favs.append(prompt_id)
        favorited = True
    store["favorites"] = favs
    save_store(store, path)
    return favorited


def list_suites(path: Path | None = None) -> list[dict[str, Any]]:
    return list(load_store(path).get("suites") or [])


def get_suite(suite_id: str, path: Path | None = None) -> dict[str, Any] | None:
    for suite in list_suites(path):
        if suite["id"] == suite_id:
            return suite
    return None


def create_suite(name: str, path: Path | None = None) -> dict[str, Any]:
    store = load_store(path)
    now = _utc_now()
    suite = {
        "id": str(uuid.uuid4()),
        "name": (name or "Untitled suite").strip()[:120] or "Untitled suite",
        "prompt_ids": [],
        "created_at": now,
        "updated_at": now,
    }
    suites = list(store.get("suites") or [])
    suites.append(suite)
    store["suites"] = suites
    save_store(store, path)
    return suite


def update_suite(
    suite_id: str,
    *,
    name: str | None = None,
    prompt_ids: list[str] | None = None,
    path: Path | None = None,
) -> dict[str, Any] | None:
    store = load_store(path)
    suites = list(store.get("suites") or [])
    for idx, suite in enumerate(suites):
        if suite.get("id") != suite_id:
            continue
        if name is not None:
            suite["name"] = name.strip()[:120] or suite["name"]
        if prompt_ids is not None:
            suite["prompt_ids"] = [str(p) for p in prompt_ids if p]
        suite["updated_at"] = _utc_now()
        suites[idx] = suite
        store["suites"] = suites
        save_store(store, path)
        return suite
    return None


def delete_suite(suite_id: str, path: Path | None = None) -> bool:
    store = load_store(path)
    suites = list(store.get("suites") or [])
    new_suites = [s for s in suites if s.get("id") != suite_id]
    if len(new_suites) == len(suites):
        return False
    store["suites"] = new_suites
    save_store(store, path)
    return True


def add_prompt_to_suite(
    suite_id: str,
    prompt_id: str,
    path: Path | None = None,
) -> dict[str, Any] | None:
    suite = get_suite(suite_id, path)
    if suite is None:
        return None
    ids = list(suite.get("prompt_ids") or [])
    if prompt_id not in ids:
        ids.append(prompt_id)
    return update_suite(suite_id, prompt_ids=ids, path=path)


def get_variable_history(path: Path | None = None) -> dict[str, list[str]]:
    store = load_store(path)
    hist = store.get("variable_history") or {}
    return {str(k): list(v) for k, v in hist.items() if isinstance(v, list)}


def append_variable_history(
    values: dict[str, Any],
    path: Path | None = None,
) -> dict[str, list[str]]:
    """Prepend non-empty stringified values per key; cap at HISTORY_CAP."""
    store = load_store(path)
    hist: dict[str, list[str]] = dict(store.get("variable_history") or {})
    for key, raw in values.items():
        if raw is None:
            continue
        text = str(raw).strip()
        if not text:
            continue
        key_s = str(key)
        existing = [v for v in hist.get(key_s, []) if v != text]
        hist[key_s] = [text, *existing][:HISTORY_CAP]
    store["variable_history"] = hist
    save_store(store, path)
    return hist
