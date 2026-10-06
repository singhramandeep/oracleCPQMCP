"""MCP tools for post-response Excel / Word export offers."""

from __future__ import annotations

import logging
from typing import Any, Literal

from oracle_cpq_mcp.core.config import update_profile_env_key
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.errors import build_tool_error
from oracle_cpq_mcp.core.responses import build_attachment_lead_envelope
from oracle_cpq_mcp.exporters.branded_documents import last_template_status
from oracle_cpq_mcp.exporters.chat_document import build_docx_from_tables
from oracle_cpq_mcp.exporters.records_excel import build_multi_sheet_workbook
from oracle_cpq_mcp.exporters.response_export import (
    MAX_EXPORT_SHEETS,
    count_sheet_rows,
    export_filename,
    file_uri,
    relative_export_path,
    validate_sheets_payload,
    write_export_bytes,
)
from oracle_cpq_mcp.prompts.refined_prompt_document import (
    compose_export_notes,
    prepend_refined_prompt_sheet,
)
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.security.context import get_security_context
from oracle_cpq_mcp.tools._register import register_tool

logger = logging.getLogger(__name__)

PostResponseExportPolicy = Literal["ask", "never", "always_excel"]
ExportChoice = Literal["excel", "word", "both", "skip", "always_excel", "never"]


def _active_customer_id() -> str:
    ctx = get_security_context()
    if ctx is None or not ctx.customer_id:
        raise RuntimeError("Security context not configured (no active customer profile).")
    return ctx.customer_id


def _set_post_response_export(policy: PostResponseExportPolicy) -> dict[str, Any]:
    customer_id = _active_customer_id()
    path = update_profile_env_key(customer_id, "POST_RESPONSE_EXPORT", policy)
    return {
        "policy": policy,
        "path": str(path),
        "key": "POST_RESPONSE_EXPORT",
        "note": (
            "Treat this result as source of truth for the rest of this session. "
            "Reload the Oracle CPQ MCP server if you need SERVER_INSTRUCTIONS rebuilt "
            "from the updated profile flag."
        ),
    }


