"""FastAPI application for Prompt Studio."""

from __future__ import annotations

import json
import os
import re
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
from oracle_cpq_mcp.core.prompt_studio_process import activation_commands
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


class PromptCreateIn(_StrictModel):
    title: str = Field(min_length=1, max_length=120)
    original_user_prompt: str = ""
    refined_prompt: str = Field(min_length=1)
    variables: dict[str, Any] | None = None
    tags: list[str] | None = None
    tools: list[str] | None = None
    output_format: Literal["chat_text", "json", "excel_download"] | None = None
    profile: str | None = Field(
        default=None,
        max_length=80,
        description="Optional CPQ customer profile stamp (blank = unscoped).",
    )


class PromptUpdateIn(_StrictModel):
    title: str | None = Field(default=None, max_length=120)
    original_user_prompt: str | None = None
    refined_prompt: str | None = None
    variables: dict[str, Any] | None = None
    tags: list[str] | None = None
    tools: list[str] | None = None
    output_format: Literal["chat_text", "json", "excel_download"] | None = None
    enabled: bool | None = None
    profile: str | None = Field(default=None, max_length=80)


class MakeVariableIn(_StrictModel):
    field: Literal["original_user_prompt", "refined_prompt"] = "refined_prompt"
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    var_name: str | None = Field(default=None, max_length=40)
    text: str | None = None
    variables: dict[str, Any] | None = None


class ImportPreviewIn(_StrictModel):
    """JSON payload already parsed by the client (or raw dump)."""

    data: Any = None
    raw_text: str | None = None


class ImportApplyIn(_StrictModel):
    import_label: str = Field(min_length=1, max_length=80)
    indices: list[int] = Field(default_factory=list)
    prompts: list[dict[str, Any]] = Field(default_factory=list)


class ExportSelectedIn(_StrictModel):
    ids: list[str] = Field(min_length=1)


