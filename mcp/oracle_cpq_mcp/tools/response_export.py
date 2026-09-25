"""MCP tools for post-response Excel / Word export offers."""

from __future__ import annotations

from typing import Any, Literal

from fastmcp.utilities.types import File

from oracle_cpq_mcp.core.config import update_profile_env_key
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.errors import build_tool_error
from oracle_cpq_mcp.core.responses import build_attachment_lead_envelope
from oracle_cpq_mcp.exporters.branded_documents import last_template_status
from oracle_cpq_mcp.exporters.chat_document import build_docx_from_tables
from oracle_cpq_mcp.exporters.records_excel import build_multi_sheet_workbook
from oracle_cpq_mcp.exporters.response_export import (
    count_sheet_rows,
    export_filename,
    file_uri,
    relative_export_path,
    validate_sheets_payload,
    write_export_bytes,
)
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.security.context import get_security_context
from oracle_cpq_mcp.tools._register import register_tool

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
) -> list[Any]:
    profile = client.profile
    normalized = validate_sheets_payload(sheets)
    diagrams_embedded = 0
    diagrams_skipped: list[dict[str, str]] = []
    if kind == "excel":
        payload = build_multi_sheet_workbook(normalized)
        filename = export_filename(title, extension="xlsx")
        mime_format = "xlsx"
        message_kind = "Excel"
    else:
        docx_result = build_docx_from_tables(
            title=title,
            sheets=normalized,
            notes=notes,
            diagrams=diagrams,
        )
        payload = docx_result.payload
        diagrams_embedded = docx_result.diagrams_embedded
        diagrams_skipped = list(docx_result.diagrams_skipped)
        filename = export_filename(title, extension="docx")
        mime_format = "docx"
        message_kind = "Word"

    path = write_export_bytes(profile, filename, payload)
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
    summary = (
        f"Exported {message_kind} for {title!r} "
        f"({len(normalized)} sheet(s), {row_count} row(s)) to {rel}."
        f"{template_note}{diagram_note}"
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
    return [
        build_attachment_lead_envelope(
            tool_name,
            message=summary,
            filename=filename,
            extra=extra,
        ),
        File(data=payload, format=mime_format, name=filename),
    ]


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
                    "excel — write .xlsx under data/{profile}/{env}/exports/ and attach",
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
    ) -> list[Any]:
        return _build_export_result(
            client=client,
            tool_name="export_response_excel",
            title=title,
            sheets=sheets,
            notes=notes,
            kind="excel",
        )

    export_response_excel.__doc__ = TOOL_CATALOG["export_response_excel"].description
    register_tool(mcp, export_response_excel, "export_response_excel")

    def export_response_word(
        title: str,
        sheets: list[dict[str, Any]],
        notes: str | None = None,
        diagrams: list[dict[str, Any]] | None = None,
    ) -> list[Any] | dict[str, Any]:
        try:
            return _build_export_result(
                client=client,
                tool_name="export_response_word",
                title=title,
                sheets=sheets,
                notes=notes,
                kind="word",
                diagrams=diagrams,
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