def _build_export_result(
    *,
    client: CPQClient,
    tool_name: str,
    title: str,
    sheets: list[dict[str, Any]],
    notes: str | None,
    kind: Literal["excel", "word"],
    diagrams: list[dict[str, Any]] | None = None,
    refined_prompt: str | None = None,
) -> dict[str, Any]:
    """Build workbook/docx, write under exports/, return a single MCP object envelope.

    Cursor and similar hosts fail when tools return ``[envelope, File]`` (no
    structuredContent). Path/URI on disk is the durable deliverable.
    """
    profile = client.profile
    include_refined = bool(
        getattr(profile, "include_refined_prompt_in_documents", True)
    )
    normalized = validate_sheets_payload(sheets)
    if kind == "excel":
        normalized = validate_sheets_payload(
            prepend_refined_prompt_sheet(
                normalized,
                refined_prompt,
                enabled=include_refined,
                max_sheets=MAX_EXPORT_SHEETS,
            )
        )
    notes = compose_export_notes(
        notes, refined_prompt, enabled=include_refined and kind == "word"
    )
    diagrams_embedded = 0
    diagrams_skipped: list[dict[str, str]] = []
    content: dict[str, int] | None = None
    if kind == "excel":
        payload = build_multi_sheet_workbook(normalized)
        filename = export_filename(title, extension="xlsx")
        message_kind = "Excel"
        path = write_export_bytes(profile, filename, payload)
    else:
        # Phase 1: title + notes + tables — always on disk before Mermaid.
        filename = export_filename(title, extension="docx")
        message_kind = "Word"
        phase1 = build_docx_from_tables(
            title=title,
            sheets=normalized,
            notes=notes,
            diagrams=None,
        )
        path = write_export_bytes(profile, filename, phase1.payload)
        content = phase1.content_dict()
        payload = phase1.payload
        # Phase 2: best-effort diagrams; never erase phase-1 content on failure.
        if diagrams:
            try:
                phase2 = build_docx_from_tables(
                    title=title,
                    sheets=normalized,
                    notes=notes,
                    diagrams=diagrams,
                )
                path.write_bytes(phase2.payload)
                payload = phase2.payload
                diagrams_embedded = phase2.diagrams_embedded
                diagrams_skipped = list(phase2.diagrams_skipped)
                content = phase2.content_dict()
            except Exception as exc:
                logger.info(
                    "Word diagram phase failed; keeping content-only export: %s",
                    type(exc).__name__,
                )
                for index, spec in enumerate(diagrams):
                    if not isinstance(spec, dict):
                        title_d = f"diagram[{index}]"
                    else:
                        title_d = str(
                            spec.get("title") or f"Diagram {index + 1}"
                        ).strip() or f"Diagram {index + 1}"
                    diagrams_skipped.append(
                        {
                            "title": title_d,
                            "reason": (
                                f"diagram phase failed: {type(exc).__name__} "
                                "(content-only file kept)"
                            ),
                        }
                    )

    rel = relative_export_path(profile, filename)
    uri = file_uri(path)
    row_count = count_sheet_rows(normalized)
    template_kind = "excel" if kind == "excel" else "word"
    template_status = last_template_status(template_kind)
    template_info = (
        template_status.as_dict()
        if hasattr(template_status, "as_dict")
        else {"kind": template_kind, "applied": False}
    )
    template_note = ""
    if not template_info.get("applied"):
        reason = template_info.get("reason") or "unavailable"
        template_note = (
            f" Template not applied ({reason}): place a valid "
            f"{'Excel Template.xlsx' if kind == 'excel' else 'Word Template.docx'} "
            "under .config/template/."
        )
    diagram_note = ""
    if kind == "word" and (diagrams_embedded or diagrams_skipped):
        diagram_note = (
            f" Diagrams: {diagrams_embedded} embedded"
            f"{f', {len(diagrams_skipped)} skipped' if diagrams_skipped else ''}."
        )
    content_note = ""
    if content is not None:
        content_note = (
            f" Content: {content['paragraphs']} paragraph(s), "
            f"{content['tables']} table(s), "
            f"{content['nonempty_text_chars']} text char(s)."
        )
    summary = (
        f"Exported {message_kind} for {title!r} "
        f"({len(normalized)} sheet(s), {row_count} row(s)) to {rel}."
        f"{template_note}{diagram_note}{content_note}"
    )
    extra: dict[str, Any] = {
        "title": title,
        "path": rel,
        "absolute_path": str(path),
        "uri": uri,
        "sheet_count": len(normalized),
        "row_count": row_count,
        "format": kind,
        "template": template_info,
    }
    if kind == "word":
        extra["diagrams_embedded"] = diagrams_embedded
        extra["diagrams_skipped"] = diagrams_skipped
        if content is not None:
            extra["content"] = content
    extra["refined_prompt_included"] = bool(
        include_refined and refined_prompt and str(refined_prompt).strip()
    )
    return build_attachment_lead_envelope(
        tool_name,
        message=summary,
        filename=filename,
        extra=extra,
    )


