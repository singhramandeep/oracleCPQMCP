"""MCP tools for Oracle CPQ Commerce transaction documents."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from fastmcp.utilities.types import File

from oracle_cpq_mcp.core.commerce_paths import (
    DEFAULT_COMMERCE_DOC_VAR_NAME,
    commerce_documents_base,
    commerce_layout_path,
    resolve_process_var_name,
)
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.errors import build_tool_error
from oracle_cpq_mcp.core.pagination import build_page_params, enrich_pagination_hint
from oracle_cpq_mcp.core.preflight import resolve_write_execution, run_commerce_action_preflight
from oracle_cpq_mcp.core.responses import build_attachment_lead_envelope
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool


def _collection_extra(
    *,
    q_expr: str | None,
    fields: list[str] | None,
    orderby: list[str] | None,
    expand: str | None,
    exclude_field_types: str | None,
) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    if q_expr:
        extra["q"] = q_expr
    if fields:
        extra["fields"] = ",".join(fields)
    if orderby:
        extra["orderby"] = ",".join(orderby)
    if expand:
        extra["expand"] = expand
    if exclude_field_types:
        extra["excludeFieldTypes"] = exclude_field_types
    return extra


def _resolve_base(
    client: CPQClient,
    process_var_name: str | None,
    doc_var_name: str,
) -> str | dict[str, Any]:
    resolved = resolve_process_var_name(client.profile, process_var_name)
    if isinstance(resolved, dict):
        return resolved
    return commerce_documents_base(resolved, doc_var_name)


def _maybe_enrich(response: Any, tool_name: str) -> Any:
    if isinstance(response, dict) and ("hasMore" in response or "items" in response):
        return enrich_pagination_hint(response, tool_name)
    return response


def register_transaction_tools(mcp: Any, client: CPQClient) -> None:
    """Register Commerce transaction document tools on the FastMCP instance."""

    def list_transactions(
        limit: int = 100,
        offset: int = 0,
        total_results: bool = True,
        q_expr: str | None = None,
        fields: list[str] | None = None,
        orderby: list[str] | None = None,
        expand: str | None = None,
        exclude_field_types: str | None = None,
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
    ) -> dict[str, Any]:
        base = _resolve_base(client, process_var_name, doc_var_name)
        if isinstance(base, dict):
            return base
        params = build_page_params(
            limit,
            offset,
            total_results=total_results,
            extra=_collection_extra(
                q_expr=q_expr,
                fields=fields,
                orderby=orderby,
                expand=expand,
                exclude_field_types=exclude_field_types,
            )
            or None,
        )
        response = client.get(base, params=params)
        return _maybe_enrich(response, "list_transactions")

    list_transactions.__doc__ = TOOL_CATALOG["list_transactions"].description
    register_tool(mcp, list_transactions, "list_transactions")

    def get_transaction(
        transaction_id: str,
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
        expand: str | None = None,
        exclude_field_types: str | None = None,
    ) -> dict[str, Any]:
        base = _resolve_base(client, process_var_name, doc_var_name)
        if isinstance(base, dict):
            return base
        params = _collection_extra(
            q_expr=None,
            fields=None,
            orderby=None,
            expand=expand,
            exclude_field_types=exclude_field_types,
        )
        return client.get(f"{base}/{transaction_id}", params=params or None)

    get_transaction.__doc__ = TOOL_CATALOG["get_transaction"].description
    register_tool(mcp, get_transaction, "get_transaction")

    def list_transaction_lines(
        transaction_id: str,
        limit: int = 100,
        offset: int = 0,
        total_results: bool = True,
        q_expr: str | None = None,
        fields: list[str] | None = None,
        orderby: list[str] | None = None,
        expand: str | None = None,
        exclude_field_types: str | None = None,
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
    ) -> dict[str, Any]:
        base = _resolve_base(client, process_var_name, doc_var_name)
        if isinstance(base, dict):
            return base
        params = build_page_params(
            limit,
            offset,
            total_results=total_results,
            extra=_collection_extra(
                q_expr=q_expr,
                fields=fields,
                orderby=orderby,
                expand=expand,
                exclude_field_types=exclude_field_types,
            )
            or None,
        )
        response = client.get(f"{base}/{transaction_id}/transactionLine", params=params)
        return _maybe_enrich(response, "list_transaction_lines")

    list_transaction_lines.__doc__ = TOOL_CATALOG["list_transaction_lines"].description
    register_tool(mcp, list_transaction_lines, "list_transaction_lines")

    def get_transaction_line(
        transaction_id: str,
        document_number: str,
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
        expand: str | None = None,
        exclude_field_types: str | None = None,
    ) -> dict[str, Any]:
        base = _resolve_base(client, process_var_name, doc_var_name)
        if isinstance(base, dict):
            return base
        params = _collection_extra(
            q_expr=None,
            fields=None,
            orderby=None,
            expand=expand,
            exclude_field_types=exclude_field_types,
        )
        return client.get(
            f"{base}/{transaction_id}/transactionLine/{document_number}",
            params=params or None,
        )

    get_transaction_line.__doc__ = TOOL_CATALOG["get_transaction_line"].description
    register_tool(mcp, get_transaction_line, "get_transaction_line")

    def get_document_layout(
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
    ) -> dict[str, Any]:
        resolved = resolve_process_var_name(client.profile, process_var_name)
        if isinstance(resolved, dict):
            return resolved
        return client.get(commerce_layout_path(resolved, doc_var_name))

    get_document_layout.__doc__ = TOOL_CATALOG["get_document_layout"].description
    register_tool(mcp, get_document_layout, "get_document_layout")

    def generate_proposal(
        transaction_id: str,
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
        body: dict[str, Any] | None = None,
        dry_run: bool = True,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        base = _resolve_base(client, process_var_name, doc_var_name)
        if isinstance(base, dict):
            return base
        txn_path = f"{base}/{transaction_id}"
        post_path = f"{txn_path}/actions/generateProposal"
        return resolve_write_execution(
            read_only=client.profile.read_only,
            dry_run=dry_run,
            confirmation_token=confirmation_token,
            tool="generate_proposal",
            action="copy",
            preflight_fn=lambda: run_commerce_action_preflight(
                client,
                tool="generate_proposal",
                action_label="GENERATE PROPOSAL",
                transaction_path=txn_path,
                post_path=post_path,
                body=body,
            ),
            execute_fn=lambda: client.post(post_path, json_body=body or {}),
        )

    generate_proposal.__doc__ = TOOL_CATALOG["generate_proposal"].description
    register_tool(mcp, generate_proposal, "generate_proposal")

    def export_attachment(
        transaction_id: str,
        attribute_var_name: str,
        action_var_name: str = "exportAttachment",
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
        body: dict[str, Any] | None = None,
        dry_run: bool = True,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        base = _resolve_base(client, process_var_name, doc_var_name)
        if isinstance(base, dict):
            return base
        txn_path = f"{base}/{transaction_id}"
        post_path = f"{txn_path}/actions/{action_var_name}"
        payload: dict[str, Any] = dict(body or {})
        selections = list(payload.get("selections") or [])
        if attribute_var_name not in selections:
            selections = [attribute_var_name, *selections]
        payload["selections"] = selections
        return resolve_write_execution(
            read_only=client.profile.read_only,
            dry_run=dry_run,
            confirmation_token=confirmation_token,
            tool="export_attachment",
            action="copy",
            preflight_fn=lambda: run_commerce_action_preflight(
                client,
                tool="export_attachment",
                action_label=(
                    f"EXPORT ATTACHMENT attribute={attribute_var_name} "
                    f"via {action_var_name}"
                ),
                transaction_path=txn_path,
                post_path=post_path,
                body=payload,
            ),
            execute_fn=lambda: client.post(post_path, json_body=payload),
        )

    export_attachment.__doc__ = TOOL_CATALOG["export_attachment"].description
    register_tool(mcp, export_attachment, "export_attachment")

    def download_attachment(
        transaction_id: str,
        attribute_var_name: str,
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
        document_number: str = "1",
    ) -> list[Any] | dict[str, Any]:
        base = _resolve_base(client, process_var_name, doc_var_name)
        if isinstance(base, dict):
            return base
        txn = client.get(f"{base}/{transaction_id}")
        if not isinstance(txn, dict):
            return build_tool_error(
                "INVALID_RESPONSE",
                "Unexpected transaction payload while resolving attachment.",
                hint="Verify transaction_id and process_var_name.",
            )
        attr = txn.get(attribute_var_name)
        file_location = None
        file_name = f"{attribute_var_name}_{transaction_id}"
        if isinstance(attr, dict):
            file_location = attr.get("fileLocation")
            file_name = attr.get("fileName") or file_name
        if not file_location:
            return build_tool_error(
                "NOT_FOUND",
                f"Attachment attribute '{attribute_var_name}' has no fileLocation "
                f"on transaction {transaction_id}.",
                hint=(
                    "Generate or export the attachment first "
                    "(generate_proposal / export_attachment)."
                ),
            )
        parsed = urlparse(str(file_location))
        path = parsed.path or ""
        marker = "/rest/"
        if marker in path:
            # /rest/v18/... -> /...
            after = path.split(marker, 1)[1]
            parts = after.split("/", 1)
            path = f"/{parts[1]}" if len(parts) > 1 else path
        elif not path.startswith("/"):
            path = f"/{path}"
        data = client.get_bytes(path, accept="*/*")
        return [
            build_attachment_lead_envelope(
                "download_attachment",
                message=(
                    f"Downloaded attachment '{attribute_var_name}' "
                    f"for transaction {transaction_id}."
                ),
                filename=str(file_name),
                extra={
                    "transaction_id": transaction_id,
                    "attribute_var_name": attribute_var_name,
                    "document_number": document_number,
                },
            ),
            File(data=data, name=str(file_name)),
        ]

    download_attachment.__doc__ = TOOL_CATALOG["download_attachment"].description
    register_tool(mcp, download_attachment, "download_attachment")

    def copy_transaction(
        transaction_id: str,
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
        body: dict[str, Any] | None = None,
        dry_run: bool = True,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        base = _resolve_base(client, process_var_name, doc_var_name)
        if isinstance(base, dict):
            return base
        txn_path = f"{base}/{transaction_id}"
        post_path = f"{txn_path}/actions/_copy_transaction"
        return resolve_write_execution(
            read_only=client.profile.read_only,
            dry_run=dry_run,
            confirmation_token=confirmation_token,
            tool="copy_transaction",
            action="copy",
            preflight_fn=lambda: run_commerce_action_preflight(
                client,
                tool="copy_transaction",
                action_label="COPY TRANSACTION",
                transaction_path=txn_path,
                post_path=post_path,
                body=body,
            ),
            execute_fn=lambda: client.post(post_path, json_body=body or {}),
        )

    copy_transaction.__doc__ = TOOL_CATALOG["copy_transaction"].description
    register_tool(mcp, copy_transaction, "copy_transaction")

    def copy_transaction_lines(
        transaction_id: str,
        process_var_name: str | None = None,
        doc_var_name: str = DEFAULT_COMMERCE_DOC_VAR_NAME,
        action_name: str = "copyLineItems_t",
        body: dict[str, Any] | None = None,
        dry_run: bool = True,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        base = _resolve_base(client, process_var_name, doc_var_name)
        if isinstance(base, dict):
            return base
        txn_path = f"{base}/{transaction_id}"
        post_path = f"{txn_path}/actions/{action_name}"
        return resolve_write_execution(
            read_only=client.profile.read_only,
            dry_run=dry_run,
            confirmation_token=confirmation_token,
            tool="copy_transaction_lines",
            action="copy",
            preflight_fn=lambda: run_commerce_action_preflight(
                client,
                tool="copy_transaction_lines",
                action_label=f"COPY TRANSACTION LINES via {action_name}",
                transaction_path=txn_path,
                post_path=post_path,
                body=body,
            ),
            execute_fn=lambda: client.post(post_path, json_body=body or {}),
        )

    copy_transaction_lines.__doc__ = TOOL_CATALOG["copy_transaction_lines"].description
    register_tool(mcp, copy_transaction_lines, "copy_transaction_lines")
