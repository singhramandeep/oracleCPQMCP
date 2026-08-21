"""MCP tools for Local ``data/`` snapshots and full-collection sync."""

from __future__ import annotations

import logging
from typing import Any, Literal

from oracle_cpq_mcp.core.bml_fetchers import fetch_all_util_library_code
from oracle_cpq_mcp.core.commerce_paths import (
    DEFAULT_COMMERCE_DOC_VAR_NAME,
    DEFAULT_LINE_DOC_VAR_NAME,
    commerce_document_path,
    resolve_process_var_name,
)
from oracle_cpq_mcp.core.config import update_profile_env_key
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.errors import build_tool_error
from oracle_cpq_mcp.core.local_data import (
    LocalDataDomain,
    get_snapshot_status,
    list_snapshots,
    load_snapshot_summary,
    parse_local_data_policy,
    persist_bml_functions_snapshot,
    persist_commerce_collection,
    persist_datatable_snapshot,
    persist_groups_snapshot,
    persist_users_snapshot,
)
from oracle_cpq_mcp.core.pagination import iterate_collection
from oracle_cpq_mcp.core.progress import report_tool_progress
from oracle_cpq_mcp.core.users_filters import UserStatusFilter
from oracle_cpq_mcp.exporters.records_excel import build_records_workbook
from oracle_cpq_mcp.exporters.users_excel import (
    build_users_workbook,
    fetch_all_users,
)
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.security.context import get_security_context
from oracle_cpq_mcp.tools._register import register_tool

logger = logging.getLogger(__name__)

LocalDataChoice = Literal["use_cache", "fetch_fresh", "prefer", "never"]

_GROUP_COLUMNS = (
    "variableName",
    "label",
    "description",
    "companyName",
    "type",
)


def _active_profile_from_client(client: CPQClient):
    return client.profile


def _active_customer_id() -> str:
    ctx = get_security_context()
    if ctx is None or not ctx.customer_id:
        raise RuntimeError("Security context not configured (no active customer profile).")
    return ctx.customer_id


def _set_local_data_policy(policy: str) -> dict[str, Any]:
    normalized = parse_local_data_policy(policy)
    customer_id = _active_customer_id()
    path = update_profile_env_key(customer_id, "LOCAL_DATA_POLICY", normalized)
    return {
        "policy": normalized,
        "path": str(path),
        "key": "LOCAL_DATA_POLICY",
        "note": (
            "Treat this result as source of truth for the rest of this session. "
            "Reload the Oracle CPQ MCP server if you need SERVER_INSTRUCTIONS rebuilt "
            "from the updated profile flag."
        ),
    }


