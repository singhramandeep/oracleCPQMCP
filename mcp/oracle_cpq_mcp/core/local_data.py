"""Local snapshot store under ``data/{customer}/{env}/…`` for full CPQ collections."""

from __future__ import annotations

import io
import json
import logging
import os
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from oracle_cpq_mcp.core.config import CPQProfile, find_project_root

LocalDataDomain = Literal["users", "groups", "bml", "commerce", "datatables"]
LocalDataPolicy = Literal["ask", "prefer", "never"]

logger = logging.getLogger(__name__)

_SAFE_SEGMENT = re.compile(r"[^A-Za-z0-9._-]+")
_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "token",
        "authorization",
        "auth",
        "credential",
        "credentials",
        "api_key",
        "apikey",
        "access_token",
        "refresh_token",
    }
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_segment(value: str, *, fallback: str = "_") -> str:
    """Filesystem-safe single path segment."""
    cleaned = _SAFE_SEGMENT.sub("_", (value or "").strip()).strip("._")
    return cleaned or fallback


def local_data_root() -> Path:
    """Resolve ``CPQ_LOCAL_DATA_DIR`` or ``{repo}/data``."""
    override = os.environ.get("CPQ_LOCAL_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return find_project_root() / "data"


def profile_env_root(profile: CPQProfile) -> Path:
    return local_data_root() / safe_segment(profile.customer_id) / safe_segment(profile.environment)


def domain_dir(
    profile: CPQProfile,
    domain: LocalDataDomain,
    *,
    process_var_name: str | None = None,
    table_name: str | None = None,
) -> Path:
    base = profile_env_root(profile) / domain
    if domain == "commerce":
        if not process_var_name:
            raise ValueError("process_var_name is required for commerce snapshots")
        return base / safe_segment(process_var_name)
    if domain == "datatables":
        if not table_name:
            raise ValueError("table_name is required for datatable snapshots")
        return base / safe_segment(table_name)
    return base


def _atomic_write_bytes(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    return path


def write_bytes(path: Path, data: bytes) -> Path:
    return _atomic_write_bytes(path, data)


def write_text(path: Path, text: str, *, encoding: str = "utf-8") -> Path:
    return _atomic_write_bytes(path, text.encode(encoding))


def write_json(path: Path, payload: Any) -> Path:
    sanitized = sanitize_for_disk(payload)
    text = json.dumps(sanitized, indent=2, ensure_ascii=False, default=str)
    return write_text(path, text + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sanitize_for_disk(value: Any) -> Any:
    """Recursively drop credential-like keys from JSON-serializable payloads."""
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_l = str(key).lower()
            if key_l in _SENSITIVE_KEYS or any(s in key_l for s in ("password", "secret", "token")):
                continue
            out[str(key)] = sanitize_for_disk(item)
        return out
    if isinstance(value, list):
        return [sanitize_for_disk(item) for item in value]
    return value


def write_manifest(
    directory: Path,
    *,
    domain: LocalDataDomain,
    profile: CPQProfile,
    source_tool: str,
    item_count: int,
    paths: dict[str, str],
    filters: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    """Write ``manifest.json`` describing a snapshot directory."""
    relative_paths = {
        key: str(Path(value).name if Path(value).parent == directory else Path(value))
        for key, value in paths.items()
    }
    # Prefer paths relative to the snapshot directory when under it.
    rel: dict[str, str] = {}
    for key, value in paths.items():
        p = Path(value)
        try:
            rel[key] = str(p.resolve().relative_to(directory.resolve())).replace("\\", "/")
        except ValueError:
            rel[key] = str(p)
    manifest: dict[str, Any] = {
        "domain": domain,
        "retrieved_at": utc_now_iso(),
        "source_tool": source_tool,
        "customer_id": profile.customer_id,
        "environment": profile.environment,
        "filters": filters or {},
        "item_count": item_count,
        "paths": rel or relative_paths,
    }
    if extra:
        manifest["extra"] = sanitize_for_disk(extra)
    path = directory / "manifest.json"
    write_json(path, manifest)
    return path


def read_manifest(directory: Path) -> dict[str, Any] | None:
    path = directory / "manifest.json"
    if not path.is_file():
        return None
    data = read_json(path)
    return data if isinstance(data, dict) else None


def is_available(
    profile: CPQProfile,
    domain: LocalDataDomain,
    *,
    process_var_name: str | None = None,
    table_name: str | None = None,
) -> bool:
    try:
        directory = domain_dir(
            profile,
            domain,
            process_var_name=process_var_name,
            table_name=table_name,
        )
    except ValueError:
        return False
    return read_manifest(directory) is not None


def list_snapshots(profile: CPQProfile) -> list[dict[str, Any]]:
    """List manifests under the active profile/env root."""
    root = profile_env_root(profile)
    if not root.is_dir():
        return []
    found: list[dict[str, Any]] = []
    for manifest_path in sorted(root.rglob("manifest.json")):
        try:
            data = read_json(manifest_path)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        entry = dict(data)
        entry["snapshot_dir"] = str(manifest_path.parent)
        entry["manifest_path"] = str(manifest_path)
        found.append(entry)
    return found


def get_snapshot_status(
    profile: CPQProfile,
    domain: LocalDataDomain,
    *,
    process_var_name: str | None = None,
    table_name: str | None = None,
) -> dict[str, Any]:
    try:
        directory = domain_dir(
            profile,
            domain,
            process_var_name=process_var_name,
            table_name=table_name,
        )
    except ValueError as exc:
        return {
            "available": False,
            "domain": domain,
            "message": str(exc),
        }
    manifest = read_manifest(directory)
    if manifest is None:
        return {
            "available": False,
            "domain": domain,
            "snapshot_dir": str(directory),
            "message": "No local snapshot found.",
        }
    return {
        "available": True,
        "domain": domain,
        "snapshot_dir": str(directory),
        "manifest": manifest,
        "local_data_policy": getattr(profile, "local_data_policy", "ask"),
    }


def load_snapshot_summary(
    profile: CPQProfile,
    domain: LocalDataDomain,
    *,
    process_var_name: str | None = None,
    table_name: str | None = None,
    include_payload: bool = False,
    payload_keys: list[str] | None = None,
) -> dict[str, Any]:
    """Return manifest + absolute file paths; optionally include selected JSON payloads."""
    status = get_snapshot_status(
        profile,
        domain,
        process_var_name=process_var_name,
        table_name=table_name,
    )
    if not status.get("available"):
        return status
    directory = Path(str(status["snapshot_dir"]))
    manifest = status["manifest"]
    paths_meta = manifest.get("paths") if isinstance(manifest, dict) else {}
    absolute: dict[str, str] = {}
    if isinstance(paths_meta, dict):
        for key, rel in paths_meta.items():
            candidate = directory / str(rel)
            absolute[str(key)] = str(candidate)
    result: dict[str, Any] = {
        "available": True,
        "domain": domain,
        "snapshot_dir": str(directory),
        "manifest": manifest,
        "files": absolute,
        "note": (
            "Prefer reading files from disk (or open paths) instead of dumping full "
            "payloads into chat. Set include_payload=true only when a small slice is needed."
        ),
    }
    if include_payload and isinstance(paths_meta, dict):
        payloads: dict[str, Any] = {}
        keys = payload_keys or [
            k for k, rel in paths_meta.items() if str(rel).endswith(".json") and k != "manifest"
        ]
        for key in keys:
            rel = paths_meta.get(key)
            if not rel:
                continue
            path = directory / str(rel)
            if path.suffix.lower() != ".json" or not path.is_file():
                continue
            try:
                payloads[str(key)] = read_json(path)
            except (OSError, json.JSONDecodeError) as exc:
                payloads[str(key)] = {"error": f"Failed to read: {exc}"}
        result["payloads"] = payloads
    return result


def persist_users_snapshot(
    profile: CPQProfile,
    users: list[dict[str, Any]],
    xlsx_bytes: bytes,
    *,
    source_tool: str,
    filters: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    directory = domain_dir(profile, "users")
    json_path = directory / "users.json"
    xlsx_path = directory / "users.xlsx"
    write_json(json_path, {"items": users, "count": len(users)})
    write_bytes(xlsx_path, xlsx_bytes)
    manifest_path = write_manifest(
        directory,
        domain="users",
        profile=profile,
        source_tool=source_tool,
        item_count=len(users),
        paths={"users_json": str(json_path), "users_xlsx": str(xlsx_path)},
        filters=filters,
        extra=extra,
    )
    return {
        "snapshot_dir": str(directory),
        "manifest_path": str(manifest_path),
        "item_count": len(users),
        "paths": {"users_json": str(json_path), "users_xlsx": str(xlsx_path)},
    }


def persist_groups_snapshot(
    profile: CPQProfile,
    groups: list[dict[str, Any]],
    xlsx_bytes: bytes,
    *,
    source_tool: str,
    filters: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    directory = domain_dir(profile, "groups")
    json_path = directory / "groups.json"
    xlsx_path = directory / "groups.xlsx"
    write_json(json_path, {"items": groups, "count": len(groups)})
    write_bytes(xlsx_path, xlsx_bytes)
    manifest_path = write_manifest(
        directory,
        domain="groups",
        profile=profile,
        source_tool=source_tool,
        item_count=len(groups),
        paths={"groups_json": str(json_path), "groups_xlsx": str(xlsx_path)},
        filters=filters,
        extra=extra,
    )
    return {
        "snapshot_dir": str(directory),
        "manifest_path": str(manifest_path),
        "item_count": len(groups),
        "paths": {"groups_json": str(json_path), "groups_xlsx": str(xlsx_path)},
    }


def _bml_function_stem(fn: dict[str, Any]) -> tuple[str, str]:
    namespace = fn.get("namespace")
    ns = safe_segment(str(namespace) if namespace else "_root")
    name = fn.get("variableName") or fn.get("name") or fn.get("resourceId") or "function"
    return ns, safe_segment(str(name))


def persist_bml_functions_snapshot(
    profile: CPQProfile,
    functions: list[dict[str, Any]],
    *,
    source_tool: str,
    filters: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    directory = domain_dir(profile, "bml")
    library_path = directory / "library.json"
    write_json(
        library_path,
        {
            "utilLibraryFunctionCount": len(functions),
            "utilLibraryFunctions": functions,
        },
    )
    paths: dict[str, str] = {"library_json": str(library_path)}
    for fn in functions:
        if not isinstance(fn, dict):
            continue
        ns, stem = _bml_function_stem(fn)
        fn_dir = directory / "functions" / ns
        script = fn.get("scriptText")
        bml_path = fn_dir / f"{stem}.bml"
        meta_path = fn_dir / f"{stem}.json"
        if isinstance(script, str):
            write_text(bml_path, script if script.endswith("\n") else script + "\n")
            paths[f"bml:{ns}/{stem}"] = str(bml_path)
        meta = {k: v for k, v in fn.items() if k != "scriptText"}
        write_json(meta_path, meta)
        paths[f"json:{ns}/{stem}"] = str(meta_path)
    # Keep manifest paths compact: library + functions dir marker
    manifest_paths = {
        "library_json": str(library_path),
        "functions_dir": str(directory / "functions"),
    }
    manifest_path = write_manifest(
        directory,
        domain="bml",
        profile=profile,
        source_tool=source_tool,
        item_count=len(functions),
        paths=manifest_paths,
        filters=filters,
        extra={**(extra or {}), "function_file_count": len(functions)},
    )
    return {
        "snapshot_dir": str(directory),
        "manifest_path": str(manifest_path),
        "item_count": len(functions),
        "paths": manifest_paths,
    }


def _safe_zip_member_path(member: str, dest_root: Path) -> Path | None:
    """Return a target path under dest_root, or None if the member is unsafe (zip slip)."""
    name = (member or "").replace("\\", "/").strip()
    if not name or name.endswith("/"):
        return None
    # Drop leading slashes / drive-like prefixes
    while name.startswith("/"):
        name = name[1:]
    parts = [p for p in name.split("/") if p and p != "."]
    if not parts or any(p == ".." for p in parts):
        return None
    if Path(parts[0]).is_absolute() or (len(parts[0]) >= 2 and parts[0][1] == ":"):
        return None
    dest_root = dest_root.resolve()
    target = dest_root.joinpath(*parts).resolve()
    try:
        target.relative_to(dest_root)
    except ValueError:
        return None
    return target


def _extract_zip_bytes(zip_bytes: bytes, dest_root: Path) -> int:
    """Extract zip bytes into dest_root. Returns number of files written."""
    dest_root.mkdir(parents=True, exist_ok=True)
    written = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            target = _safe_zip_member_path(info.filename, dest_root)
            if target is None:
                logger.warning("Skipping unsafe zip member: %s", info.filename)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            written += 1
    return written


def persist_bml_zip_snapshot(
    profile: CPQProfile,
    zip_bytes: bytes,
    *,
    source_tool: str,
    filename: str,
    filters: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    directory = domain_dir(profile, "bml")
    zip_path = directory / safe_segment(filename, fallback="bml_export.zip")
    if not zip_path.suffix:
        zip_path = zip_path.with_suffix(".zip")
    write_bytes(zip_path, zip_bytes)

    site_dir = directory / "site"
    if site_dir.exists():
        shutil.rmtree(site_dir, ignore_errors=True)
    extracted_count = _extract_zip_bytes(zip_bytes, site_dir)

    paths = {"bml_zip": str(zip_path), "site_dir": str(site_dir)}
    manifest_path = write_manifest(
        directory,
        domain="bml",
        profile=profile,
        source_tool=source_tool,
        item_count=extracted_count,
        paths=paths,
        filters=filters,
        extra={
            **(extra or {}),
            "note": (
                "ZIP site export saved and extracted under site/ "
                "(full Commerce BML/BMLT folder tree)."
            ),
            "extracted_file_count": extracted_count,
        },
    )
    return {
        "snapshot_dir": str(directory),
        "manifest_path": str(manifest_path),
        "item_count": extracted_count,
        "paths": paths,
    }


def persist_commerce_collection(
    profile: CPQProfile,
    *,
    process_var_name: str,
    collection_key: str,
    items: list[dict[str, Any]],
    xlsx_bytes: bytes,
    source_tool: str,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    directory = domain_dir(profile, "commerce", process_var_name=process_var_name)
    stem = safe_segment(collection_key)
    json_path = directory / f"{stem}.json"
    xlsx_path = directory / f"{stem}.xlsx"
    write_json(json_path, {"items": items, "count": len(items)})
    write_bytes(xlsx_path, xlsx_bytes)
    # Merge paths into existing manifest if present
    existing = read_manifest(directory) or {}
    paths = dict(existing.get("paths") or {})
    paths[f"{stem}_json"] = str(json_path)
    paths[f"{stem}_xlsx"] = str(xlsx_path)
    # rewrite relative via write_manifest
    abs_paths = {k: (directory / v if not Path(str(v)).is_absolute() else Path(str(v))) for k, v in paths.items()}
    # Prefer absolute current writes
    abs_paths[f"{stem}_json"] = json_path
    abs_paths[f"{stem}_xlsx"] = xlsx_path
    prior_count = int(existing.get("item_count") or 0) if isinstance(existing, dict) else 0
    manifest_path = write_manifest(
        directory,
        domain="commerce",
        profile=profile,
        source_tool=source_tool,
        item_count=prior_count + len(items),
        paths={k: str(v) for k, v in abs_paths.items()},
        filters={**(existing.get("filters") or {}), **(filters or {}), "process_var_name": process_var_name},
        extra={"process_var_name": process_var_name, "last_collection": collection_key},
    )
    return {
        "snapshot_dir": str(directory),
        "manifest_path": str(manifest_path),
        "item_count": len(items),
        "collection": collection_key,
        "paths": {f"{stem}_json": str(json_path), f"{stem}_xlsx": str(xlsx_path)},
    }


def persist_datatable_snapshot(
    profile: CPQProfile,
    *,
    table_name: str,
    meta: dict[str, Any] | None,
    rows: list[dict[str, Any]],
    xlsx_bytes: bytes,
    source_tool: str,
    filters: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    directory = domain_dir(profile, "datatables", table_name=table_name)
    meta_path = directory / "meta.json"
    rows_path = directory / "rows.json"
    xlsx_path = directory / "rows.xlsx"
    write_json(meta_path, meta or {})
    write_json(rows_path, {"items": rows, "count": len(rows)})
    write_bytes(xlsx_path, xlsx_bytes)
    paths = {
        "meta_json": str(meta_path),
        "rows_json": str(rows_path),
        "rows_xlsx": str(xlsx_path),
    }
    manifest_path = write_manifest(
        directory,
        domain="datatables",
        profile=profile,
        source_tool=source_tool,
        item_count=len(rows),
        paths=paths,
        filters={**(filters or {}), "table_name": table_name},
        extra=extra,
    )
    return {
        "snapshot_dir": str(directory),
        "manifest_path": str(manifest_path),
        "item_count": len(rows),
        "paths": paths,
    }


def parse_local_data_policy(value: str | None, *, default: LocalDataPolicy = "ask") -> LocalDataPolicy:
    if value is None or value.strip() == "":
        return default
    normalized = value.strip().lower()
    if normalized in ("ask", "prefer", "never"):
        return normalized  # type: ignore[return-value]
    raise ValueError(
        f"Invalid LOCAL_DATA_POLICY '{value}'. Use ask, prefer, or never."
    )


__all__ = [
    "LocalDataDomain",
    "LocalDataPolicy",
    "domain_dir",
    "get_snapshot_status",
    "is_available",
    "list_snapshots",
    "load_snapshot_summary",
    "local_data_root",
    "parse_local_data_policy",
    "persist_bml_functions_snapshot",
    "persist_bml_zip_snapshot",
    "persist_commerce_collection",
    "persist_datatable_snapshot",
    "persist_groups_snapshot",
    "persist_users_snapshot",
    "profile_env_root",
    "read_manifest",
    "safe_segment",
    "sanitize_for_disk",
    "utc_now_iso",
    "write_bytes",
    "write_json",
    "write_manifest",
    "write_text",
]
