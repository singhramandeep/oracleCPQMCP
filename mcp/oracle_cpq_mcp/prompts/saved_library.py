"""Persistent library of saved refined prompts (local JSON file)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oracle_cpq_mcp.core.config import find_project_root

logger = logging.getLogger(__name__)

LIBRARY_VERSION = 1
DEFAULT_FILENAME = "saved_prompts.json"
DEFAULT_DIRNAME = ".prompts"

_SECRET_KEY_RE = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|credential)",
    re.I,
)


OUTPUT_FORMATS = frozenset({"chat_text", "json", "excel_download"})
DEFAULT_OUTPUT_FORMAT = "chat_text"
# Query/filter token for prompts with no profile stamped.
UNSCOPED_PROFILE_FILTER = "__unscoped__"


def normalize_profile(value: str | None) -> str | None:
    """Return stripped profile name, or None when blank/missing."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def profiles_equal(left: str | None, right: str | None) -> bool:
    """True when both profiles normalize to the same key (None ≡ blank)."""
    return (normalize_profile(left) or "") == (normalize_profile(right) or "")


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
    profile: str | None = None

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
            profile=normalize_profile(data.get("profile")),
        )


class UpdatePromptError(ValueError):
    """Raised when update_prompt validation fails."""


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


def default_saved_prompts_path(project_root: Path | None = None) -> Path:
    """Canonical library path: ``{repo}/.prompts/saved_prompts.json``."""
    root = project_root or find_project_root()
    return (root / DEFAULT_DIRNAME / DEFAULT_FILENAME).resolve()


def is_legacy_config_saved_prompts_path(path: Path) -> bool:
    """True when *path* is the old ``.config/saved_prompts.json`` location."""
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        return False
    return resolved.name == DEFAULT_FILENAME and resolved.parent.name == ".config"


def saved_prompts_path() -> Path:
    """Resolve library path from env or default under ``.prompts/``.

    If ``CPQ_SAVED_PROMPTS_PATH`` points at the legacy
    ``.config/saved_prompts.json`` and the canonical ``.prompts`` file exists,
    prefer ``.prompts`` so Studio/MCP do not split the library.
    """
    canonical = default_saved_prompts_path()
    override = os.environ.get("CPQ_SAVED_PROMPTS_PATH")
    if not override or not str(override).strip():
        return canonical
    candidate = Path(override).expanduser().resolve()
    if is_legacy_config_saved_prompts_path(candidate) and canonical.is_file():
        logger.info(
            "Ignoring legacy CPQ_SAVED_PROMPTS_PATH under .config; using %s",
            canonical,
        )
        return canonical
    return candidate


