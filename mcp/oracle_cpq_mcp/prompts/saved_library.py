"""Persistent library of saved refined prompts (local JSON file)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oracle_cpq_mcp.core.config import config_dir

LIBRARY_VERSION = 1
DEFAULT_FILENAME = "saved_prompts.json"

_SECRET_KEY_RE = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|credential)",
    re.I,
)


OUTPUT_FORMATS = frozenset({"chat_text", "json", "excel_download"})
DEFAULT_OUTPUT_FORMAT = "chat_text"


@dataclass
class SavedPrompt:
    """One saved refined-prompt entry."""

    id: str
    title: str
    original_user_prompt: str
    refined_prompt: str
    variables: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    created_at: str = ""
    last_run_at: str = ""
    run_count: int = 0
    content_hash: str = ""
    enabled: bool = True
    output_format: str = DEFAULT_OUTPUT_FORMAT

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SavedPrompt:
        # Missing enabled → True (migrate older libraries without rewrite).
        enabled_raw = data.get("enabled", True)
        if isinstance(enabled_raw, str):
            enabled = enabled_raw.strip().lower() in ("1", "true", "yes", "on")
        else:
            enabled = bool(enabled_raw)
        fmt = str(data.get("output_format") or DEFAULT_OUTPUT_FORMAT).strip().lower()
        if fmt not in OUTPUT_FORMATS:
            fmt = DEFAULT_OUTPUT_FORMAT
        return cls(
            id=str(data.get("id") or ""),
            title=str(data.get("title") or ""),
            original_user_prompt=str(data.get("original_user_prompt") or ""),
            refined_prompt=str(data.get("refined_prompt") or ""),
            variables=dict(data.get("variables") or {}),
            tags=list(data.get("tags") or []),
            tools=list(data.get("tools") or []),
            created_at=str(data.get("created_at") or ""),
            last_run_at=str(data.get("last_run_at") or ""),
            run_count=int(data.get("run_count") or 0),
            content_hash=str(data.get("content_hash") or ""),
            enabled=enabled,
            output_format=fmt,
        )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sanitize_variables(variables: dict[str, Any] | None) -> dict[str, Any]:
    """Drop secret-looking keys; stringify remaining values briefly."""
    if not variables:
        return {}
    cleaned: dict[str, Any] = {}
    for key, value in variables.items():
        if _SECRET_KEY_RE.search(str(key)):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            cleaned[str(key)] = value
        else:
            cleaned[str(key)] = str(value)[:500]
    return cleaned


def normalize_output_format(value: str | None) -> str:
    """Return a valid output_format; default chat_text."""
    fmt = (value or DEFAULT_OUTPUT_FORMAT).strip().lower()
    return fmt if fmt in OUTPUT_FORMATS else DEFAULT_OUTPUT_FORMAT


def content_hash_for(
    refined_prompt: str,
    tools: list[str],
    output_format: str = DEFAULT_OUTPUT_FORMAT,
) -> str:
    """Stable hash for dedupe (normalized refined text + sorted tools + format)."""
    normalized = re.sub(r"\s+", " ", (refined_prompt or "").strip().lower())
    fmt = normalize_output_format(output_format)
    payload = normalized + "|" + ",".join(sorted(tools)) + "|" + fmt
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def saved_prompts_path() -> Path:
    """Resolve library path from env or default under .config/."""
    override = os.environ.get("CPQ_SAVED_PROMPTS_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return config_dir() / DEFAULT_FILENAME


def _empty_library() -> dict[str, Any]:
    return {"version": LIBRARY_VERSION, "prompts": []}


def load_library(path: Path | None = None) -> dict[str, Any]:
    """Load library JSON; return empty structure if missing/corrupt."""
    target = path or saved_prompts_path()
    if not target.is_file():
        return _empty_library()
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_library()
    if not isinstance(data, dict):
        return _empty_library()
    prompts = data.get("prompts")
    if not isinstance(prompts, list):
        data["prompts"] = []
    data.setdefault("version", LIBRARY_VERSION)
    return data


def save_library(data: dict[str, Any], path: Path | None = None) -> Path:
    """Write library atomically."""
    target = path or saved_prompts_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    tmp.write_text(payload, encoding="utf-8")
    tmp.replace(target)
    return target


def list_entries(
    path: Path | None = None,
    *,
    include_disabled: bool = False,
) -> list[SavedPrompt]:
    """List saved prompts; by default excludes enabled=false."""
    data = load_library(path)
    entries = [
        SavedPrompt.from_dict(p) for p in data.get("prompts", []) if isinstance(p, dict)
    ]
    if include_disabled:
        return entries
    return [e for e in entries if e.enabled]


def get_entry(prompt_id: str, path: Path | None = None) -> SavedPrompt | None:
    """Load by id, including disabled rows (for admin toggle)."""
    for entry in list_entries(path, include_disabled=True):
        if entry.id == prompt_id:
            return entry
    return None


def find_by_hash(content_hash: str, path: Path | None = None) -> SavedPrompt | None:
    for entry in list_entries(path, include_disabled=True):
        if entry.content_hash == content_hash:
            return entry
    return None


def upsert_prompt(
    *,
    title: str,
    original_user_prompt: str,
    refined_prompt: str,
    variables: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    tools: list[str] | None = None,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    path: Path | None = None,
) -> tuple[SavedPrompt, bool]:
    """Insert or update by content hash. Returns (entry, created).

    New rows are always enabled=True. Dedupe updates do not flip enabled.
    """
    tools_list = list(tools or [])
    tags_list = sorted(set(tags or []))
    variables_clean = sanitize_variables(variables)
    fmt = normalize_output_format(output_format)
    digest = content_hash_for(refined_prompt, tools_list, fmt)
    now = _utc_now()
    data = load_library(path)
    prompts: list[dict[str, Any]] = list(data.get("prompts") or [])

    for idx, raw in enumerate(prompts):
        if not isinstance(raw, dict):
            continue
        existing = SavedPrompt.from_dict(raw)
        existing_hash = existing.content_hash or content_hash_for(
            existing.refined_prompt,
            existing.tools,
            existing.output_format,
        )
        if existing_hash == digest:
            existing.title = title.strip() or existing.title
            existing.original_user_prompt = original_user_prompt or existing.original_user_prompt
            existing.refined_prompt = refined_prompt
            existing.variables = variables_clean
            existing.tags = sorted(set(existing.tags) | set(tags_list))
            existing.tools = tools_list or existing.tools
            existing.output_format = fmt
            existing.content_hash = digest
            existing.last_run_at = now
            existing.run_count = max(existing.run_count, 0) + 1
            if not existing.created_at:
                existing.created_at = now
            # Preserve existing.enabled
            prompts[idx] = existing.to_dict()
            data["prompts"] = prompts
            save_library(data, path)
            return existing, False

    entry = SavedPrompt(
        id=str(uuid.uuid4()),
        title=(title or "Untitled prompt").strip()[:120],
        original_user_prompt=original_user_prompt or "",
        refined_prompt=refined_prompt,
        variables=variables_clean,
        tags=tags_list,
        tools=tools_list,
        created_at=now,
        last_run_at=now,
        run_count=1,
        content_hash=digest,
        enabled=True,
        output_format=fmt,
    )
    prompts.append(entry.to_dict())
    data["prompts"] = prompts
    save_library(data, path)
    return entry, True


def set_enabled(
    prompt_id: str,
    enabled: bool,
    path: Path | None = None,
) -> SavedPrompt | None:
    """Enable or disable a saved prompt by id."""
    data = load_library(path)
    prompts: list[dict[str, Any]] = list(data.get("prompts") or [])
    for idx, raw in enumerate(prompts):
        if not isinstance(raw, dict):
            continue
        if raw.get("id") != prompt_id:
            continue
        entry = SavedPrompt.from_dict(raw)
        entry.enabled = bool(enabled)
        prompts[idx] = entry.to_dict()
        data["prompts"] = prompts
        save_library(data, path)
        return entry
    return None


def record_use(prompt_id: str, path: Path | None = None) -> SavedPrompt | None:
    data = load_library(path)
    prompts: list[dict[str, Any]] = list(data.get("prompts") or [])
    now = _utc_now()
    for idx, raw in enumerate(prompts):
        if not isinstance(raw, dict):
            continue
        if raw.get("id") != prompt_id:
            continue
        entry = SavedPrompt.from_dict(raw)
        entry.last_run_at = now
        entry.run_count = max(entry.run_count, 0) + 1
        prompts[idx] = entry.to_dict()
        data["prompts"] = prompts
        save_library(data, path)
        return entry
    return None


def search_entries(
    *,
    query: str | None = None,
    tag: str | None = None,
    tool_domain: str | None = None,
    tool: str | None = None,
    path: Path | None = None,
    include_disabled: bool = False,
) -> list[SavedPrompt]:
    """Filter saved prompts by title substring, tag, tool name, and/or tool domain."""
    from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG

    results = list_entries(path, include_disabled=include_disabled)
    if query:
        q = query.strip().lower()
        results = [
            e
            for e in results
            if q in e.title.lower()
            or q in e.original_user_prompt.lower()
            or q in e.refined_prompt.lower()
        ]
    if tag:
        t = tag.strip().lower()
        results = [e for e in results if t in {x.lower() for x in e.tags}]
    if tool:
        tool_name = tool.strip().lower()
        results = [e for e in results if tool_name in {x.lower() for x in e.tools}]
    if tool_domain:
        domain = tool_domain.strip().lower()
        filtered: list[SavedPrompt] = []
        for entry in results:
            for tool_name in entry.tools:
                spec = TOOL_CATALOG.get(tool_name)
                if spec and spec.domain == domain:
                    filtered.append(entry)
                    break
                if tool_name.lower() == domain or domain in entry.tags:
                    filtered.append(entry)
                    break
        results = filtered
    return results


def last_used(
    limit: int = 5,
    path: Path | None = None,
    *,
    include_disabled: bool = False,
) -> list[SavedPrompt]:
    entries = list_entries(path, include_disabled=include_disabled)
    entries.sort(key=lambda e: e.last_run_at or e.created_at or "", reverse=True)
    return entries[: max(0, limit)]


def choice_label(entry: SavedPrompt) -> str:
    """Plain-text menu label (no icons): [tags] title."""
    tag_prefix = ",".join(entry.tags[:3]) if entry.tags else "general"
    return f"[{tag_prefix}] {entry.title}"[:120]
