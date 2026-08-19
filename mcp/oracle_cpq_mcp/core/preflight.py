"""Safe execution preflight checks for state-changing MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from oracle_cpq_mcp.core.cpq_client import CPQClient, format_curl_command
from oracle_cpq_mcp.core.errors import CPQAPIError
from oracle_cpq_mcp.security.confirmation import issue_confirmation_token
from oracle_cpq_mcp.security.context import SecurityContext
from oracle_cpq_mcp.security.settings import SecuritySettings

PreflightStatus = Literal["preflight_ok", "preflight_failed"]
WriteAction = Literal["update", "create", "deploy"]

PREFLIGHT_NEXT_STEP = (
    "Ask the user to confirm this change, then call again with "
    "dry_run=false and the confirmation_token from this response."
)
CONFIRMATION_NEXT_STEP = (
    "Ask the user to confirm, then call again with dry_run=false and confirmation_token."
)
READ_ONLY_NEXT_STEP = (
    "Set READ_ONLY=false in the profile .env file to allow create/update/deploy operations."
)


def build_preflight_response(
    tool: str,
    *,
    action: WriteAction,
    status: PreflightStatus,
    message: str,
    would_execute: dict[str, Any],
    confirmation_prompt: str | None = None,
    preflight: dict[str, Any] | None = None,
    errors: list[str] | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a consistent dry-run preflight response envelope."""
    payload: dict[str, Any] = {
        "dry_run": True,
        "tool": tool,
        "action": action,
        "status": status,
        "message": message,
        "would_execute": would_execute,
        "next_step": PREFLIGHT_NEXT_STEP,
    }
    if status == "preflight_ok" and confirmation_prompt:
        payload["confirmation_prompt"] = confirmation_prompt
    if preflight is not None:
        payload["preflight"] = preflight
    if errors:
        payload["errors"] = errors
    if error is not None:
        payload["error"] = error
    return payload


