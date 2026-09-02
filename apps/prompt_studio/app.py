"""FastAPI application for Prompt Studio."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from apps.prompt_studio import __version__ as STUDIO_VERSION
from apps.prompt_studio import store as studio_store
from apps.prompt_studio.placeholders import (
    extract_placeholders,
    fill_placeholders,
    reconcile_variables,
    suggest_var_name,
    validate_var_name,
    wrap_selection,
)
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


class PromptUpdateIn(_StrictModel):
    title: str | None = Field(default=None, max_length=120)
    original_user_prompt: str | None = None
    refined_prompt: str | None = None
    variables: dict[str, Any] | None = None
    tags: list[str] | None = None
    tools: list[str] | None = None
    output_format: Literal["chat_text", "json", "excel_download"] | None = None
    enabled: bool | None = None


class MakeVariableIn(_StrictModel):
    field: Literal["original_user_prompt", "refined_prompt"] = "refined_prompt"
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    var_name: str | None = Field(default=None, max_length=40)
    text: str | None = None
    variables: dict[str, Any] | None = None


def create_app() -> FastAPI:
    app = FastAPI(title="Prompt Studio", version="0.2.0")

    def _entry_summary(entry: saved_library.SavedPrompt, favorites: set[str]) -> dict[str, Any]:
        original = entry.original_user_prompt or ""
        preview = original if len(original) <= 160 else original[:157] + "…"
        return {
            "id": entry.id,
            "title": entry.title,
            "original_user_prompt": original,
            "original_preview": preview,
            "tags": entry.tags,
            "tools": entry.tools,
            "output_format": entry.output_format,
            "last_run_at": entry.last_run_at,
            "run_count": entry.run_count,
            "created_at": entry.created_at,
            "enabled": entry.enabled,
            "favorite": entry.id in favorites,
            "placeholder_count": len(extract_placeholders(entry.refined_prompt)),
        }

    def _prompt_detail(entry: saved_library.SavedPrompt, favorites: set[str]) -> dict[str, Any]:
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

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/library_info")
    def library_info() -> dict[str, Any]:
        path = saved_library.saved_prompts_path()
        enabled = saved_library.list_entries(path)
        all_entries = saved_library.list_entries(path, include_disabled=True)
        disabled_count = len(all_entries) - len(enabled)
        last_modified: str | None = None
        if path.is_file():
            last_modified = datetime.fromtimestamp(
                path.stat().st_mtime, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
        config_dir = os.environ.get("CPQ_CONFIG_DIR") or str(path.parent.resolve())
        return {
            "path": str(path.resolve()),
            "config_dir": config_dir,
            "exists": path.is_file(),
            "enabled_count": len(enabled),
            "total_count": len(all_entries),
            "disabled_count": disabled_count,
            "last_modified": last_modified,
            "help": (
                "Prompts appear after MCP save_refined_prompt (or offer-save). "
                "Set AUTO_SAVE_REFINED_PROMPT=true on the active profile and reload MCP "
                "to save automatically."
            ),
        }

    @app.get("/api/prompts")
    def list_prompts(
        q: str | None = Query(default=None),
        tag: str | None = Query(default=None),
        favorites_only: bool = Query(default=False),
        include_disabled: bool = Query(default=False),
        sort: Literal["recent", "title"] = Query(default="recent"),
    ) -> dict[str, Any]:
        favorites = set(studio_store.load_store().get("favorites") or [])
        if q or tag:
            entries = saved_library.search_entries(
                query=q, tag=tag, include_disabled=include_disabled
            )
        else:
            entries = saved_library.list_entries(include_disabled=include_disabled)
        if favorites_only:
            entries = [e for e in entries if e.id in favorites]
        if q and not tag:
            needle = q.strip().lower()
            extra = []
            seen = {e.id for e in entries}
            for e in saved_library.list_entries(include_disabled=include_disabled):
                if e.id in seen:
                    continue
                hay = " ".join(e.tags + e.tools).lower()
                if needle in hay:
                    extra.append(e)
            entries = list(entries) + extra
        entries = saved_library.sort_entries(entries, sort=sort)
        return {
            "count": len(entries),
            "prompts": [_entry_summary(e, favorites) for e in entries],
        }

    @app.get("/api/prompts/download", response_model=None)
    def download_prompts(
        include_disabled: bool = Query(default=True),
    ) -> FileResponse | Response:
        """Download the full saved-prompts library as JSON."""
        path = saved_library.saved_prompts_path()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        filename = f"saved_prompts_{stamp}.json"
        if include_disabled and path.is_file():
            return FileResponse(
                path,
                media_type="application/json",
                filename=filename,
            )
        data = saved_library.load_library(path)
        if not include_disabled:
            data = {
                **data,
                "prompts": [
                    p
                    for p in data.get("prompts", [])
                    if isinstance(p, dict) and p.get("enabled", True)
                ],
            }
        body = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        return Response(
            content=body,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.get("/api/prompts/{prompt_id}")
    def get_prompt(
        prompt_id: str,
        include_disabled: bool = Query(default=True),
    ) -> dict[str, Any]:
        entry = saved_library.get_entry(prompt_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Prompt not found")
        if not entry.enabled and not include_disabled:
            raise HTTPException(status_code=404, detail="Prompt not found")
        favorites = set(studio_store.load_store().get("favorites") or [])
        return _prompt_detail(entry, favorites)

    @app.patch("/api/prompts/{prompt_id}")
    def patch_prompt(prompt_id: str, body: PromptUpdateIn) -> dict[str, Any]:
        payload = body.model_dump(exclude_unset=True)
        if not payload:
            raise HTTPException(status_code=400, detail="No fields to update")
        try:
            entry = saved_library.update_prompt(prompt_id, **payload)
        except saved_library.UpdatePromptError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        favorites = set(studio_store.load_store().get("favorites") or [])
        return _prompt_detail(entry, favorites)

    @app.post("/api/prompts/{prompt_id}/make-variable")
    def make_variable(prompt_id: str, body: MakeVariableIn) -> dict[str, Any]:
        entry = saved_library.get_entry(prompt_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Prompt not found")

        if body.text is not None:
            source_text = body.text
        elif body.field == "original_user_prompt":
            source_text = entry.original_user_prompt
        else:
            source_text = entry.refined_prompt

        if body.end <= body.start or body.end > len(source_text):
            raise HTTPException(status_code=400, detail="Invalid selection range")

        selected = source_text[body.start : body.end]
        if not selected.strip():
            raise HTTPException(status_code=400, detail="Selection is empty")

        existing_names = set(extract_placeholders(entry.refined_prompt))
        existing_names.update((body.variables or entry.variables or {}).keys())
        try:
            var_name = validate_var_name(
                body.var_name or suggest_var_name(selected, existing_names)
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        try:
            updated_text = wrap_selection(source_text, body.start, body.end, var_name)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        variables = dict(body.variables if body.variables is not None else entry.variables)
        if var_name not in variables or not str(variables.get(var_name) or "").strip():
            variables[var_name] = selected.strip()

        result_original = (
            updated_text if body.field == "original_user_prompt" else entry.original_user_prompt
        )
        result_refined = (
            updated_text if body.field == "refined_prompt" else entry.refined_prompt
        )
        reconciled = reconcile_variables(result_refined, variables)
        return {
            "prompt_id": prompt_id,
            "field": body.field,
            "var_name": var_name,
            "selected_text": selected,
            "original_user_prompt": result_original,
            "refined_prompt": result_refined,
            "variables": reconciled,
            "placeholders": extract_placeholders(result_refined),
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

    @app.delete("/api/prompts/{prompt_id}")
    def delete_prompt(prompt_id: str) -> dict[str, bool]:
        if not saved_library.delete_prompt(prompt_id):
            raise HTTPException(status_code=404, detail="Prompt not found")
        studio_store.remove_prompt_references(prompt_id)
        return {"deleted": True}

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
    def index() -> Response:
        html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
        html = html.replace("?v=0.2.0", f"?v={STUDIO_VERSION}")
        return Response(
            content=html,
            media_type="text/html",
            headers={"Cache-Control": "no-cache"},
        )

    @app.get("/static/app.js")
    def studio_app_js() -> FileResponse:
        return FileResponse(
            STATIC_DIR / "app.js",
            media_type="application/javascript",
            headers={"Cache-Control": "no-cache"},
        )

    @app.get("/static/styles.css")
    def studio_styles_css() -> FileResponse:
        return FileResponse(
            STATIC_DIR / "styles.css",
            media_type="text/css",
            headers={"Cache-Control": "no-cache"},
        )

    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    return app


app = create_app()
