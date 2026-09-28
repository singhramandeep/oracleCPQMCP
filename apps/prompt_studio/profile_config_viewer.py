"""Read-only, redacted profile YAML and workspace path maps for Prompt Studio."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from oracle_cpq_mcp.core.catalog import catalog_path
from oracle_cpq_mcp.core.config import config_dir, find_project_root, profile_yaml_path
from oracle_cpq_mcp.core.debug_api_log import debug_log_dir
from oracle_cpq_mcp.core.local_data import local_data_root
from oracle_cpq_mcp.prompts import saved_library

from apps.prompt_studio import store as studio_store

try:
    import yaml
except ImportError:  # pragma: no cover - exercised when PyYAML missing
    yaml = None  # type: ignore[assignment]

MAX_YAML_BYTES = 512 * 1024  # 512 KiB
REDACTED = "[REDACTED]"
_SECRET_KEY_RE = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|credential)",
    re.I,
)
_SAFE_CUSTOMER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_EXAMPLE_NAME = "example.yaml"
_BLOCKED_STEMS = frozenset(
    {
        "prompt_studio",
        ".catalog",
        ".env",
        ".profile",
        "example",
    }
)


class ConfigViewerError(ValueError):
    """Invalid profile id or unsafe path request."""


def _path_info(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    exists = resolved.exists()
    is_dir = resolved.is_dir() if exists else False
    is_file = resolved.is_file() if exists else False
    return {
        "path": str(resolved),
        "exists": exists,
        "is_dir": is_dir,
        "is_file": is_file,
    }


def validate_customer_id(customer_id: str) -> str:
    """Reject path traversal / invalid profile ids."""
    raw = (customer_id or "").strip()
    if not raw or raw != Path(raw).name:
        raise ConfigViewerError("Invalid profile id")
    if ".." in raw or "/" in raw or "\\" in raw:
        raise ConfigViewerError("Invalid profile id")
    if not _SAFE_CUSTOMER_ID_RE.match(raw):
        raise ConfigViewerError("Invalid profile id")
    if raw.lower().startswith(".") or raw in _BLOCKED_STEMS:
        raise ConfigViewerError("Invalid profile id")
    return raw


def redact_value(key: str, value: Any) -> Any:
    """Recursively redact secret-looking keys; leave structure intact."""
    if isinstance(value, dict):
        return {str(k): redact_value(str(k), v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(key, item) for item in value]
    if _SECRET_KEY_RE.search(key):
        if value is None or value == "":
            return value
        return REDACTED
    return value


def redact_document(document: Any) -> Any:
    if not isinstance(document, dict):
        return document
    return redact_value("", document)


def dump_redacted_yaml(document: Any) -> str:
    if yaml is None:
        raise ConfigViewerError(
            "PyYAML is required to view profile YAML. "
            "Install with: pip install 'PyYAML>=6.0.0'"
        )
    return yaml.safe_dump(
        document,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )


def _resolve_under_config(path: Path) -> Path:
    root = config_dir().resolve()
    target = path.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ConfigViewerError("Path escapes config directory") from exc
    return target


def list_config_profiles() -> list[dict[str, Any]]:
    """List allowlisted customer profile YAML files under ``.config/``."""
    root = config_dir()
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.yaml")):
        stem = path.stem
        if stem.startswith(".") or stem in _BLOCKED_STEMS:
            continue
        if path.name.endswith(".example"):
            continue
        try:
            customer_id = validate_customer_id(stem)
        except ConfigViewerError:
            continue
        try:
            st = path.stat()
        except OSError:
            continue
        catalog = catalog_path(customer_id)
        rows.append(
            {
                "customer_id": customer_id,
                "filename": path.name,
                "kind": "yaml",
                "size_bytes": st.st_size,
                "has_catalog": catalog.is_file(),
                "catalog_filename": catalog.name if catalog.is_file() else None,
            }
        )
    return rows


def load_redacted_profile(customer_id: str) -> dict[str, Any]:
    """Load and redact one allowlisted profile YAML (never ``.env``)."""
    cid = validate_customer_id(customer_id)
    path = _resolve_under_config(profile_yaml_path(cid))
    if not path.is_file():
        raise FileNotFoundError(f"Profile YAML not found: {cid}.yaml")
    size = path.stat().st_size
    if size > MAX_YAML_BYTES:
        raise ConfigViewerError(
            f"Profile YAML exceeds {MAX_YAML_BYTES} bytes (refusing to load)"
        )
    text = path.read_text(encoding="utf-8")
    if yaml is None:
        raise ConfigViewerError(
            "PyYAML is required to view profile YAML. "
            "Install with: pip install 'PyYAML>=6.0.0'"
        )
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigViewerError(f"Invalid YAML: {exc}") from exc
    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        raise ConfigViewerError("Profile YAML must be a mapping at the root")
    document = redact_document(loaded)
    catalog = catalog_path(cid)
    catalog_payload: dict[str, Any] | None = None
    if catalog.is_file() and catalog.stat().st_size <= MAX_YAML_BYTES:
        try:
            cat_raw = yaml.safe_load(catalog.read_text(encoding="utf-8"))
            if isinstance(cat_raw, dict):
                catalog_payload = {
                    "filename": catalog.name,
                    "document": redact_document(cat_raw),
                    "yaml_redacted": dump_redacted_yaml(redact_document(cat_raw)),
                }
        except (OSError, yaml.YAMLError):
            catalog_payload = None

    example_path = config_dir() / _EXAMPLE_NAME
    return {
        "customer_id": cid,
        "kind": "yaml",
        "filename": path.name,
        "path": str(path),
        "size_bytes": size,
        "document": document,
        "yaml_redacted": dump_redacted_yaml(document),
        "catalog": catalog_payload,
        "example_available": example_path.is_file(),
        "read_only": True,
        "secrets_redacted": True,
    }


def load_profile_example() -> dict[str, Any]:
    """Return the committed ``example.yaml`` (redacted for consistency)."""
    path = _resolve_under_config(config_dir() / _EXAMPLE_NAME)
    if not path.is_file():
        raise FileNotFoundError(_EXAMPLE_NAME)
    if path.stat().st_size > MAX_YAML_BYTES:
        raise ConfigViewerError("Example profile YAML is too large")
    if yaml is None:
        raise ConfigViewerError(
            "PyYAML is required to view profile YAML. "
            "Install with: pip install 'PyYAML>=6.0.0'"
        )
    loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ConfigViewerError("Example profile YAML must be a mapping")
    document = redact_document(loaded)
    return {
        "customer_id": None,
        "kind": "example",
        "filename": path.name,
        "path": str(path),
        "document": document,
        "yaml_redacted": dump_redacted_yaml(document),
        "read_only": True,
        "secrets_redacted": True,
    }


def workspace_paths(
    *,
    profile: str | None = None,
    environment: str | None = None,
) -> dict[str, Any]:
    """Return copyable path map for profile/env resource locations."""
    cid = (profile or "").strip() or None
    env = (environment or "").strip() or None
    if cid:
        cid = validate_customer_id(cid)
    if env and env not in {"dev", "test", "prod"}:
        raise ConfigViewerError("environment must be dev, test, or prod")

    yaml_path = profile_yaml_path(cid) if cid else config_dir() / "(select a profile).yaml"
    data_root = local_data_root()
    if cid and env:
        local_root = data_root / cid / env
        exports = local_root / "exports"
        debug_log = debug_log_dir() / f"{cid}-{env}.log"
    elif cid:
        local_root = data_root / cid
        exports = local_root
        debug_log = debug_log_dir() / f"{cid}-*.log"
    else:
        local_root = data_root
        exports = data_root
        debug_log = debug_log_dir()

    paths = {
        "profile_yaml": _path_info(yaml_path) if cid else {
            "path": str(yaml_path),
            "exists": False,
            "is_dir": False,
            "is_file": False,
        },
        "saved_prompts": _path_info(saved_library.saved_prompts_path()),
        "studio_state": _path_info(studio_store.studio_path()),
        "logs_dir": _path_info(debug_log_dir()),
        "debug_log": _path_info(debug_log) if cid and env else {
            "path": str(debug_log),
            "exists": False,
            "is_dir": False,
            "is_file": False,
        },
        "local_data_root": _path_info(local_root if cid else data_root),
        "exports_dir": _path_info(exports),
        "project_root": _path_info(find_project_root()),
        "config_dir": _path_info(config_dir()),
        "example_profile_yaml": _path_info(config_dir() / _EXAMPLE_NAME),
    }
    if cid:
        cat = catalog_path(cid)
        paths["catalog_yaml"] = _path_info(cat)

    return {
        "profile": cid,
        "environment": env,
        "paths": paths,
    }
