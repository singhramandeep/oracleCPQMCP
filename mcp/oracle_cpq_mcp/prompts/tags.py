"""Tag catalog helpers for refined / saved prompts."""

from __future__ import annotations

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG

# Fixed intent tags (in addition to tool domains).
INTENT_TAGS = frozenset({"audit", "export", "write", "discovery", "read"})

ALLOWED_TAGS = frozenset(
    {
        "users",
        "groups",
        "datatables",
        "bml",
        "commerce",
        "performance",
        "parts",
        "tasks",
        "configuration",
        "meta",
        *INTENT_TAGS,
    }
)


def tags_for_tools(tool_names: list[str] | None, *, extra: list[str] | None = None) -> list[str]:
    """Derive constrained tags from tools used (+ optional intent extras)."""
    tags: set[str] = set()
    for name in tool_names or []:
        spec = TOOL_CATALOG.get(name)
        if spec:
            tags.add(spec.domain)
            if spec.operation == "write":
                tags.add("write")
            else:
                tags.add("read")
            if "export" in name or "download" in name:
                tags.add("export")
            if name == "discover_tools":
                tags.add("discovery")
    for item in extra or []:
        normalized = item.strip().lower()
        if normalized in ALLOWED_TAGS:
            tags.add(normalized)
    return sorted(tags)


def normalize_tags(tags: list[str] | None) -> list[str]:
    """Keep only allowlisted tags."""
    if not tags:
        return []
    return sorted({t.strip().lower() for t in tags if t.strip().lower() in ALLOWED_TAGS})
