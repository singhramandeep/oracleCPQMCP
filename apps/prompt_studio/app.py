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
from apps.prompt_studio import log_viewer
from apps.prompt_studio import profile_config_viewer
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
from oracle_cpq_mcp.prompts.tags import CX_MODULE_TAGS, PRODUCT_TAGS

STATIC_DIR = Path(__file__).resolve().parent / "static"

_CX_MODULE_FILTER = Literal[
    "sales",
    "prm",
    "service",
    "field_service",
    "subscription",
    "incentive_compensation",
]


def _filter_product_module(
    entries: list[Any],
    *,
    product: str | None,
    cx_module: str | None,
) -> list[Any]:
    """AND-filter saved prompts by product (cpq/cx) and CX module slug tags."""
    out = entries
    if product:
        needle = product.strip().lower()
        if needle not in PRODUCT_TAGS:
            return []
        out = [e for e in out if needle in (e.tags or [])]
    if cx_module:
        slug = cx_module.strip().lower()
        if slug not in CX_MODULE_TAGS:
            return []
        out = [e for e in out if slug in (e.tags or [])]
    return out


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FavoriteOut(_StrictModel):
    prompt_id: str
    favorited: bool


class RatingIn(_StrictModel):
    rating: int | None = Field(
        default=None,
        description="Prompt rating 1–10, or null to clear.",
    )