def _preflight_api_failure(
    tool: str,
    *,
    action: WriteAction,
    message: str,
    would_execute: dict[str, Any],
    exc: CPQAPIError,
    preflight: dict[str, Any] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    """Build a preflight_failed response with nested structured error details."""
    return build_preflight_response(
        tool,
        action=action,
        status="preflight_failed",
        message=message,
        would_execute=would_execute,
        preflight=preflight,
        errors=errors or [str(exc)],
        error=exc.to_tool_error(),
    )


def build_confirmation_required_response(
    tool: str,
    *,
    action: WriteAction,
    message: str,
    confirmation_prompt: str,
    would_execute: dict[str, Any],
    preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a response when mutation was requested without user confirmation."""
    payload: dict[str, Any] = {
        "dry_run": False,
        "tool": tool,
        "action": action,
        "status": "confirmation_required",
        "message": message,
        "confirmation_prompt": confirmation_prompt,
        "would_execute": would_execute,
        "next_step": CONFIRMATION_NEXT_STEP,
    }
    if preflight is not None:
        payload["preflight"] = preflight
    return payload


def attach_confirmation_to_response(
    result: dict[str, Any],
    tool: str,
    arguments: dict[str, Any],
    *,
    context: SecurityContext,
    settings: SecuritySettings,
) -> dict[str, Any]:
    """Attach HMAC confirmation token to preflight_ok or confirmation_required responses."""
    if result.get("status") not in ("preflight_ok", "confirmation_required"):
        return result
    if settings.confirmation_secret is None:
        return result
    try:
        token_fields = issue_confirmation_token(
            tool, arguments, context=context, settings=settings
        )
    except Exception:
        return result
    enriched = dict(result)
    enriched.update(token_fields)
    return enriched


def build_read_only_blocked_response(tool: str, *, action: WriteAction) -> dict[str, Any]:
    """Build a response when profile READ_ONLY blocks a mutating operation."""
    action_label = action.upper()
    return {
        "dry_run": False,
        "tool": tool,
        "action": action,
        "status": "read_only_blocked",
        "read_only": True,
        "message": (
            f"Profile READ_ONLY=true — this {action_label} operation is blocked. "
            "No create/update/patch/delete API calls were made."
        ),
        "next_step": READ_ONLY_NEXT_STEP,
    }


def _annotate_read_only_preflight(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("status") != "preflight_ok":
        return result
    annotated = dict(result)
    annotated["read_only"] = True
    annotated["execution_blocked"] = True
    annotated["message"] = (
        f"{result['message']} Profile READ_ONLY=true — execution is blocked."
    )
    if confirmation_prompt := result.get("confirmation_prompt"):
        annotated["confirmation_prompt"] = (
            f"{confirmation_prompt} Profile READ_ONLY=true — execution is blocked."
        )
    annotated["next_step"] = READ_ONLY_NEXT_STEP
    return annotated


def resolve_write_execution(
    *,
    read_only: bool,
    dry_run: bool,
    confirmation_token: str | None,
    tool: str,
    action: WriteAction,
    preflight_fn: Callable[[], dict[str, Any]],
    execute_fn: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Route write tool calls through preflight, confirmation, or execution."""
    if read_only and not dry_run:
        return build_read_only_blocked_response(tool, action=action)
    if dry_run:
        result = preflight_fn()
        if read_only:
            return _annotate_read_only_preflight(result)
        return result
    preview = preflight_fn()
    if preview.get("status") != "preflight_ok":
        return preview
    if not confirmation_token:
        return build_confirmation_required_response(
            preview["tool"],
            action=preview["action"],
            message=preview["message"],
            confirmation_prompt=preview["confirmation_prompt"],
            would_execute=preview["would_execute"],
            preflight=preview.get("preflight"),
        )
    return execute_fn()


def _would_execute(
    client: CPQClient,
    *,
    method: str,
    path: str,
    body: Any = None,
) -> dict[str, Any]:
    url = f"{client.profile.rest_base}{path}"
    return {
        "method": method.upper(),
        "path": path,
        "body": body,
        "curl": format_curl_command(
            method,
            url,
            username=client.profile.username,
            json_body=body,
        ),
    }


def run_update_user_preflight(
    client: CPQClient,
    party_number: str,
    patch_body: dict[str, Any],
) -> dict[str, Any]:
    """Validate update_user inputs and confirm the target user exists."""
    errors: list[str] = []
    if not party_number or not party_number.strip():
        errors.append("party_number is required")
    if not isinstance(patch_body, dict) or not patch_body:
        errors.append("patch_body must be a non-empty object")

    path = f"/users/{party_number.strip()}" if party_number else "/users/"
    would = _would_execute(client, method="PATCH", path=path, body=patch_body)

    if errors:
        return build_preflight_response(
            "update_user",
            action="update",
            status="preflight_failed",
            message="update_user preflight failed",
            would_execute=would,
            errors=errors,
        )

    try:
        current_user = client.get(path)
    except CPQAPIError as exc:
        return _preflight_api_failure(
            "update_user",
            action="update",
            message=f"User '{party_number}' not found or not accessible",
            would_execute=would,
            exc=exc,
            preflight={"party_number": party_number},
        )

    user_label = current_user.get("login") or party_number
    confirmation_prompt = f"This will UPDATE user '{user_label}' in CPQ. Confirm to proceed."
    return build_preflight_response(
        "update_user",
        action="update",
        status="preflight_ok",
        message=f"This will UPDATE user '{user_label}' in CPQ.",
        confirmation_prompt=confirmation_prompt,
        would_execute=would,
        preflight={
            "party_number": party_number,
            "current_user": current_user,
            "fields_to_change": sorted(patch_body.keys()),
        },
    )


def run_create_group_preflight(
    client: CPQClient,
    group_body: dict[str, Any],
) -> dict[str, Any]:
    """Validate create_group inputs and confirm the group name is not already taken."""
    company = client.profile.company_login_name
    path = f"/companies/{company}/groups"
    would = _would_execute(client, method="POST", path=path, body=group_body)

    errors: list[str] = []
    if not isinstance(group_body, dict) or not group_body:
        errors.append("group_body must be a non-empty object")
    variable_name = group_body.get("variableName") if isinstance(group_body, dict) else None
    if isinstance(group_body, dict) and group_body and not variable_name:
        errors.append("group_body must include variableName")

    if errors:
        return build_preflight_response(
            "create_group",
            action="create",
            status="preflight_failed",
            message="create_group preflight failed",
            would_execute=would,
            errors=errors,
        )

    assert variable_name is not None
    check_path = f"/companies/{company}/groups/{variable_name}"
    try:
        existing = client.get(check_path)
        return build_preflight_response(
            "create_group",
            action="create",
            status="preflight_failed",
            message=f"Group '{variable_name}' already exists",
            would_execute=would,
            preflight={"variableName": variable_name, "existing_group": existing},
            errors=[f"Group '{variable_name}' already exists for company '{company}'"],
        )
    except CPQAPIError as exc:
        if exc.status_code != 404:
            return _preflight_api_failure(
                "create_group",
                action="create",
                message=f"Could not verify group name '{variable_name}'",
                would_execute=would,
                exc=exc,
                preflight={"variableName": variable_name},
            )

    confirmation_prompt = f"This will CREATE group '{variable_name}' in CPQ. Confirm to proceed."
    return build_preflight_response(
        "create_group",
        action="create",
        status="preflight_ok",
        message=f"This will CREATE group '{variable_name}' in CPQ.",
        confirmation_prompt=confirmation_prompt,
        would_execute=would,
        preflight={
            "company": company,
            "variableName": variable_name,
            "group_body": group_body,
        },
    )


def run_deploy_datatables_preflight(
    client: CPQClient,
    table_names: list[str],
) -> dict[str, Any]:
    """Validate deploy_datatables inputs and confirm each table exists."""
    body = {"selections": table_names}
    would = _would_execute(
        client,
        method="POST",
        path="/datatables/actions/deploy",
        body=body,
    )

    errors: list[str] = []
    if not table_names:
        errors.append("table_names must be a non-empty list")
    else:
        for index, name in enumerate(table_names):
            if not isinstance(name, str) or not name.strip():
                errors.append(f"table_names[{index}] must be a non-empty string")

    if errors:
        return build_preflight_response(
            "deploy_datatables",
            action="deploy",
            status="preflight_failed",
            message="deploy_datatables preflight failed",
            would_execute=would,
            errors=errors,
        )

    tables: list[dict[str, Any]] = []
    for name in table_names:
        try:
            metadata = client.get(f"/datatables/{name}")
            tables.append({"name": name, "found": True, "metadata": metadata})
        except CPQAPIError as exc:
            return _preflight_api_failure(
                "deploy_datatables",
                action="deploy",
                message=f"Table '{name}' not found or not accessible",
                would_execute=would,
                exc=exc,
                preflight={"tables_checked": tables, "failed_table": name},
            )

    count = len(table_names)
    table_label = f"{count} data table(s)"
    confirmation_prompt = (
        f"This will DEPLOY {table_label} to live CPQ configuration. Confirm to proceed."
    )
    return build_preflight_response(
        "deploy_datatables",
        action="deploy",
        status="preflight_ok",
        message=f"This will DEPLOY {table_label} to live CPQ configuration.",
        confirmation_prompt=confirmation_prompt,
        would_execute=would,
        preflight={
            "table_names": table_names,
            "tables": tables,
        },
    )
