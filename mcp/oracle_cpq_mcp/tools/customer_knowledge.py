"""MCP tools for profile-scoped customer knowledge (cross-session memory)."""

from __future__ import annotations

from typing import Any

from oracle_cpq_mcp.core.config import update_profile_env_key
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.errors import build_tool_error
from oracle_cpq_mcp.core.knowledge import (
    KnowledgeError,
    append_customer_knowledge_entry,
    default_customer_knowledge_filename,
    ensure_customer_knowledge_stub,
    read_customer_knowledge_file,
    resolve_customer_knowledge_path,
)
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool

_RELOAD_HINT = (
    "Knowledge is durable on disk. Call get_customer_knowledge in this session "
    "to reuse facts. Reload/restart Oracle CPQ MCP so injected Customer knowledge "
    "instructions pick up new text in a new chat."
)


def register_customer_knowledge_tools(mcp: Any, client: CPQClient) -> None:
    """Register customer knowledge read/ensure/append tools."""

    def get_customer_knowledge() -> dict[str, Any]:
        profile = client.profile
        path = resolve_customer_knowledge_path(profile)
        meta = read_customer_knowledge_file(path)
        configured = bool((profile.customer_knowledge_file or "").strip())
        return {
            "filename": path.name,
            "path": str(path),
            "configured_on_profile": configured,
            "profile_field": profile.customer_knowledge_file,
            "exists": meta["exists"],
            "text": meta["text"],
            "character_count": meta["character_count"],
            "size_bytes": meta["size_bytes"],
            "mtime": meta["mtime"],
            "hint": (
                None
                if configured and meta["exists"]
                else (
                    "Profile customer_knowledge_file is unset or file missing. "
                    "Call ensure_customer_knowledge to create the stub and wire the profile."
                )
            ),
        }

    get_customer_knowledge.__doc__ = TOOL_CATALOG["get_customer_knowledge"].description
    register_tool(mcp, get_customer_knowledge, "get_customer_knowledge")

    def ensure_customer_knowledge() -> dict[str, Any]:
        profile = client.profile
        filename = (profile.customer_knowledge_file or "").strip() or (
            default_customer_knowledge_filename(profile.customer_id)
        )
        try:
            path = resolve_customer_knowledge_path(profile)
            # If unset, resolve uses default; keep filename for YAML write.
            if not (profile.customer_knowledge_file or "").strip():
                from oracle_cpq_mcp.core.knowledge import resolve_knowledge_basename

                path = resolve_knowledge_basename(filename)
            stub = ensure_customer_knowledge_stub(
                path, customer_name=profile.customer_name or profile.customer_id
            )
        except KnowledgeError as exc:
            return build_tool_error(
                getattr(exc, "code", "VALIDATION_ERROR"),  # type: ignore[arg-type]
                str(exc),
                hint="Use a basename like hunterFusion.md under knowledge/.",
            )

        profile_path = None
        field_updated = False
        if not (profile.customer_knowledge_file or "").strip():
            try:
                profile_path = update_profile_env_key(
                    profile.customer_id,
                    "CUSTOMER_KNOWLEDGE_FILE",
                    path.name,
                )
                profile.customer_knowledge_file = path.name
                field_updated = True
            except (ValueError, FileNotFoundError, ImportError) as exc:
                return build_tool_error(
                    "VALIDATION_ERROR",
                    f"Created knowledge stub but failed to update profile: {exc}",
                    hint=(
                        f"Set customer_knowledge_file: {path.name} on the profile YAML "
                        "manually, then reload MCP."
                    ),
                    details={"path": str(path), "filename": path.name},
                )

        return {
            "filename": path.name,
            "path": str(path),
            "created": stub.get("created", False),
            "profile_field_updated": field_updated,
            "profile_path": str(profile_path) if profile_path else None,
            "character_count": stub["character_count"],
            "reload_hint": _RELOAD_HINT,
        }

    ensure_customer_knowledge.__doc__ = TOOL_CATALOG[
        "ensure_customer_knowledge"
    ].description
    register_tool(mcp, ensure_customer_knowledge, "ensure_customer_knowledge")

    def append_customer_knowledge(
        summary: str,
        title: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        profile = client.profile
        try:
            # Ensure file + profile wiring so appends are discoverable next session.
            if not (profile.customer_knowledge_file or "").strip():
                ensure_result = ensure_customer_knowledge()
                if ensure_result.get("status") == "error":
                    return ensure_result

            path = resolve_customer_knowledge_path(profile)
            if not path.is_file():
                ensure_customer_knowledge_stub(
                    path,
                    customer_name=profile.customer_name or profile.customer_id,
                )

            meta = append_customer_knowledge_entry(
                path,
                environment=profile.environment,
                title=(title or "Discovery").strip() or "Discovery",
                body=summary,
                source="agent",
                tags=tags,
            )
        except KnowledgeError as exc:
            return build_tool_error(
                getattr(exc, "code", "VALIDATION_ERROR"),  # type: ignore[arg-type]
                str(exc),
                hint=(
                    "Summarize discoveries in plain language; do not paste passwords, "
                    "oauth secrets, or Bearer tokens. Point to data/ for large dumps."
                ),
            )

        return {
            "filename": path.name,
            "path": str(path),
            "title": meta.get("title"),
            "bytes_appended": meta.get("bytes_appended"),
            "character_count": meta["character_count"],
            "size_bytes": meta["size_bytes"],
            "reload_hint": _RELOAD_HINT,
        }

    append_customer_knowledge.__doc__ = TOOL_CATALOG[
        "append_customer_knowledge"
    ].description
    register_tool(mcp, append_customer_knowledge, "append_customer_knowledge")
