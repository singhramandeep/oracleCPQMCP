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

LIBRARY_VERSION = 2
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

DATA_SOURCES = frozenset({"cache", "api", "mixed"})
MAX_RUN_HISTORY = 50
MAX_COMMENTS = 100
MAX_COMMENT_LEN = 2000


class UpdatePromptError(ValueError):
    """Raised when update_prompt / rating / run validation fails."""


def empty_source_stats() -> dict[str, Any]:
    """Empty per-source timing bucket (cache/api/mixed stay independent)."""
    return {
        "count": 0,
        "last_duration_ms": None,
        "last_at": "",
        "total_duration_ms": 0,
        "avg_duration_ms": None,
    }


def empty_stats() -> dict[str, Any]:
    return {source: empty_source_stats() for source in ("cache", "api", "mixed")}


def normalize_data_source(value: str | None) -> str:
    """Return cache|api|mixed or raise UpdatePromptError."""
    source = (value or "").strip().lower()
    if source not in DATA_SOURCES:
        raise UpdatePromptError(
            f"source must be one of {sorted(DATA_SOURCES)}; got {value!r}"
        )
    return source


def normalize_rating(value: Any) -> int | None:
    """Validate rating 1–10 or None to clear."""
    if value is None or value == "":
        return None
    try:
        rating = int(value)
    except (TypeError, ValueError) as exc:
        raise UpdatePromptError("rating must be an integer 1–10 or null") from exc
    if rating < 1 or rating > 10:
        raise UpdatePromptError("rating must be between 1 and 10 inclusive")
    return rating


