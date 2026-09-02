"""MCP tools for Oracle CPQ BML APIs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastmcp.utilities.types import File

from oracle_cpq_mcp.core.bml_fetchers import (
    bml_export_filename,
    fetch_all_util_library_code,
)
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.core.local_data import (
    persist_bml_functions_snapshot,
    persist_bml_zip_snapshot,
    profile_env_root,
)
from oracle_cpq_mcp.core.local_jobs import start_background_job, update_job
from oracle_cpq_mcp.core.pagination import build_page_params, enrich_pagination_hint
from oracle_cpq_mcp.core.preflight import (
    resolve_write_execution,
    run_export_bml_library_preflight,
)
from oracle_cpq_mcp.core.progress import report_tool_progress
from oracle_cpq_mcp.core.responses import build_attachment_lead_envelope
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.tools._register import register_tool

BmlDelivery = Literal["zip", "json"]


def _search_bml_tree(
    root: Path,
    query: str,
    *,
    case_insensitive: bool,
    max_matches: int,
) -> list[dict[str, Any]]:
    needle = query.lower() if case_insensitive else query
    matches: list[dict[str, Any]] = []
    if not root.is_dir() or max_matches <= 0:
        return matches
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".bml", ".bmlt", ".txt", ".json"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hay = text.lower() if case_insensitive else text
        if needle not in hay:
            continue
        line_no = 0
        snippet = ""
        for idx, line in enumerate(text.splitlines(), start=1):
            cmp_line = line.lower() if case_insensitive else line
            if needle in cmp_line:
                line_no = idx
                snippet = line.strip()[:240]
                break
        rel = str(path.relative_to(root)).replace("\\", "/")
        matches.append(
            {
                "path": rel,
                "absolute_path": str(path.resolve()),
                "line": line_no or None,
                "snippet": snippet,
            }
        )
        if len(matches) >= max_matches:
            break
    return matches


def register_bml_tools(mcp: Any, client: CPQClient) -> None:
    """Register BML tools on the FastMCP instance."""

    def get_all_bml_code(delivery: BmlDelivery = "zip") -> list[str | File] | dict[str, Any]:
        if delivery == "zip":
            report_tool_progress(0, 1, message="Downloading BML/BMLT site export")
            zip_bytes = client.get_bytes("/adminMeta")
            report_tool_progress(1, 1, message="BML export download complete")
            filename = bml_export_filename(client.profile)
            try:
                local = persist_bml_zip_snapshot(
                    client.profile,
                    zip_bytes,
                    source_tool="get_all_bml_code",
                    filename=filename,
                    filters={"delivery": "zip"},
                )
            except OSError as exc:
                local = {"error": str(exc)}
            summary = (
                f"Downloaded all Commerce BML and BMLT files from "
                f"{client.profile.customer_name} ({client.profile.environment}) "
                f"to {filename} and extracted the site tree under "
                f"data/{client.profile.customer_id}/{client.profile.environment}/bml/site/. "
                f"Equivalent to cpq-toolkit pull. "
                f"For non-blocking export use start_bml_site_export + get_local_job."
            )
            return [
                build_attachment_lead_envelope(
                    "get_all_bml_code",
                    message=summary,
                    filename=filename,
                    extra={"delivery": "zip", "local_snapshot": local},
                ),
                File(
                    data=zip_bytes,
                    format="zip",
                    name=filename,
                ),
            ]

        functions, truncated, has_more = fetch_all_util_library_code(client)
        try:
            local = persist_bml_functions_snapshot(
                client.profile,
                functions,
                source_tool="get_all_bml_code",
                filters={"delivery": "json"},
                extra={"truncated": truncated, "has_more": has_more},
            )
        except OSError as exc:
            local = {"error": str(exc)}
        return {
            "delivery": "json",
            "customer": client.profile.customer_name,
            "environment": client.profile.environment,
            "utilLibraryFunctionCount": len(functions),
            "utilLibraryFunctions": functions,
            "truncated": truncated,
            "has_more": has_more,
            "local_snapshot": local,
            "note": (
                "JSON delivery returns util library scriptText only. "
                "Use delivery='zip' or start_bml_site_export for the full Commerce "
                "BML/BMLT site export. "
                "Per-function .bml/.json files were written under data/ when persist succeeded."
            ),
        }

    get_all_bml_code.__doc__ = TOOL_CATALOG["get_all_bml_code"].description
    register_tool(mcp, get_all_bml_code, "get_all_bml_code")

    def start_bml_site_export() -> dict[str, Any]:
        profile = client.profile

        def _worker(job_id: str) -> None:
            job_client = CPQClient(profile, timeout=profile.http_timeout)
            zip_bytes = job_client.get_bytes("/adminMeta")
            filename = bml_export_filename(profile)
            local = persist_bml_zip_snapshot(
                profile,
                zip_bytes,
                source_tool="start_bml_site_export",
                filename=filename,
                filters={"delivery": "zip", "async": True},
            )
            update_job(
                profile,
                job_id,
                status="succeeded",
                message="BML site export complete",
                result={
                    "filename": filename,
                    "local_snapshot": local,
                    "hint": (
                        "Search with search_local_bml or browse "
                        f"data/{profile.customer_id}/{profile.environment}/bml/site/"
                    ),
                },
                error=None,
            )

        record = start_background_job(
            profile,
            kind="bml_site_export",
            message="Queued BML/BMLT site export (GET /adminMeta)",
            worker=_worker,
        )
        return {
            "job_id": record["job_id"],
            "status": record["status"],
            "kind": record["kind"],
            "message": record["message"],
            "poll_with": "get_local_job",
            "hint": (
                "Call get_local_job(job_id=...) until status is succeeded or failed. "
                "This avoids blocking the MCP tool call for multi-minute downloads."
            ),
        }

    start_bml_site_export.__doc__ = TOOL_CATALOG["start_bml_site_export"].description
    register_tool(mcp, start_bml_site_export, "start_bml_site_export")

    def search_local_bml(
        query: str,
        max_matches: int = 50,
        case_insensitive: bool = True,
        include_functions: bool = True,
    ) -> dict[str, Any]:
        root = profile_env_root(client.profile) / "bml"
        site = root / "site"
        functions_dir = root / "functions"
        if not site.is_dir() and not (include_functions and functions_dir.is_dir()):
            return {
                "status": "error",
                "code": "NOT_FOUND",
                "message": "No local BML extract found under data/.../bml/site/",
                "hint": (
                    "Run start_bml_site_export (then get_local_job) or "
                    "get_all_bml_code(delivery=zip) first."
                ),
            }
        matches = _search_bml_tree(
            site,
            query,
            case_insensitive=case_insensitive,
            max_matches=max_matches,
        )
        if include_functions and len(matches) < max_matches and functions_dir.is_dir():
            extra = _search_bml_tree(
                functions_dir,
                query,
                case_insensitive=case_insensitive,
                max_matches=max_matches - len(matches),
            )
            for item in extra:
                item["path"] = f"functions/{item['path']}"
            matches.extend(extra)
        return {
            "query": query,
            "match_count": len(matches),
            "truncated": len(matches) >= max_matches,
            "matches": matches,
            "search_roots": {
                "site": str(site) if site.is_dir() else None,
                "functions": str(functions_dir)
                if include_functions and functions_dir.is_dir()
                else None,
            },
        }

    search_local_bml.__doc__ = TOOL_CATALOG["search_local_bml"].description
    register_tool(mcp, search_local_bml, "search_local_bml")

    def get_bml_function(function_id: str) -> dict[str, Any]:
        return client.get(f"/bml/library/functions/{function_id}")

    get_bml_function.__doc__ = TOOL_CATALOG["get_bml_function"].description
    register_tool(mcp, get_bml_function, "get_bml_function")

    def search_bml_scripts(
        q_expr: str | None = None,
        limit: int = 100,
        offset: int = 0,
        orderby: str | None = None,
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        extra: dict[str, Any] = {}
        if q_expr:
            extra["q"] = q_expr
        if orderby:
            extra["orderby"] = orderby
        if fields:
            extra["fields"] = ",".join(fields)
        params = build_page_params(limit, offset, extra=extra or None)
        response = client.get("/bml/scripts", params=params)
        return enrich_pagination_hint(response, "search_bml_scripts")

    search_bml_scripts.__doc__ = TOOL_CATALOG["search_bml_scripts"].description
    register_tool(mcp, search_bml_scripts, "search_bml_scripts")

    def list_bml_common_functions(
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params = build_page_params(limit, offset)
        response = client.get("/bml/common/functions", params=params)
        return enrich_pagination_hint(response, "list_bml_common_functions")

    list_bml_common_functions.__doc__ = TOOL_CATALOG["list_bml_common_functions"].description
    register_tool(mcp, list_bml_common_functions, "list_bml_common_functions")

    def get_bml_common_function(name: str) -> dict[str, Any]:
        return client.get(f"/bml/common/functions/{name}")

    get_bml_common_function.__doc__ = TOOL_CATALOG["get_bml_common_function"].description
    register_tool(mcp, get_bml_common_function, "get_bml_common_function")

    def list_bml_library_folders(
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params = build_page_params(limit, offset)
        response = client.get("/bml/library/folders", params=params)
        return enrich_pagination_hint(response, "list_bml_library_folders")

    list_bml_library_folders.__doc__ = TOOL_CATALOG["list_bml_library_folders"].description
    register_tool(mcp, list_bml_library_folders, "list_bml_library_folders")

    def get_bml_dependent_attributes(body: dict[str, Any] | None = None) -> dict[str, Any]:
        return client.post(
            "/bml/library/functions/actions/dependentAttributes",
            json_body=body or {},
        )

    get_bml_dependent_attributes.__doc__ = TOOL_CATALOG[
        "get_bml_dependent_attributes"
    ].description
    register_tool(mcp, get_bml_dependent_attributes, "get_bml_dependent_attributes")

    def export_bml_library_functions(
        body: dict[str, Any] | None = None,
        dry_run: bool = True,
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        payload = body or {}
        return resolve_write_execution(
            read_only=client.profile.read_only,
            dry_run=dry_run,
            confirmation_token=confirmation_token,
            tool="export_bml_library_functions",
            action="export",
            preflight_fn=lambda: run_export_bml_library_preflight(client, payload),
            execute_fn=lambda: client.post(
                "/bml/library/functions/actions/export",
                json_body=payload,
            ),
        )

    export_bml_library_functions.__doc__ = TOOL_CATALOG[
        "export_bml_library_functions"
    ].description
    register_tool(mcp, export_bml_library_functions, "export_bml_library_functions")
