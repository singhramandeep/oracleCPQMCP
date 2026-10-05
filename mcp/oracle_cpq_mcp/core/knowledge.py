"""Load shared and customer knowledge markdown for MCP instructions."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oracle_cpq_mcp.core.config import CPQProfile, find_project_root

logger = logging.getLogger(__name__)

BASE_KNOWLEDGE_FILENAME = "CPQBaseKnowledge.md"

# Append limits (chars / bytes of UTF-8 text).
MAX_ENTRY_BODY_CHARS = 8_000
MAX_KNOWLEDGE_FILE_BYTES = 256_000

_SECRET_PATTERNS = (
    re.compile(r"password\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"passwd\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"oauth_client_secret\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"oauth_client_id\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"\boauth_[a-z0-9_]+\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-]{8,}", re.IGNORECASE),
    re.compile(r"Basic\s+[A-Za-z0-9+/=]{8,}", re.IGNORECASE),
    re.compile(r"DEV_PASSWORD\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"TEST_PASSWORD\s*[=:]\s*\S+", re.IGNORECASE),
    re.compile(r"PROD_PASSWORD\s*[=:]\s*\S+", re.IGNORECASE),
)


class KnowledgeError(ValueError):
    """Raised for knowledge path / content validation failures."""

    def __init__(self, message: str, *, code: str = "VALIDATION_ERROR") -> None:
        super().__init__(message)
        self.code = code


def knowledge_dir(project_root: Path | None = None) -> Path:
    """Return the repo `knowledge/` directory."""
    root = project_root or find_project_root()
    return root / "knowledge"


def load_base_knowledge(project_root: Path | None = None) -> str:
    """Load shared CPQBaseKnowledge.md; return empty string if missing."""
    path = knowledge_dir(project_root) / BASE_KNOWLEDGE_FILENAME
    if not path.is_file():
        logger.warning("Shared knowledge file not found: %s", path)
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_customer_knowledge(
    customer_knowledge_file: str | None,
    *,
    project_root: Path | None = None,
) -> str:
    """Load knowledge/{CUSTOMER_KNOWLEDGE_FILE}; warn and return '' if missing."""
    if not customer_knowledge_file:
        return ""
    try:
        path = resolve_knowledge_basename(
            customer_knowledge_file, project_root=project_root
        )
    except KnowledgeError as exc:
        logger.warning("%s", exc)
        return ""

    if not path.is_file():
        logger.warning("Customer knowledge file not found (skipping): %s", path)
        return ""
    return path.read_text(encoding="utf-8").strip()


def default_customer_knowledge_filename(customer_id: str) -> str:
    """Return `{customer_id}.md` (basename only)."""
    safe = Path(customer_id.strip()).name
    if not safe or safe != customer_id.strip():
        raise KnowledgeError(
            f"Invalid customer_id for knowledge filename: {customer_id!r}"
        )
    if not safe.endswith(".md"):
        return f"{safe}.md"
    return safe


def resolve_knowledge_basename(
    filename: str,
    *,
    project_root: Path | None = None,
) -> Path:
    """Resolve a basename-only knowledge file under knowledge/; reject traversal."""
    raw = (filename or "").strip()
    name = Path(raw).name
    if not raw or name != raw or name in (".", ".."):
        raise KnowledgeError(
            f"Knowledge filename must be a basename only (got {filename!r})"
        )
    if name == BASE_KNOWLEDGE_FILENAME:
        raise KnowledgeError(
            f"Refusing to use shared {BASE_KNOWLEDGE_FILENAME} as customer knowledge"
        )
    return knowledge_dir(project_root) / name


def resolve_customer_knowledge_path(
    profile: CPQProfile,
    *,
    project_root: Path | None = None,
) -> Path:
    """Resolve knowledge path from profile field or default `{customer_id}.md`."""
    configured = (profile.customer_knowledge_file or "").strip()
    if configured:
        return resolve_knowledge_basename(configured, project_root=project_root)
    return resolve_knowledge_basename(
        default_customer_knowledge_filename(profile.customer_id),
        project_root=project_root,
    )


def read_customer_knowledge_file(path: Path) -> dict[str, Any]:
    """Return UTF-8 text plus metadata for a knowledge file."""
    exists = path.is_file()
    text = path.read_text(encoding="utf-8") if exists else ""
    size = path.stat().st_size if exists else 0
    mtime = (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
        if exists
        else None
    )
    return {
        "exists": exists,
        "path": str(path),
        "filename": path.name,
        "text": text,
        "character_count": len(text),
        "size_bytes": size,
        "mtime": mtime,
    }


def scan_for_secrets(text: str) -> str | None:
    """Return a short match description if text looks like it contains secrets."""
    for pattern in _SECRET_PATTERNS:
        match = pattern.search(text)
        if match:
            return f"Matched pattern resembling a secret ({pattern.pattern[:40]}…)"
    return None


def ensure_customer_knowledge_stub(
    path: Path,
    *,
    customer_name: str,
) -> dict[str, Any]:
    """Create knowledge file with a short header if missing; never overwrite."""
    if path.name == BASE_KNOWLEDGE_FILENAME:
        raise KnowledgeError(
            f"Refusing to write shared {BASE_KNOWLEDGE_FILENAME}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    created = False
    if not path.is_file():
        header = (
            f"# Customer knowledge — {customer_name}\n\n"
            "Engagement discoveries (process quirks, aliases, gotchas). "
            "Keep entries short; point to `data/` for raw dumps. "
            "Never store passwords, OAuth secrets, or tokens.\n\n"
            "Updated via MCP `append_customer_knowledge`.\n"
        )
        path.write_text(header, encoding="utf-8")
        created = True
    meta = read_customer_knowledge_file(path)
    meta["created"] = created
    return meta


def append_customer_knowledge_entry(
    path: Path,
    *,
    environment: str,
    title: str,
    body: str,
    source: str = "agent",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Append a dated markdown section; enforce size caps and secret scan."""
    if path.name == BASE_KNOWLEDGE_FILENAME:
        raise KnowledgeError(
            f"Refusing to append to shared {BASE_KNOWLEDGE_FILENAME}"
        )

    clean_title = (title or "Discovery").strip() or "Discovery"
    clean_body = (body or "").strip()
    if not clean_body:
        raise KnowledgeError("Knowledge entry body/summary must be non-empty")
    if len(clean_body) > MAX_ENTRY_BODY_CHARS:
        raise KnowledgeError(
            f"Entry body exceeds {MAX_ENTRY_BODY_CHARS} characters "
            f"(got {len(clean_body)})"
        )

    secret_hit = scan_for_secrets(clean_title) or scan_for_secrets(clean_body)
    if secret_hit:
        raise KnowledgeError(
            f"Refusing to append: {secret_hit}. "
            "Never store passwords, OAuth secrets, or tokens in knowledge."
        )

    tag_line = ""
    if tags:
        safe_tags = [t.strip() for t in tags if t and t.strip()]
        if safe_tags:
            tag_line = f"tags: {', '.join(safe_tags)}\n"

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    entry = (
        f"\n## {clean_title}\n"
        f"- date: {stamp}\n"
        f"- env: {environment}\n"
        f"- source: {source}\n"
        f"{tag_line}"
        f"\n{clean_body}\n"
    )
    entry_bytes = len(entry.encode("utf-8"))

    path.parent.mkdir(parents=True, exist_ok=True)
    current_size = path.stat().st_size if path.is_file() else 0
    if current_size + entry_bytes > MAX_KNOWLEDGE_FILE_BYTES:
        raise KnowledgeError(
            f"Knowledge file would exceed {MAX_KNOWLEDGE_FILE_BYTES} bytes "
            f"(current={current_size}, entry={entry_bytes}). "
            "Trim older entries or start a new file."
        )

    with path.open("a", encoding="utf-8") as handle:
        handle.write(entry)

    meta = read_customer_knowledge_file(path)
    meta["bytes_appended"] = entry_bytes
    meta["title"] = clean_title
    return meta