def pin_saved_prompts_env(
    repo_root: Path,
    env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Return env with ``CPQ_SAVED_PROMPTS_PATH`` pinned to ``.prompts`` when needed.

    Pins when unset or when set to legacy ``.config/saved_prompts.json``.
    Custom non-legacy overrides are preserved.
    """
    out = dict(env) if env is not None else dict(os.environ)
    config = repo_root / ".config"
    out.setdefault("CPQ_CONFIG_DIR", str(config.resolve()))
    canonical = str(default_saved_prompts_path(repo_root))
    current = (out.get("CPQ_SAVED_PROMPTS_PATH") or "").strip()
    if not current or is_legacy_config_saved_prompts_path(Path(current)):
        out["CPQ_SAVED_PROMPTS_PATH"] = canonical
    return out


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
    profile: str | None = None,
    path: Path | None = None,
) -> tuple[SavedPrompt, bool]:
    """Insert or update by content hash + profile. Returns (entry, created).

    New rows are always enabled=True. Dedupe updates do not flip enabled.
    Same content under a different profile creates a separate row.
    """
    tools_list = list(tools or [])
    tags_list = sorted(set(tags or []))
    variables_clean = sanitize_variables(variables)
    fmt = normalize_output_format(output_format)
    profile_norm = normalize_profile(profile)
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
        if existing_hash == digest and profiles_equal(existing.profile, profile_norm):
            existing.title = title.strip() or existing.title
            existing.original_user_prompt = original_user_prompt or existing.original_user_prompt
            existing.refined_prompt = refined_prompt
            existing.variables = variables_clean
            existing.tags = sorted(set(existing.tags) | set(tags_list))
            existing.tools = tools_list or existing.tools
            existing.output_format = fmt
            existing.content_hash = digest
            if profile_norm is not None:
                existing.profile = profile_norm
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
        profile=profile_norm,
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


def _placeholder_names(text: str) -> list[str]:
    """Extract {{snake_case}} names in first-seen order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for match in re.finditer(r"\{\{([a-z][a-z0-9_]*)\}\}", text or ""):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def _reconcile_variables(
    refined_prompt: str,
    variables: dict[str, Any] | None,
) -> dict[str, Any]:
    """Keep hints for placeholders still present; add empty hints for new ones."""
    existing = dict(variables or {})
    return {name: existing.get(name, "") for name in _placeholder_names(refined_prompt)}


def update_prompt(
    prompt_id: str,
    *,
    title: str | None = None,
    original_user_prompt: str | None = None,
    refined_prompt: str | None = None,
    variables: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    tools: list[str] | None = None,
    output_format: str | None = None,
    enabled: bool | None = None,
    profile: str | None = None,
    path: Path | None = None,
) -> SavedPrompt:
    """Update a saved prompt by id (not content-hash dedupe).

    Raises UpdatePromptError if the new content hash collides with another id
    under the same profile.
    """
    data = load_library(path)
    prompts: list[dict[str, Any]] = list(data.get("prompts") or [])
    target_idx: int | None = None
    entry: SavedPrompt | None = None
    for idx, raw in enumerate(prompts):
        if not isinstance(raw, dict):
            continue
        if raw.get("id") == prompt_id:
            target_idx = idx
            entry = SavedPrompt.from_dict(raw)
            break
    if entry is None or target_idx is None:
        raise UpdatePromptError(f"Prompt not found: {prompt_id}")

    if title is not None:
        entry.title = title.strip()[:120] or entry.title
    if original_user_prompt is not None:
        entry.original_user_prompt = original_user_prompt
    if refined_prompt is not None:
        entry.refined_prompt = refined_prompt
    if tags is not None:
        entry.tags = sorted(set(tags))
    if tools is not None:
        entry.tools = list(tools)
    if output_format is not None:
        entry.output_format = normalize_output_format(output_format)
    if enabled is not None:
        entry.enabled = bool(enabled)
    if profile is not None:
        # Empty string clears profile (unscoped).
        entry.profile = normalize_profile(profile)

    if variables is not None:
        entry.variables = sanitize_variables(variables)
    elif refined_prompt is not None:
        entry.variables = sanitize_variables(
            _reconcile_variables(entry.refined_prompt, entry.variables)
        )

    new_hash = content_hash_for(entry.refined_prompt, entry.tools, entry.output_format)
    for raw in prompts:
        if not isinstance(raw, dict):
            continue
        other_id = str(raw.get("id") or "")
        if other_id == prompt_id:
            continue
        other = SavedPrompt.from_dict(raw)
        other_hash = other.content_hash or content_hash_for(
            other.refined_prompt,
            other.tools,
            other.output_format,
        )
        if other_hash == new_hash and profiles_equal(other.profile, entry.profile):
            raise UpdatePromptError(
                "Updated content matches another saved prompt (content hash collision). "
                "Change the refined template or save as a duplicate instead."
            )
    entry.content_hash = new_hash
    prompts[target_idx] = entry.to_dict()
    data["prompts"] = prompts
    save_library(data, path)
    return entry


def sort_entries(
    entries: list[SavedPrompt],
    *,
    sort: str = "recent",
) -> list[SavedPrompt]:
    """Sort prompt entries for display (recent = last_run_at/created_at desc)."""
    if sort == "title":
        return sorted(entries, key=lambda e: e.title.lower())
    return sorted(
        entries,
        key=lambda e: e.last_run_at or e.created_at or "",
        reverse=True,
    )


def delete_prompt(prompt_id: str, path: Path | None = None) -> bool:
    """Permanently remove a prompt by id. Returns True if removed."""
    data = load_library(path)
    prompts: list[dict[str, Any]] = list(data.get("prompts") or [])
    kept = [
        raw
        for raw in prompts
        if not (isinstance(raw, dict) and raw.get("id") == prompt_id)
    ]
    if len(kept) == len(prompts):
        return False
    data["prompts"] = kept
    save_library(data, path)
    return True


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
    profile: str | None = None,
    path: Path | None = None,
    include_disabled: bool = False,
) -> list[SavedPrompt]:
    """Filter saved prompts by title substring, tag, tool, domain, and/or profile."""
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
    if profile is not None and str(profile).strip():
        token = str(profile).strip()
        if token == UNSCOPED_PROFILE_FILTER:
            results = [e for e in results if normalize_profile(e.profile) is None]
        else:
            want = normalize_profile(token)
            results = [
                e for e in results if profiles_equal(e.profile, want)
            ]
    return results


