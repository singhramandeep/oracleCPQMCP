"""FastAPI application for Prompt Studio."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from apps.prompt_studio import store as studio_store
from apps.prompt_studio.placeholders import extract_placeholders, fill_placeholders
from oracle_cpq_mcp.prompts import saved_library

STATIC_DIR = Path(__file__).resolve().parent / "static"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FavoriteOut(_StrictModel):
    prompt_id: str
    favorited: bool


class SuiteCreateIn(_StrictModel):
    name: str = Field(min_length=1, max_length=120)


class SuiteUpdateIn(_StrictModel):
    name: str | None = Field(default=None, max_length=120)
    prompt_ids: list[str] | None = None


class SuiteAddPromptIn(_StrictModel):
    prompt_id: str = Field(min_length=1)


class GenerateIn(_StrictModel):
    prompt_id: str = Field(min_length=1)
    values: dict[str, Any] = Field(default_factory=dict)


def create_app() -> FastAPI:
    app = FastAPI(title="Prompt Studio", version="0.1.0")

    def _entry_summary(entry: saved_library.SavedPrompt, favorites: set[str]) -> dict[str, Any]:
        return {
            "id": entry.id,
            "title": entry.title,
            "tags": entry.tags,
            "tools": entry.tools,
            "output_format": entry.output_format,
            "last_run_at": entry.last_run_at,
            "run_count": entry.run_count,
            "created_at": entry.created_at,
            "favorite": entry.id in favorites,
            "placeholder_count": len(extract_placeholders(entry.refined_prompt)),
        }

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/prompts")
    def list_prompts(
        q: str | None = Query(default=None),
        tag: str | None = Query(default=None),
        favorites_only: bool = Query(default=False),
    ) -> dict[str, Any]:
        favorites = set(studio_store.load_store().get("favorites") or [])
        if q or tag:
            entries = saved_library.search_entries(query=q, tag=tag)
        else:
            entries = saved_library.list_entries()
        if favorites_only:
            entries = [e for e in entries if e.id in favorites]
        # Enrich search: also match tags/tools when q is set (search_entries misses tags)
        if q and not tag:
            needle = q.strip().lower()
            extra = []
            seen = {e.id for e in entries}
            for e in saved_library.list_entries():
                if e.id in seen:
                    continue
                hay = " ".join(e.tags + e.tools).lower()
                if needle in hay:
                    extra.append(e)
            entries = list(entries) + extra
        return {
            "count": len(entries),
            "prompts": [_entry_summary(e, favorites) for e in entries],
        }

    @app.get("/api/prompts/{prompt_id}")
    def get_prompt(prompt_id: str) -> dict[str, Any]:
        entry = saved_library.get_entry(prompt_id)
        if entry is None or not entry.enabled:
            raise HTTPException(status_code=404, detail="Prompt not found")
        favorites = set(studio_store.load_store().get("favorites") or [])
        placeholders = extract_placeholders(entry.refined_prompt)
        history = studio_store.get_variable_history()
        return {
            **_entry_summary(entry, favorites),
            "original_user_prompt": entry.original_user_prompt,
            "refined_prompt": entry.refined_prompt,
            "variables": entry.variables,
            "placeholders": placeholders,
            "recent_values": {k: history.get(k, []) for k in placeholders},
        }

    @app.get("/api/tags")
    def list_tags() -> dict[str, Any]:
        counts: dict[str, int] = {}
        for entry in saved_library.list_entries():
            for tag in entry.tags:
                counts[tag] = counts.get(tag, 0) + 1
        tags = [{"tag": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: x[0].lower())]
        return {"tags": tags}

    @app.post("/api/prompts/{prompt_id}/favorite")
    def favorite_prompt(prompt_id: str) -> FavoriteOut:
        entry = saved_library.get_entry(prompt_id)
        if entry is None or not entry.enabled:
            raise HTTPException(status_code=404, detail="Prompt not found")
        favorited = studio_store.toggle_favorite(prompt_id)
        return FavoriteOut(prompt_id=prompt_id, favorited=favorited)

    @app.get("/api/suites")
    def get_suites() -> dict[str, Any]:
        return {"suites": studio_store.list_suites()}

    @app.post("/api/suites")
    def post_suite(body: SuiteCreateIn) -> dict[str, Any]:
        return studio_store.create_suite(body.name)

    @app.get("/api/suites/{suite_id}")
    def get_suite(suite_id: str) -> dict[str, Any]:
        suite = studio_store.get_suite(suite_id)
        if suite is None:
            raise HTTPException(status_code=404, detail="Suite not found")
        favorites = set(studio_store.load_store().get("favorites") or [])
        prompts = []
        for pid in suite.get("prompt_ids") or []:
            entry = saved_library.get_entry(pid)
            if entry and entry.enabled:
                prompts.append(_entry_summary(entry, favorites))
        return {**suite, "prompts": prompts}

    @app.patch("/api/suites/{suite_id}")
    def patch_suite(suite_id: str, body: SuiteUpdateIn) -> dict[str, Any]:
        suite = studio_store.update_suite(
            suite_id,
            name=body.name,
            prompt_ids=body.prompt_ids,
        )
        if suite is None:
            raise HTTPException(status_code=404, detail="Suite not found")
        return suite

    @app.delete("/api/suites/{suite_id}")
    def remove_suite(suite_id: str) -> dict[str, bool]:
        if not studio_store.delete_suite(suite_id):
            raise HTTPException(status_code=404, detail="Suite not found")
        return {"deleted": True}

    @app.post("/api/suites/{suite_id}/prompts")
    def add_to_suite(suite_id: str, body: SuiteAddPromptIn) -> dict[str, Any]:
        entry = saved_library.get_entry(body.prompt_id)
        if entry is None or not entry.enabled:
            raise HTTPException(status_code=404, detail="Prompt not found")
        suite = studio_store.add_prompt_to_suite(suite_id, body.prompt_id)
        if suite is None:
            raise HTTPException(status_code=404, detail="Suite not found")
        return suite

    @app.get("/api/variable-history")
    def variable_history() -> dict[str, Any]:
        return {"variable_history": studio_store.get_variable_history()}

    @app.post("/api/generate")
    def generate(body: GenerateIn) -> dict[str, Any]:
        entry = saved_library.get_entry(body.prompt_id)
        if entry is None or not entry.enabled:
            raise HTTPException(status_code=404, detail="Prompt not found")
        filled = fill_placeholders(entry.refined_prompt, body.values)
        studio_store.append_variable_history(body.values)
        return {
            "prompt_id": entry.id,
            "title": entry.title,
            "filled_text": filled,
            "placeholders": extract_placeholders(entry.refined_prompt),
        }

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return app


app = create_app()