def create_app() -> FastAPI:
    app = FastAPI(title="Prompt Studio", version=STUDIO_VERSION)

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
            "profile": entry.profile,
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

    def _studio_commands() -> dict[str, str]:
        cmds = activation_commands()
        restart = cmds.get("restart") or "python -m apps.prompt_studio restart"
        return {
            "start": cmds.get("powershell") or cmds.get("module") or "",
            "start_unix": cmds.get("unix") or "",
            "restart": restart,
            "restart_script": cmds.get("restart_script") or "",
            "stop": restart.replace(" restart", " stop"),
            "module": cmds.get("module") or "python -m apps.prompt_studio",
            "url": cmds.get("url") or "http://127.0.0.1:8765",
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
        if path.parent.name == ".prompts":
            config_dir = str((path.parent.parent / ".config").resolve())
        else:
            config_dir = os.environ.get("CPQ_CONFIG_DIR") or str(path.parent.resolve())
        return {
            "path": str(path.resolve()),
            "config_dir": config_dir,
            "exists": path.is_file(),
            "enabled_count": len(enabled),
            "total_count": len(all_entries),
            "disabled_count": disabled_count,
            "last_modified": last_modified,
            "commands": _studio_commands(),
            "help": (
                "Prompts live in the library file shown in the header. "
                "They appear after MCP save_refined_prompt / offer-save, "
                "or via New / Import in Prompt Studio. "
                "Set AUTO_SAVE_REFINED_PROMPT=true on the active profile to auto-save."
            ),
        }

    @app.get("/api/help")
    def help_info() -> dict[str, Any]:
        path = saved_library.saved_prompts_path()
        cmds = _studio_commands()
        return {
            "library_path": str(path.resolve()),
            "commands": cmds,
            "sections": [
                {
                    "title": "Library file",
                    "body": (
                        f"All prompts are stored in:\n{path.resolve()}\n\n"
                        "Override with CPQ_SAVED_PROMPTS_PATH. MCP and Studio share this file."
                    ),
                },
                {
                    "title": "Start Prompt Studio",
                    "body": (
                        "From the repo root:\n"
                        f"{cmds.get('start', '')}\n\n"
                        f"Then open {cmds.get('url', 'http://127.0.0.1:8765')}."
                    ),
                },
                {
                    "title": "Restart Prompt Studio",
                    "body": (
                        "One command (stops port listeners, then starts):\n"
                        f"{cmds.get('restart', '')}\n\n"
                        f"Or: {cmds.get('restart_script', '')}\n\n"
                        f"Stop only: {cmds.get('stop', '')}"
                    ),
                },
                {
                    "title": "Import prompts",
                    "body": (
                        "Use Import in the toolbar. Choose a JSON file exported from this "
                        "app (library object, prompt array, or single prompt). Enter an "
                        "import name/tag, select which prompts to import, then Import. "
                        "Each imported prompt is tagged imported and import:<slug>."
                    ),
                },
                {
                    "title": "Export prompts",
                    "body": (
                        "Export all downloads the full library JSON. "
                        "Select prompts with checkboxes and use Export selected for a subset."
                    ),
                },
                {
                    "title": "New prompt / MCP auto-save",
                    "body": (
                        "New prompt creates a row directly in the library. "
                        "Agents also save via save_refined_prompt when "
                        "AUTO_SAVE_REFINED_PROMPT=true on the active profile "
                        "(example profiles default to true)."
                    ),
                },
            ],
        }

    @app.get("/api/prompts")
    def list_prompts(
        q: str | None = Query(default=None),
        tag: str | None = Query(default=None),
        profile: str | None = Query(default=None),
        favorites_only: bool = Query(default=False),
        include_disabled: bool = Query(default=False),
        sort: Literal["recent", "title"] = Query(default="recent"),
    ) -> dict[str, Any]:
        favorites = set(studio_store.load_store().get("favorites") or [])
        if q or tag or profile:
            entries = saved_library.search_entries(
                query=q,
                tag=tag,
                profile=profile,
                include_disabled=include_disabled,
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
                if profile:
                    filtered = saved_library.search_entries(
                        profile=profile,
                        include_disabled=include_disabled,
                    )
                    allowed = {x.id for x in filtered}
                    if e.id not in allowed:
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

    @app.get("/api/profiles")
    def list_profiles() -> dict[str, Any]:
        return saved_library.list_profile_names(include_disabled=True)

    @app.post("/api/prompts")
    def create_prompt(body: PromptCreateIn) -> dict[str, Any]:
        if not body.refined_prompt.strip():
            raise HTTPException(status_code=400, detail="refined_prompt is required")
        entry, created = saved_library.upsert_prompt(
            title=body.title,
            original_user_prompt=body.original_user_prompt or "",
            refined_prompt=body.refined_prompt,
            variables=body.variables,
            tags=body.tags,
            tools=body.tools,
            output_format=body.output_format or saved_library.DEFAULT_OUTPUT_FORMAT,
            profile=body.profile,
        )
        favorites = set(studio_store.load_store().get("favorites") or [])
        detail = _prompt_detail(entry, favorites)
        detail["created"] = created
        return detail

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

    @app.post("/api/prompts/export", response_model=None)
    def export_selected(body: ExportSelectedIn) -> Response:
        ids = [i.strip() for i in body.ids if i and str(i).strip()]
        if not ids:
            raise HTTPException(status_code=400, detail="ids must be non-empty")
        wanted = set(ids)
        prompts: list[dict[str, Any]] = []
        for entry in saved_library.list_entries(include_disabled=True):
            if entry.id in wanted:
                prompts.append(entry.to_dict())
        if not prompts:
            raise HTTPException(status_code=404, detail="No matching prompts to export")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        payload = {
            "version": saved_library.LIBRARY_VERSION,
            "exported_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            "prompts": prompts,
        }
        filename = f"saved_prompts_selected_{stamp}.json"
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        return Response(
            content=text,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.post("/api/prompts/import/preview")
    def import_preview(body: ImportPreviewIn) -> dict[str, Any]:
        raw: Any = body.data
        if raw is None and body.raw_text:
            try:
                raw = json.loads(body.raw_text)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=400, detail=f"Invalid JSON: {exc}"
                ) from exc
        if raw is None:
            raise HTTPException(status_code=400, detail="Provide data or raw_text")
        try:
            prompts = saved_library.normalize_import_payload(raw)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        candidates = saved_library.build_import_candidates(prompts)
        return {
            "count": len(candidates),
            "candidates": candidates,
            "prompts": prompts,
        }

    @app.post("/api/prompts/import")
    def import_apply(body: ImportApplyIn) -> dict[str, Any]:
        label = body.import_label.strip()
        if not label:
            raise HTTPException(status_code=400, detail="import_label is required")
        if not body.prompts:
            raise HTTPException(status_code=400, detail="prompts is required")
        if not body.indices:
            raise HTTPException(status_code=400, detail="Select at least one prompt")

        batch_tags = saved_library.import_batch_tags(label)
        slug = saved_library.import_batch_slug(label)
        imported = 0
        updated = 0
        skipped_empty = 0
        errors: list[str] = []
        results: list[dict[str, Any]] = []

        for idx in body.indices:
            if idx < 0 or idx >= len(body.prompts):
                errors.append(f"index {idx} out of range")
                continue
            raw = body.prompts[idx]
            if not isinstance(raw, dict):
                errors.append(f"index {idx}: not an object")
                continue
            refined = str(raw.get("refined_prompt") or "").strip()
            if not refined:
                skipped_empty += 1
                continue
            title = str(raw.get("title") or "Untitled prompt").strip()[:120]
            tags = [str(t) for t in (raw.get("tags") or []) if str(t).strip()]
            tags = sorted(set(tags) | set(batch_tags))
            tools = [str(t) for t in (raw.get("tools") or []) if str(t).strip()]
            try:
                entry, created = saved_library.upsert_prompt(
                    title=title or "Untitled prompt",
                    original_user_prompt=str(raw.get("original_user_prompt") or ""),
                    refined_prompt=refined,
                    variables=raw.get("variables")
                    if isinstance(raw.get("variables"), dict)
                    else None,
                    tags=tags,
                    tools=tools,
                    output_format=str(
                        raw.get("output_format") or saved_library.DEFAULT_OUTPUT_FORMAT
                    ),
                    profile=raw.get("profile")
                    if isinstance(raw.get("profile"), str) or raw.get("profile") is None
                    else str(raw.get("profile")),
                )
            except Exception as exc:  # noqa: BLE001 — report per-row
                errors.append(f"index {idx}: {exc}")
                continue
            if created:
                imported += 1
                status = "imported"
            else:
                updated += 1
                status = "updated"
            results.append(
                {"index": idx, "id": entry.id, "title": entry.title, "status": status}
            )

        return {
            "import_label": label,
            "import_slug": slug,
            "import_tags": batch_tags,
            "imported": imported,
            "updated": updated,
            "skipped_duplicate": 0,
            "skipped_empty": skipped_empty,
            "errors": errors,
            "results": results,
        }

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
        tags = [
            {"tag": k, "count": v}
            for k, v in sorted(counts.items(), key=lambda x: x[0].lower())
        ]
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
        html = re.sub(r"\?v=\d+\.\d+\.\d+", f"?v={STUDIO_VERSION}", html)
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