def list_profile_names(
    path: Path | None = None,
    *,
    include_disabled: bool = True,
) -> dict[str, Any]:
    """Distinct profile names plus unscoped count for Studio filter UI."""
    entries = list_entries(path, include_disabled=include_disabled)
    names = sorted(
        {
            normalize_profile(e.profile)
            for e in entries
            if normalize_profile(e.profile)
        }
    )
    unscoped = sum(1 for e in entries if normalize_profile(e.profile) is None)
    return {
        "profiles": names,
        "unscoped_count": unscoped,
        "total": len(entries),
    }


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


def import_batch_slug(label: str) -> str:
    """Sanitize an import batch name into a short tag-safe slug."""
    raw = re.sub(r"[^a-zA-Z0-9]+", "_", (label or "").strip().lower()).strip("_")
    return (raw[:40] or "batch")


def import_batch_tags(label: str) -> list[str]:
    """Tags applied to every prompt imported under *label*."""
    slug = import_batch_slug(label)
    return ["imported", f"import:{slug}"]


def normalize_import_payload(raw: Any) -> list[dict[str, Any]]:
    """Accept library object, prompt array, or single prompt → list of dicts."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [p for p in raw if isinstance(p, dict)]
    if isinstance(raw, dict):
        prompts = raw.get("prompts")
        if isinstance(prompts, list):
            return [p for p in prompts if isinstance(p, dict)]
        # Single prompt object (has refined text or title)
        if raw.get("refined_prompt") is not None or raw.get("title") is not None:
            return [raw]
    raise ValueError(
        "Import JSON must be a library object {prompts: [...]}, a prompt array, "
        "or a single prompt object"
    )


def build_import_candidates(
    raw_prompts: list[dict[str, Any]],
    *,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """Normalize import rows for preview (index, hash, already_in_library)."""
    existing_hashes: set[str] = set()
    for entry in list_entries(path, include_disabled=True):
        digest = entry.content_hash or content_hash_for(
            entry.refined_prompt, entry.tools, entry.output_format
        )
        if digest:
            existing_hashes.add(digest)

    candidates: list[dict[str, Any]] = []
    for idx, raw in enumerate(raw_prompts):
        title = str(raw.get("title") or "Untitled prompt").strip()[:120]
        refined = str(raw.get("refined_prompt") or "")
        tools = [str(t) for t in (raw.get("tools") or []) if str(t).strip()]
        tags = [str(t) for t in (raw.get("tags") or []) if str(t).strip()]
        fmt = normalize_output_format(str(raw.get("output_format") or ""))
        digest = content_hash_for(refined, tools, fmt) if refined.strip() else ""
        preview = refined.strip()
        if len(preview) > 160:
            preview = preview[:157] + "…"
        candidates.append(
            {
                "index": idx,
                "id": str(raw.get("id") or "") or None,
                "title": title or "Untitled prompt",
                "tags": tags,
                "tools": tools,
                "output_format": fmt,
                "refined_preview": preview,
                "content_hash": digest,
                "already_in_library": bool(digest and digest in existing_hashes),
                "empty_refined": not bool(refined.strip()),
            }
        )
    return candidates