def register_local_data_tools(mcp: Any, client: CPQClient) -> None:
    """Register local snapshot UX tools and sync_*_local tools."""

    def list_local_data() -> dict[str, Any]:
        profile = _active_profile_from_client(client)
        items = list_snapshots(profile)
        return {
            "customer_id": profile.customer_id,
            "environment": profile.environment,
            "local_data_policy": profile.local_data_policy,
            "count": len(items),
            "items": items,
        }

    list_local_data.__doc__ = TOOL_CATALOG["list_local_data"].description
    register_tool(mcp, list_local_data, "list_local_data")

    def get_local_data_status(
        domain: LocalDataDomain,
        process_var_name: str | None = None,
        table_name: str | None = None,
    ) -> dict[str, Any]:
        profile = _active_profile_from_client(client)
        status = get_snapshot_status(
            profile,
            domain,
            process_var_name=process_var_name,
            table_name=table_name,
        )
        status["local_data_policy"] = profile.local_data_policy
        return status

    get_local_data_status.__doc__ = TOOL_CATALOG["get_local_data_status"].description
    register_tool(mcp, get_local_data_status, "get_local_data_status")

    def load_local_data(
        domain: LocalDataDomain,
        process_var_name: str | None = None,
        table_name: str | None = None,
        include_payload: bool = False,
        payload_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        profile = _active_profile_from_client(client)
        return load_snapshot_summary(
            profile,
            domain,
            process_var_name=process_var_name,
            table_name=table_name,
            include_payload=include_payload,
            payload_keys=payload_keys,
        )

    load_local_data.__doc__ = TOOL_CATALOG["load_local_data"].description
    register_tool(mcp, load_local_data, "load_local_data")

    def set_local_data_policy(policy: Literal["ask", "prefer", "never"]) -> dict[str, Any]:
        return _set_local_data_policy(policy)

    set_local_data_policy.__doc__ = TOOL_CATALOG["set_local_data_policy"].description
    register_tool(mcp, set_local_data_policy, "set_local_data_policy")

    def offer_use_local_data(
        domain: LocalDataDomain,
        process_var_name: str | None = None,
        table_name: str | None = None,
        choice: LocalDataChoice | None = None,
    ) -> dict[str, Any]:
        profile = _active_profile_from_client(client)
        status = get_snapshot_status(
            profile,
            domain,
            process_var_name=process_var_name,
            table_name=table_name,
        )
        if choice is None:
            retrieved = None
            if status.get("available") and isinstance(status.get("manifest"), dict):
                retrieved = status["manifest"].get("retrieved_at")
            if status.get("available"):
                question = (
                    f"Local {domain} snapshot exists"
                    + (f" (retrieved_at={retrieved})" if retrieved else "")
                    + ". Use cached data, fetch fresh from CPQ, "
                    "or change LOCAL_DATA_POLICY?"
                )
            else:
                question = (
                    f"No local {domain} snapshot found. Fetch fresh from CPQ, "
                    "or set LOCAL_DATA_POLICY for future runs?"
                )
            return {
                "needs_user_input": True,
                "available": bool(status.get("available")),
                "domain": domain,
                "local_data_policy": profile.local_data_policy,
                "retrieved_at": retrieved,
                "question": question,
                "choices": [
                    "use_cache — use local data/ snapshot (if available)",
                    "fetch_fresh — call CPQ / sync_*_local now",
                    "prefer — set LOCAL_DATA_POLICY=prefer and use cache when present",
                    "never — set LOCAL_DATA_POLICY=never (always fresh)",
                ],
                "hint": (
                    "Ask the user, then call offer_use_local_data again with choice=… "
                    "Same domain / process_var_name / table_name."
                ),
                "pending": {
                    "domain": domain,
                    "process_var_name": process_var_name,
                    "table_name": table_name,
                    "status": status,
                },
            }

        if choice == "prefer":
            flag = _set_local_data_policy("prefer")
            loaded = (
                load_local_data(
                    domain,
                    process_var_name=process_var_name,
                    table_name=table_name,
                )
                if status.get("available")
                else status
            )
            return {
                "choice": choice,
                "policy": flag,
                "action": "use_cache" if status.get("available") else "fetch_fresh",
                "data": loaded,
            }
        if choice == "never":
            flag = _set_local_data_policy("never")
            return {
                "choice": choice,
                "policy": flag,
                "action": "fetch_fresh",
                "message": "LOCAL_DATA_POLICY=never. Call the matching sync_*_local or live CPQ tools.",
            }
        if choice == "use_cache":
            if not status.get("available"):
                return {
                    "choice": choice,
                    "action": "fetch_fresh",
                    "message": "No local snapshot available; fetch fresh instead.",
                    "status": status,
                }
            return {
                "choice": choice,
                "action": "use_cache",
                "data": load_local_data(
                    domain,
                    process_var_name=process_var_name,
                    table_name=table_name,
                ),
            }
        # fetch_fresh
        return {
            "choice": "fetch_fresh",
            "action": "fetch_fresh",
            "message": (
                f"Fetch fresh {domain} data via sync_*_local (or live list/export tools), "
                "which will refresh data/{customer}/{env}/…"
            ),
            "suggested_tools": {
                "users": "sync_users_local",
                "groups": "sync_groups_local",
                "bml": "sync_bml_local",
                "commerce": "sync_commerce_metadata_local",
                "datatables": "sync_datatable_local",
            }.get(domain),
        }

    offer_use_local_data.__doc__ = TOOL_CATALOG["offer_use_local_data"].description
    register_tool(mcp, offer_use_local_data, "offer_use_local_data")

    def sync_users_local(
        status_filter: UserStatusFilter = "active",
        q_expr: str | None = None,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        report_tool_progress(0, 1, message="Syncing all users to local data/")
        fetch_result = fetch_all_users(
            client,
            status_filter=status_filter,
            q_expr=q_expr,
        )
        users = [u for u in fetch_result.items if isinstance(u, dict)]
        xlsx_bytes = build_users_workbook(users, columns=columns)
        persisted = persist_users_snapshot(
            client.profile,
            users,
            xlsx_bytes,
            source_tool="sync_users_local",
            filters={"status_filter": status_filter, "q_expr": q_expr},
            extra={
                "truncated": fetch_result.truncated,
                "has_more": fetch_result.has_more,
            },
        )
        report_tool_progress(1, 1, message="Users sync complete")
        return {
            "domain": "users",
            "truncated": fetch_result.truncated,
            "has_more": fetch_result.has_more,
            **persisted,
        }

    sync_users_local.__doc__ = TOOL_CATALOG["sync_users_local"].description
    register_tool(mcp, sync_users_local, "sync_users_local")

    def sync_groups_local() -> dict[str, Any]:
        company = client.profile.company_login_name
        report_tool_progress(0, 1, message="Syncing all groups to local data/")
        fetch_result = iterate_collection(
            client,
            f"/companies/{company}/groups",
            page_size=100,
            max_items=10_000,
            on_progress=lambda count, message: report_tool_progress(
                float(count),
                10_000.0,
                message=message or f"Fetching groups ({count})",
            ),
        )
        groups = [g for g in fetch_result.items if isinstance(g, dict)]
        xlsx_bytes = build_records_workbook(
            groups,
            sheet_title="Groups",
            columns=list(_GROUP_COLUMNS),
        )
        persisted = persist_groups_snapshot(
            client.profile,
            groups,
            xlsx_bytes,
            source_tool="sync_groups_local",
            extra={
                "truncated": fetch_result.truncated,
                "has_more": fetch_result.has_more,
                "company_login_name": company,
            },
        )
        report_tool_progress(1, 1, message="Groups sync complete")
        return {
            "domain": "groups",
            "truncated": fetch_result.truncated,
            "has_more": fetch_result.has_more,
            **persisted,
        }

    sync_groups_local.__doc__ = TOOL_CATALOG["sync_groups_local"].description
    register_tool(mcp, sync_groups_local, "sync_groups_local")

    def sync_bml_local() -> dict[str, Any]:
        report_tool_progress(0, 1, message="Syncing util library BML to local data/")
        functions, truncated, has_more = fetch_all_util_library_code(client)
        persisted = persist_bml_functions_snapshot(
            client.profile,
            functions,
            source_tool="sync_bml_local",
            extra={"truncated": truncated, "has_more": has_more, "delivery": "json"},
        )
        report_tool_progress(1, 1, message="BML sync complete")
        return {
            "domain": "bml",
            "truncated": truncated,
            "has_more": has_more,
            **persisted,
        }

    sync_bml_local.__doc__ = TOOL_CATALOG["sync_bml_local"].description
    register_tool(mcp, sync_bml_local, "sync_bml_local")

    def sync_commerce_metadata_local(
        process_var_name: str | None = None,
        expand_all: bool = True,
    ) -> dict[str, Any]:
        resolved = resolve_process_var_name(client.profile, process_var_name)
        if isinstance(resolved, dict):
            return resolved
        process = str(resolved)
        collections = (
            ("header_attributes", DEFAULT_COMMERCE_DOC_VAR_NAME, "attributes"),
            ("header_actions", DEFAULT_COMMERCE_DOC_VAR_NAME, "actionDefs"),
            ("line_attributes", DEFAULT_LINE_DOC_VAR_NAME, "attributes"),
            ("line_actions", DEFAULT_LINE_DOC_VAR_NAME, "actionDefs"),
        )
        results: dict[str, Any] = {}
        for index, (key, doc, resource) in enumerate(collections, start=1):
            report_tool_progress(
                float(index - 1),
                float(len(collections)),
                message=f"Syncing commerce {key}",
            )
            path = commerce_document_path(process, doc, resource)  # type: ignore[arg-type]
            extra_params: dict[str, Any] = {}
            if expand_all:
                extra_params["expand"] = "all*"
            fetch_result = iterate_collection(
                client,
                path,
                params=extra_params or None,
                page_size=100,
                max_items=10_000,
            )
            items = [i for i in fetch_result.items if isinstance(i, dict)]
            xlsx_bytes = build_records_workbook(items, sheet_title=key[:31])
            results[key] = persist_commerce_collection(
                client.profile,
                process_var_name=process,
                collection_key=key,
                items=items,
                xlsx_bytes=xlsx_bytes,
                source_tool="sync_commerce_metadata_local",
                filters={"expand_all": expand_all, "doc_var_name": doc},
            )
            results[key]["truncated"] = fetch_result.truncated
            results[key]["has_more"] = fetch_result.has_more
        report_tool_progress(1, 1, message="Commerce metadata sync complete")
        return {
            "domain": "commerce",
            "process_var_name": process,
            "collections": results,
        }

    sync_commerce_metadata_local.__doc__ = TOOL_CATALOG[
        "sync_commerce_metadata_local"
    ].description
    register_tool(mcp, sync_commerce_metadata_local, "sync_commerce_metadata_local")

    def sync_datatable_local(table_name: str | None = None) -> dict[str, Any]:
        name = table_name or client.profile.custom_data_table_name
        if not name:
            return build_tool_error(
                "VALIDATION_ERROR",
                "table_name is required (no CUSTOM_DATA_TABLE_NAME in profile)",
                hint="Set CUSTOM_DATA_TABLE_NAME in the profile .env or pass table_name.",
            )
        report_tool_progress(0, 1, message=f"Syncing datatable {name}")
        meta = client.get(f"/datatables/{name}")
        if not isinstance(meta, dict):
            meta = {"raw": meta}
        fetch_result = iterate_collection(
            client,
            f"/adminCustom{name}",
            page_size=100,
            max_items=50_000,
            on_progress=lambda count, message: report_tool_progress(
                float(count),
                50_000.0,
                message=message or f"Fetching rows ({count})",
            ),
        )
        rows = [r for r in fetch_result.items if isinstance(r, dict)]
        xlsx_bytes = build_records_workbook(rows, sheet_title="Rows")
        persisted = persist_datatable_snapshot(
            client.profile,
            table_name=name,
            meta=meta,
            rows=rows,
            xlsx_bytes=xlsx_bytes,
            source_tool="sync_datatable_local",
            extra={
                "truncated": fetch_result.truncated,
                "has_more": fetch_result.has_more,
            },
        )
        report_tool_progress(1, 1, message=f"Datatable {name} sync complete")
        return {
            "domain": "datatables",
            "table_name": name,
            "truncated": fetch_result.truncated,
            "has_more": fetch_result.has_more,
            **persisted,
        }

    sync_datatable_local.__doc__ = TOOL_CATALOG["sync_datatable_local"].description
    register_tool(mcp, sync_datatable_local, "sync_datatable_local")

    def sync_datatables_local(table_names: list[str] | None = None) -> dict[str, Any]:
        names = table_names or list(client.profile.custom_data_table_names)
        if not names:
            return build_tool_error(
                "VALIDATION_ERROR",
                "No table names provided and CUSTOM_DATA_TABLE_NAME* is empty.",
                hint="Pass table_names or set CUSTOM_DATA_TABLE_NAME in the profile .env.",
            )
        results: list[dict[str, Any]] = []
        for name in names:
            results.append(sync_datatable_local(table_name=name))
        return {
            "domain": "datatables",
            "count": len(results),
            "tables": results,
        }

    sync_datatables_local.__doc__ = TOOL_CATALOG["sync_datatables_local"].description
    register_tool(mcp, sync_datatables_local, "sync_datatables_local")