class CommentIn(_StrictModel):
    text: str = Field(min_length=1, max_length=saved_library.MAX_COMMENT_LEN)


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

    def _last_run_summary(entry: saved_library.SavedPrompt) -> dict[str, Any]:
        history = entry.run_history or []
        if not history:
            return {
                "last_source": None,
                "last_duration_ms": None,
            }
        last = history[-1]
        return {
            "last_source": last.get("source"),
            "last_duration_ms": last.get("duration_ms"),
        }

    def _entry_summary(entry: saved_library.SavedPrompt, favorites: set[str]) -> dict[str, Any]:
        original = entry.original_user_prompt or ""
        preview = original if len(original) <= 160 else original[:157] + "…"
        last_run = _last_run_summary(entry)
        stats = entry.stats or saved_library.empty_stats()
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
            "rating": entry.rating,
            "comment_count": len(entry.comments or []),
            "last_source": last_run["last_source"],
            "last_duration_ms": last_run["last_duration_ms"],
            "stats_summary": {
                source: {
                    "count": (stats.get(source) or {}).get("count", 0),
                    "last_duration_ms": (stats.get(source) or {}).get(
                        "last_duration_ms"
                    ),
                    "avg_duration_ms": (stats.get(source) or {}).get("avg_duration_ms"),
                }
                for source in ("cache", "api", "mixed")
            },
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
            "comments": entry.comments,
            "run_history": entry.run_history,
            "stats": entry.stats or saved_library.empty_stats(),
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
        return {"status": "ok", "version": STUDIO_VERSION}

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
            "version": STUDIO_VERSION,
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
            "version": STUDIO_VERSION,
            "sections": [
                {
                    "title": "What is Prompt Studio?",
                    "body": (
                        f"Prompt Studio v{STUDIO_VERSION} is a local UI for browsing, editing, "
                        "rating, and filling saved refined prompts. It does NOT call Oracle CPQ "
                        "and never edits profile passwords. Agents and Studio share the same "
                        "library file. The app version is always shown in the header badge."
                    ),
                },
                {
                    "title": "Library file",
                    "body": (
                        f"All prompts are stored in:\n{path.resolve()}\n\n"
                        "Override with CPQ_SAVED_PROMPTS_PATH. MCP and Studio share this file. "
                        "Header shows the absolute path (click to copy) and live prompt counts."
                    ),
                },
                {
                    "title": "Start / restart / stop",
                    "body": (
                        "From the repo root:\n"
                        f"Start: {cmds.get('start', '')}\n"
                        f"Restart: {cmds.get('restart', '')}\n"
                        f"Or script: {cmds.get('restart_script', '')}\n"
                        f"Stop: {cmds.get('stop', '')}\n\n"
                        f"Open {cmds.get('url', 'http://127.0.0.1:8765')}. "
                        "After upgrades, hard-refresh the browser (Ctrl+F5) so static assets "
                        "match the version badge."
                    ),
                },
                {
                    "title": "Browse: cards, list, filters",
                    "body": (
                        "Toggle Cards / List in the toolbar (persisted). List columns: title, "
                        "rating, format, runs, last run, actions.\n\n"
                        "Filters: search box, sidebar tags, Profile (All / Unscoped / stamped), "
                        "Product (All / CPQ / CX), CX module (Sales / PRM / …), "
                        "Rating (All / Unrated / Rated / 7+ / 8+ / 9+ / 10), Favorites, "
                        "Show disabled. Result count shows when any filter is active. "
                        "Product/CX tags are stamped by save_refined_prompt from tools used."
                    ),
                },
                {
                    "title": "New / Import / Export",
                    "body": (
                        "New prompt creates a row in the library.\n"
                        "Import: upload JSON (library object, array, or single prompt), enter an "
                        "import name/tag, select rows, Import. Tags: imported + import:<slug>. "
                        "Ratings/comments/telemetry are preserved without bumping run counts.\n"
                        "Export all / Export selected download library JSON."
                    ),
                },
                {
                    "title": "Run, edit, and variables",
                    "body": (
                        "Open a prompt to Run (fill {{placeholders}}, Generate + Copy) or Edit "
                        "(title, original, refined template, enabled). Make variable wraps a "
                        "selection as {{snake_case}}. Edit textareas auto-grow with content "
                        "(still vertically resizable; long prompts are capped)."
                    ),
                },
                {
                    "title": "Ratings & run telemetry",
                    "body": (
                        "Rate prompts 1–10 and leave comments in the Run modal. Rating shows on "
                        "cards and in the list Rating column; filter via the Rating toolbar.\n"
                        "After an agent finishes a saved-prompt run, MCP record_prompt_use stores "
                        "elapsed time with source cache|api|mixed. Averages stay separate per source."
                    ),
                },
                {
                    "title": "Suites & favorites",
                    "body": (
                        "Star a prompt for Favorites. Suites are named ordered lists — create from "
                        "the Suites view or Add to suite from a card menu."
                    ),
                },
                {
                    "title": "API logs",
                    "body": (
                        "Open API logs to browse DEBUG_MODE request logs "
                        f"under {log_viewer.logs_dir()}.\n\n"
                        "Files are named {profile}-{environment}.log. "
                        "Enable DEBUG_MODE=true on the active CPQ profile so MCP writes these "
                        "files. Passwords in curl lines are redacted (user:***). Filter by "
                        "method, status, path, and latency; copy curl, blocks, or JSON; "
                        "download the raw file."
                    ),
                },
                {
                    "title": "Profiles & Paths",
                    "body": (
                        "Inspect redacted profile YAML (credentials never shown) and copy "
                        "workspace paths for the library, studio state, logs, local cache, and "
                        "exports. Never edit username/password from Studio — you own credentials."
                    ),
                },
                {
                    "title": "MCP auto-save",
                    "body": (
                        "Agents also save via save_refined_prompt when "
                        "AUTO_SAVE_REFINED_PROMPT=true on the active profile "
                        "(example profiles often default to true). "
                        "ensure_prompt_studio only starts Studio when down — it does not restart "
                        "a live process."
                    ),
                },
            ],
        }

    @app.get("/api/config/profiles")
    def list_config_profiles() -> dict[str, Any]:
        profiles = profile_config_viewer.list_config_profiles()
        return {"count": len(profiles), "profiles": profiles}

    @app.get("/api/config/profiles/example")
    def get_config_profile_example() -> dict[str, Any]:
        try:
            return profile_config_viewer.load_profile_example()
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except profile_config_viewer.ConfigViewerError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/config/profiles/{customer_id}")
    def get_config_profile(customer_id: str) -> dict[str, Any]:
        try:
            return profile_config_viewer.load_redacted_profile(customer_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except profile_config_viewer.ConfigViewerError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/workspace/paths")
    def get_workspace_paths(
        profile: str | None = Query(default=None),
        environment: str | None = Query(default=None),
    ) -> dict[str, Any]:
        try:
            return profile_config_viewer.workspace_paths(
                profile=profile,
                environment=environment,
            )
        except profile_config_viewer.ConfigViewerError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/logs")
    def list_logs() -> dict[str, Any]:
        files = log_viewer.list_log_files()
        return {
            "logs_dir": str(log_viewer.logs_dir().resolve()),
            "files": files,
            "count": len(files),
        }

    @app.get("/api/logs/{name}")
    def get_log(
        name: str,
        q: str | None = Query(default=None),
        method: str | None = Query(default=None),
        status: str | None = Query(default=None),
        path_contains: str | None = Query(default=None),
        min_ms: float | None = Query(default=None, ge=0),
        max_ms: float | None = Query(default=None, ge=0),
        limit: int = Query(default=200, ge=1, le=1000),
        offset: int = Query(default=0, ge=0),
    ) -> dict[str, Any]:
        try:
            return log_viewer.load_log_payload(
                name,
                q=q,
                method=method,
                status=status,
                path_contains=path_contains,
                min_ms=min_ms,
                max_ms=max_ms,
                limit=limit,
                offset=offset,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/logs/{name}/raw", response_model=None)
    def get_log_raw(name: str) -> Response:
        try:
            path = log_viewer.resolve_log_path(name)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return FileResponse(
            path,
            media_type="text/plain; charset=utf-8",
            filename=path.name,
            headers={"Cache-Control": "no-cache"},
        )

    @app.get("/api/prompts")
    def list_prompts(
        q: str | None = Query(default=None),
        tag: str | None = Query(default=None),
        profile: str | None = Query(default=None),
        product: Literal["cpq", "cx"] | None = Query(default=None),
        cx_module: _CX_MODULE_FILTER | None = Query(default=None),
        rating_filter: Literal["unrated", "rated"] | None = Query(default=None),
        min_rating: int | None = Query(default=None, ge=1, le=10),
        favorites_only: bool = Query(default=False),
        include_disabled: bool = Query(default=False),
        sort: Literal["recent", "title"] = Query(default="recent"),
    ) -> dict[str, Any]:
        favorites = set(studio_store.load_store().get("favorites") or [])
        use_search = bool(
            q
            or tag
            or profile
            or product
            or cx_module
            or rating_filter
            or min_rating is not None
        )
        if use_search:
            try:
                entries = saved_library.search_entries(
                    query=q,
                    tag=tag,
                    profile=profile,
                    rating_filter=rating_filter,
                    min_rating=min_rating,
                    include_disabled=include_disabled,
                )
            except saved_library.UpdatePromptError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
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
                if rating_filter or min_rating is not None:
                    try:
                        rating_ok = saved_library.search_entries(
                            rating_filter=rating_filter,
                            min_rating=min_rating,
                            include_disabled=include_disabled,
                        )
                    except saved_library.UpdatePromptError as exc:
                        raise HTTPException(status_code=400, detail=str(exc)) from exc
                    if e.id not in {x.id for x in rating_ok}:
                        continue
                hay = " ".join(e.tags + e.tools).lower()
                if needle in hay:
                    extra.append(e)
            entries = list(entries) + extra
        entries = _filter_product_module(entries, product=product, cx_module=cx_module)
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
            try:
                entry, created = saved_library.import_prompt(
                    raw,
                    extra_tags=batch_tags,
                )
            except saved_library.UpdatePromptError as exc:
                errors.append(f"index {idx}: {exc}")
                continue
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

    @app.patch("/api/prompts/{prompt_id}/rating")
    def patch_prompt_rating(prompt_id: str, body: RatingIn) -> dict[str, Any]:
        try:
            entry = saved_library.set_rating(prompt_id, body.rating)
        except saved_library.UpdatePromptError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if entry is None:
            raise HTTPException(status_code=404, detail="Prompt not found")
        favorites = set(studio_store.load_store().get("favorites") or [])
        return _prompt_detail(entry, favorites)

    @app.post("/api/prompts/{prompt_id}/comments")
    def post_prompt_comment(prompt_id: str, body: CommentIn) -> dict[str, Any]:
        try:
            entry = saved_library.add_comment(prompt_id, body.text)
        except saved_library.UpdatePromptError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if entry is None:
            raise HTTPException(status_code=404, detail="Prompt not found")
        favorites = set(studio_store.load_store().get("favorites") or [])
        return _prompt_detail(entry, favorites)

    @app.patch("/api/prompts/{prompt_id}/comments/{comment_id}")
    def patch_prompt_comment(
        prompt_id: str,
        comment_id: str,
        body: CommentIn,
    ) -> dict[str, Any]:
        try:
            entry = saved_library.update_comment(prompt_id, comment_id, body.text)
        except saved_library.UpdatePromptError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if entry is None:
            raise HTTPException(status_code=404, detail="Prompt not found")
        favorites = set(studio_store.load_store().get("favorites") or [])
        return _prompt_detail(entry, favorites)

    @app.delete("/api/prompts/{prompt_id}/comments/{comment_id}")
    def delete_prompt_comment(prompt_id: str, comment_id: str) -> dict[str, Any]:
        try:
            entry = saved_library.delete_comment(prompt_id, comment_id)
        except saved_library.UpdatePromptError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if entry is None:
            raise HTTPException(status_code=404, detail="Prompt not found")
        favorites = set(studio_store.load_store().get("favorites") or [])
        return _prompt_detail(entry, favorites)

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