def register_response_export_tools(mcp: Any, client: CPQClient) -> None:
    """Register post-response export offer / Excel / Word tools."""

    def offer_export_response(
        title: str,
        sheets: list[dict[str, Any]] | None = None,
        notes: str | None = None,
        choice: ExportChoice | None = None,
    ) -> dict[str, Any]:
        """Ask whether to export tabular chat data; handle choice / policy updates."""
        pending = {
            "title": title,
            "sheet_count": len(sheets or []),
            "row_count": count_sheet_rows(sheets or []),
            "notes_present": bool(notes and str(notes).strip()),
        }
        if choice is None:
            return {
                "needs_user_input": True,
                "elicitation_preferred": True,
                "question": (
                    f"Export tabular data from {title!r}? "
                    "Excel (.xlsx), Word (.docx under data/.../exports with a local file link), "
                    "both, skip, always export Excel without asking, or never ask."
                ),
                "choices": [
                    "excel — write .xlsx under data/{profile}/{env}/exports/",
                    "word — write .docx under data/.../exports/ and return path + file:// URI",
                    "both — Excel and Word",
                    "skip — do not export this response",
                    "always_excel — export Excel now and set POST_RESPONSE_EXPORT=always_excel",
                    "never — skip and set POST_RESPONSE_EXPORT=never",
                ],
                "hint": (
                    "Prefer host MCP elicitation when available; otherwise ask in chat, "
                    "then call offer_export_response again with choice=… "
                    "For excel/word/both/always_excel, also call export_response_excel "
                    "and/or export_response_word with the same title/sheets/notes."
                ),
                "pending": pending,
                "post_response_export": getattr(
                    client.profile, "post_response_export", "ask"
                ),
            }

        if choice == "skip":
            return {
                "exported": False,
                "choice": "skip",
                "message": "User declined post-response export.",
                "pending": pending,
            }

        if choice == "never":
            flag = _set_post_response_export("never")
            return {
                "exported": False,
                "choice": "never",
                "policy": flag,
                "message": (
                    "Skipped export and set POST_RESPONSE_EXPORT=never on the profile .env."
                ),
                "pending": pending,
            }

        if choice == "always_excel":
            flag = _set_post_response_export("always_excel")
            return {
                "exported": False,
                "choice": "always_excel",
                "policy": flag,
                "next_tools": ["export_response_excel"],
                "message": (
                    "POST_RESPONSE_EXPORT=always_excel written. "
                    "Call export_response_excel now with the same title/sheets."
                ),
                "pending": pending,
            }

        if choice == "excel":
            next_tools = ["export_response_excel"]
        elif choice == "word":
            next_tools = ["export_response_word"]
        else:
            next_tools = ["export_response_excel", "export_response_word"]

        return {
            "exported": False,
            "choice": choice,
            "next_tools": next_tools,
            "message": (
                f"User chose {choice}. Call {', '.join(next_tools)} with the same "
                "title/sheets (and notes/diagrams for Word)."
            ),
            "pending": pending,
        }

    offer_export_response.__doc__ = TOOL_CATALOG["offer_export_response"].description
    register_tool(mcp, offer_export_response, "offer_export_response")

    def export_response_excel(
        title: str,
        sheets: list[dict[str, Any]],
        notes: str | None = None,
        refined_prompt: str | None = None,
    ) -> dict[str, Any]:
        return _build_export_result(
            client=client,
            tool_name="export_response_excel",
            title=title,
            sheets=sheets,
            notes=notes,
            kind="excel",
            refined_prompt=refined_prompt,
        )

    export_response_excel.__doc__ = TOOL_CATALOG["export_response_excel"].description
    register_tool(mcp, export_response_excel, "export_response_excel")

    def export_response_word(
        title: str,
        sheets: list[dict[str, Any]],
        notes: str | None = None,
        diagrams: list[dict[str, Any]] | None = None,
        refined_prompt: str | None = None,
    ) -> dict[str, Any]:
        try:
            return _build_export_result(
                client=client,
                tool_name="export_response_word",
                title=title,
                sheets=sheets,
                notes=notes,
                kind="word",
                diagrams=diagrams,
                refined_prompt=refined_prompt,
            )
        except RuntimeError as exc:
            return build_tool_error(
                "INTERNAL_ERROR",
                str(exc),
                hint='Install with: pip install python-docx  or  pip install -e ".[docs]"',
            )

    export_response_word.__doc__ = TOOL_CATALOG["export_response_word"].description
    register_tool(mcp, export_response_word, "export_response_word")

    def set_post_response_export(
        policy: PostResponseExportPolicy,
    ) -> dict[str, Any]:
        return _set_post_response_export(policy)

    set_post_response_export.__doc__ = TOOL_CATALOG["set_post_response_export"].description
    register_tool(mcp, set_post_response_export, "set_post_response_export")