def _normalize_comments(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw[:MAX_COMMENTS]:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        out.append(
            {
                "id": str(item.get("id") or uuid.uuid4()),
                "text": text[:MAX_COMMENT_LEN],
                "created_at": str(item.get("created_at") or ""),
                "updated_at": str(item.get("updated_at") or ""),
            }
        )
    return out


def _normalize_run_history(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw[-MAX_RUN_HISTORY:]:
        if not isinstance(item, dict):
            continue
        try:
            source = normalize_data_source(str(item.get("source") or ""))
        except UpdatePromptError:
            continue
        try:
            duration_ms = int(item.get("duration_ms"))
        except (TypeError, ValueError):
            continue
        if duration_ms < 0:
            continue
        out.append(
            {
                "run_id": str(item.get("run_id") or uuid.uuid4()),
                "duration_ms": duration_ms,
                "source": source,
                "recorded_at": str(item.get("recorded_at") or ""),
                "profile": normalize_profile(item.get("profile")),
                "environment": normalize_profile(item.get("environment")),
            }
        )
    return out


def _normalize_stats(raw: Any) -> dict[str, Any]:
    base = empty_stats()
    if not isinstance(raw, dict):
        return base
    for source in ("cache", "api", "mixed"):
        bucket = raw.get(source)
        if not isinstance(bucket, dict):
            continue
        count = max(0, int(bucket.get("count") or 0))
        total = max(0, int(bucket.get("total_duration_ms") or 0))
        last_ms = bucket.get("last_duration_ms")
        try:
            last_duration = int(last_ms) if last_ms is not None else None
        except (TypeError, ValueError):
            last_duration = None
        avg = float(total) / count if count else None
        # Prefer stored avg when consistent; always recompute from total/count.
        base[source] = {
            "count": count,
            "last_duration_ms": last_duration,
            "last_at": str(bucket.get("last_at") or ""),
            "total_duration_ms": total,
            "avg_duration_ms": avg,
        }
    return base


def _apply_run_to_stats(
    stats: dict[str, Any],
    *,
    duration_ms: int,
    source: str,
    recorded_at: str,
) -> dict[str, Any]:
    """Update one source bucket; never mix cache/api/mixed averages."""
    updated = _normalize_stats(stats)
    bucket = dict(updated[source])
    bucket["count"] = int(bucket["count"]) + 1
    bucket["last_duration_ms"] = int(duration_ms)
    bucket["last_at"] = recorded_at
    bucket["total_duration_ms"] = int(bucket["total_duration_ms"]) + int(duration_ms)
    bucket["avg_duration_ms"] = float(bucket["total_duration_ms"]) / bucket["count"]
    updated[source] = bucket
    return updated


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
    rating: int | None = None
    comments: list[dict[str, Any]] = field(default_factory=list)
    run_history: list[dict[str, Any]] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=empty_stats)

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
        rating_raw = data.get("rating", None)
        try:
            rating = normalize_rating(rating_raw) if rating_raw is not None else None
        except UpdatePromptError:
            rating = None
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
            rating=rating,
            comments=_normalize_comments(data.get("comments")),
            run_history=_normalize_run_history(data.get("run_history")),
            stats=_normalize_stats(data.get("stats")),
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
            if not existing.created_at:
                existing.created_at = now
            # Preserve enabled, rating, comments, run stats — saving is not a run.
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
        last_run_at="",
        run_count=0,
        content_hash=digest,
        enabled=True,
        output_format=fmt,
        profile=profile_norm,
        rating=None,
        comments=[],
        run_history=[],
        stats=empty_stats(),
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


def record_use(
    prompt_id: str,
    *,
    duration_ms: int | None = None,
    source: str | None = None,
    profile: str | None = None,
    environment: str | None = None,
    path: Path | None = None,
) -> SavedPrompt | None:
    """Record a completed prompt execution.

    When *duration_ms* and *source* are provided, update the matching
    cache/api/mixed bucket only (averages are never blended across sources).
    Legacy callers that omit both still bump run_count / last_run_at.
    """
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
        if duration_ms is not None or source is not None:
            if duration_ms is None:
                raise UpdatePromptError("duration_ms is required when source is set")
            if source is None:
                raise UpdatePromptError("source is required when duration_ms is set")
            try:
                duration_int = int(duration_ms)
            except (TypeError, ValueError) as exc:
                raise UpdatePromptError("duration_ms must be an integer") from exc
            if duration_int < 0:
                raise UpdatePromptError("duration_ms must be >= 0")
            source_norm = normalize_data_source(source)
            entry.stats = _apply_run_to_stats(
                entry.stats,
                duration_ms=duration_int,
                source=source_norm,
                recorded_at=now,
            )
            history = list(entry.run_history)
            history.append(
                {
                    "run_id": str(uuid.uuid4()),
                    "duration_ms": duration_int,
                    "source": source_norm,
                    "recorded_at": now,
                    "profile": normalize_profile(profile),
                    "environment": normalize_profile(environment),
                }
            )
            entry.run_history = history[-MAX_RUN_HISTORY:]
        prompts[idx] = entry.to_dict()
        data["prompts"] = prompts
        save_library(data, path)
        return entry
    return None


def set_rating(
    prompt_id: str,
    rating: int | None,
    path: Path | None = None,
) -> SavedPrompt | None:
    """Set or clear the prompt-level 1–10 rating."""
    rating_norm = normalize_rating(rating)
    data = load_library(path)
    prompts: list[dict[str, Any]] = list(data.get("prompts") or [])
    for idx, raw in enumerate(prompts):
        if not isinstance(raw, dict) or raw.get("id") != prompt_id:
            continue
        entry = SavedPrompt.from_dict(raw)
        entry.rating = rating_norm
        prompts[idx] = entry.to_dict()
        data["prompts"] = prompts
        save_library(data, path)
        return entry
    return None


def add_comment(
    prompt_id: str,
    text: str,
    path: Path | None = None,
) -> SavedPrompt | None:
    """Append a prompt-level comment."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise UpdatePromptError("comment text is required")
    if len(cleaned) > MAX_COMMENT_LEN:
        raise UpdatePromptError(f"comment text exceeds {MAX_COMMENT_LEN} characters")
    data = load_library(path)
    prompts: list[dict[str, Any]] = list(data.get("prompts") or [])
    now = _utc_now()
    for idx, raw in enumerate(prompts):
        if not isinstance(raw, dict) or raw.get("id") != prompt_id:
            continue
        entry = SavedPrompt.from_dict(raw)
        comments = list(entry.comments)
        if len(comments) >= MAX_COMMENTS:
            raise UpdatePromptError(f"comment limit ({MAX_COMMENTS}) reached")
        comments.append(
            {
                "id": str(uuid.uuid4()),
                "text": cleaned,
                "created_at": now,
                "updated_at": "",
            }
        )
        entry.comments = comments
        prompts[idx] = entry.to_dict()
        data["prompts"] = prompts
        save_library(data, path)
        return entry
    return None


def update_comment(
    prompt_id: str,
    comment_id: str,
    text: str,
    path: Path | None = None,
) -> SavedPrompt | None:
    cleaned = (text or "").strip()
    if not cleaned:
        raise UpdatePromptError("comment text is required")
    if len(cleaned) > MAX_COMMENT_LEN:
        raise UpdatePromptError(f"comment text exceeds {MAX_COMMENT_LEN} characters")
    data = load_library(path)
    prompts: list[dict[str, Any]] = list(data.get("prompts") or [])
    now = _utc_now()
    for idx, raw in enumerate(prompts):
        if not isinstance(raw, dict) or raw.get("id") != prompt_id:
            continue
        entry = SavedPrompt.from_dict(raw)
        found = False
        comments: list[dict[str, Any]] = []
        for comment in entry.comments:
            if comment.get("id") == comment_id:
                comments.append(
                    {
                        **comment,
                        "text": cleaned,
                        "updated_at": now,
                    }
                )
                found = True
            else:
                comments.append(comment)
        if not found:
            raise UpdatePromptError(f"comment not found: {comment_id}")
        entry.comments = comments
        prompts[idx] = entry.to_dict()
        data["prompts"] = prompts
        save_library(data, path)
        return entry
    return None


def delete_comment(
    prompt_id: str,
    comment_id: str,
    path: Path | None = None,
) -> SavedPrompt | None:
    data = load_library(path)
    prompts: list[dict[str, Any]] = list(data.get("prompts") or [])
    for idx, raw in enumerate(prompts):
        if not isinstance(raw, dict) or raw.get("id") != prompt_id:
            continue
        entry = SavedPrompt.from_dict(raw)
        before = len(entry.comments)
        entry.comments = [c for c in entry.comments if c.get("id") != comment_id]
        if len(entry.comments) == before:
            raise UpdatePromptError(f"comment not found: {comment_id}")
        prompts[idx] = entry.to_dict()
        data["prompts"] = prompts
        save_library(data, path)
        return entry
    return None


def import_prompt(
    raw: dict[str, Any],
    *,
    path: Path | None = None,
    extra_tags: list[str] | None = None,
) -> tuple[SavedPrompt, bool]:
    """Import one prompt dict preserving rating/comments/stats without bumping runs."""
    if not isinstance(raw, dict):
        raise UpdatePromptError("import prompt must be an object")
    refined = str(raw.get("refined_prompt") or "").strip()
    if not refined:
        raise UpdatePromptError("refined_prompt is required")
    tools_list = [str(t) for t in (raw.get("tools") or []) if str(t).strip()]
    tags_list = sorted(
        set(str(t) for t in (raw.get("tags") or []) if str(t).strip())
        | set(extra_tags or [])
    )
    fmt = normalize_output_format(str(raw.get("output_format") or ""))
    profile_norm = normalize_profile(raw.get("profile"))
    digest = content_hash_for(refined, tools_list, fmt)
    now = _utc_now()
    data = load_library(path)
    prompts: list[dict[str, Any]] = list(data.get("prompts") or [])

    imported_rating = None
    if raw.get("rating") is not None:
        imported_rating = normalize_rating(raw.get("rating"))
    imported_comments = _normalize_comments(raw.get("comments"))
    imported_history = _normalize_run_history(raw.get("run_history"))
    imported_stats = _normalize_stats(raw.get("stats"))
    imported_run_count = max(0, int(raw.get("run_count") or 0))
    imported_last_run = str(raw.get("last_run_at") or "")
    imported_created = str(raw.get("created_at") or now)

    for idx, existing_raw in enumerate(prompts):
        if not isinstance(existing_raw, dict):
            continue
        existing = SavedPrompt.from_dict(existing_raw)
        existing_hash = existing.content_hash or content_hash_for(
            existing.refined_prompt,
            existing.tools,
            existing.output_format,
        )
        if existing_hash == digest and profiles_equal(existing.profile, profile_norm):
            existing.title = str(raw.get("title") or existing.title).strip()[:120] or existing.title
            existing.original_user_prompt = str(
                raw.get("original_user_prompt") or existing.original_user_prompt
            )
            existing.refined_prompt = refined
            existing.variables = sanitize_variables(
                raw.get("variables") if isinstance(raw.get("variables"), dict) else existing.variables
            )
            existing.tags = sorted(set(existing.tags) | set(tags_list))
            existing.tools = tools_list or existing.tools
            existing.output_format = fmt
            existing.content_hash = digest
            if profile_norm is not None:
                existing.profile = profile_norm
            # Preserve imported engagement/telemetry without bumping runs.
            if imported_rating is not None:
                existing.rating = imported_rating
            if imported_comments:
                existing.comments = imported_comments
            if imported_history:
                existing.run_history = imported_history
            if any(imported_stats[s]["count"] for s in imported_stats):
                existing.stats = imported_stats
                existing.run_count = imported_run_count
                existing.last_run_at = imported_last_run or existing.last_run_at
            prompts[idx] = existing.to_dict()
            data["prompts"] = prompts
            save_library(data, path)
            return existing, False

    entry = SavedPrompt(
        id=str(raw.get("id") or uuid.uuid4()),
        title=str(raw.get("title") or "Untitled prompt").strip()[:120] or "Untitled prompt",
        original_user_prompt=str(raw.get("original_user_prompt") or ""),
        refined_prompt=refined,
        variables=sanitize_variables(
            raw.get("variables") if isinstance(raw.get("variables"), dict) else None
        ),
        tags=tags_list,
        tools=tools_list,
        created_at=imported_created,
        last_run_at=imported_last_run,
        run_count=imported_run_count,
        content_hash=digest,
        enabled=bool(raw.get("enabled", True)),
        output_format=fmt,
        profile=profile_norm,
        rating=imported_rating,
        comments=imported_comments,
        run_history=imported_history,
        stats=imported_stats,
    )
    # Avoid id collisions with an unrelated row.
    if any(isinstance(p, dict) and p.get("id") == entry.id for p in prompts):
        entry.id = str(uuid.uuid4())
    prompts.append(entry.to_dict())
    data["prompts"] = prompts
    save_library(data, path)
    return entry, True


def search_entries(
    *,
    query: str | None = None,
    tag: str | None = None,
    tool_domain: str | None = None,
    tool: str | None = None,
    profile: str | None = None,
    rating_filter: str | None = None,
    min_rating: int | None = None,
    path: Path | None = None,
    include_disabled: bool = False,
) -> list[SavedPrompt]:
    """Filter saved prompts by title substring, tag, tool, domain, profile, and/or rating."""
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
    rf = (rating_filter or "").strip().lower() or None
    if rf == "unrated":
        results = [e for e in results if e.rating is None]
    elif rf == "rated":
        results = [e for e in results if e.rating is not None]
    elif rf is not None:
        raise UpdatePromptError("rating_filter must be 'unrated', 'rated', or omitted")
    if min_rating is not None:
        try:
            floor = int(min_rating)
        except (TypeError, ValueError) as exc:
            raise UpdatePromptError("min_rating must be an integer 1–10") from exc
        if floor < 1 or floor > 10:
            raise UpdatePromptError("min_rating must be between 1 and 10 inclusive")
        results = [
            e for e in results if e.rating is not None and e.rating >= floor
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

