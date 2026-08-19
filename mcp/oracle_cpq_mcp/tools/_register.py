"""Helper to register MCP tools with catalog metadata and security pipeline."""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar, get_origin, get_type_hints

from oracle_cpq_mcp.core.config import CPQProfile
from oracle_cpq_mcp.core.errors import CPQAPIError, exception_to_tool_error
from oracle_cpq_mcp.core.output_validation import (
    OutputValidationError,
    build_output_validation_error,
    validate_tool_output,
)
from oracle_cpq_mcp.core.preflight import attach_confirmation_to_response
from oracle_cpq_mcp.core.responses import wrap_tool_success
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG, ToolSpec, mcp_tool_kwargs
from oracle_cpq_mcp.security.audit import emit_audit_event
from oracle_cpq_mcp.security.authorization import authorize_tool
from oracle_cpq_mcp.security.confirmation import validate_confirmation_token
from oracle_cpq_mcp.security.context import (
    SecurityContext,
    build_security_context,
    get_security_context,
    increment_session_tool_calls,
    set_security_context,
)
from oracle_cpq_mcp.security.exceptions import SecurityError
from oracle_cpq_mcp.security.policy import ToolPolicy
from oracle_cpq_mcp.security.rate_limit import check_rate_limit
from oracle_cpq_mcp.security.replay import check_replay
from oracle_cpq_mcp.security.sanitization import sanitize_tool_output
from oracle_cpq_mcp.security.settings import SecuritySettings, load_security_settings
from oracle_cpq_mcp.security.validation import validate_tool_input

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

_profile: CPQProfile | None = None
_settings: SecuritySettings = load_security_settings()


def configure_security(profile: CPQProfile, settings: SecuritySettings | None = None) -> None:
    """Bind active profile and security settings for tool registration."""
    global _profile, _settings
    _profile = profile
    if settings is not None:
        _settings = settings


def _returns_list(fn: Callable[..., Any]) -> bool:
    try:
        return_type = get_type_hints(fn).get("return")
    except (NameError, TypeError, AttributeError):
        return_type = fn.__annotations__.get("return")
    if return_type is None:
        return False
    return get_origin(return_type) is list


def _wrap_if_list_return(fn: Callable[..., Any], payload: dict[str, Any]) -> Any:
    if _returns_list(fn):
        return [payload]
    return payload


def _ensure_write_token_valid(
    tool_name: str,
    validated: dict[str, Any],
    *,
    context: SecurityContext,
    policy: ToolPolicy,
) -> None:
    if not policy.confirmation_required:
        return
    if validated.get("dry_run", True):
        return
    validate_confirmation_token(
        tool_name,
        validated,
        validated.get("confirmation_token"),
        context=context,
        settings=_settings,
    )
    check_replay(tool_name, validated, context=context, settings=_settings)


def register_tool(mcp: Any, fn: F, spec_name: str) -> F:
    """Register *fn* with security pipeline and safe error wrapping."""
    if spec_name not in TOOL_CATALOG:
        raise KeyError(f"Unknown tool spec: {spec_name}")
    spec: ToolSpec = TOOL_CATALOG[spec_name]

    @functools.wraps(fn)
    def safe_fn(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        ctx = build_security_context(_profile) if _profile else get_security_context()
        if ctx is None and _profile:
            ctx = build_security_context(_profile)
        if ctx is None:
            raise RuntimeError("Security context not configured")

        set_security_context(ctx)
        call_count = increment_session_tool_calls()
        if call_count > _settings.max_tool_calls_per_session:
            err = {
                "status": "error",
                "code": "POLICY_VIOLATION",
                "message": "Maximum tool calls per session exceeded.",
                "hint": "Start a new session or increase CPQ_MAX_TOOL_CALLS.",
            }
            return _wrap_if_list_return(fn, err)

        authorization_result = "denied"
        policy_result = "denied"
        confirmation_required = spec.operation == "write"
        confirmation_result: str | None = None
        execution_result = "error"
        error_code: str | None = None
        validated: dict[str, Any] = {}

        try:
            policy = authorize_tool(
                spec_name, context=ctx, settings=_settings, kwargs=kwargs
            )
            authorization_result = "allowed"
            policy_result = "allowed"

            validated = validate_tool_input(spec_name, kwargs)
            check_rate_limit(
                spec_name,
                customer_id=ctx.customer_id,
                policy=policy,
                settings=_settings,
            )

            _ensure_write_token_valid(spec_name, validated, context=ctx, policy=policy)
            if confirmation_required and not validated.get("dry_run", True):
                confirmation_result = "valid"

            result = fn(*args, **validated)
            if isinstance(result, dict) and result.get("status") in (
                "preflight_ok",
                "confirmation_required",
            ):
                result = attach_confirmation_to_response(
                    result, spec_name, validated, context=ctx, settings=_settings
                )

            result = sanitize_tool_output(result, max_bytes=_settings.max_response_bytes)
            execution_result = "success"
            if isinstance(result, dict) and result.get("status") == "error":
                execution_result = "error"
                error_code = result.get("code")
            elif isinstance(result, list) and result and isinstance(result[0], dict):
                if result[0].get("status") == "error":
                    execution_result = "error"
                    error_code = result[0].get("code")
            else:
                result = wrap_tool_success(spec_name, result)

            try:
                validate_tool_output(spec_name, result)
            except OutputValidationError:
                logger.warning("Output validation failed for %s", spec_name, exc_info=True)
                error_code = "INTERNAL_ERROR"
                execution_result = "error"
                return _wrap_if_list_return(fn, build_output_validation_error())

            return result

        except SecurityError as exc:
            error_code = exc.code
            execution_result = "denied"
            return _wrap_if_list_return(fn, exc.to_tool_error())
        except CPQAPIError as exc:
            error_code = exc.code if hasattr(exc, "code") else "CPQ_API_ERROR"
            return _wrap_if_list_return(fn, exc.to_tool_error())
        except (ValueError, TypeError) as exc:
            error_code = "VALIDATION_ERROR"
            return _wrap_if_list_return(fn, exception_to_tool_error(exc))
        except Exception as exc:
            logger.exception("Unhandled error in tool %s", spec_name)
            error_code = "INTERNAL_ERROR"
            return _wrap_if_list_return(fn, exception_to_tool_error(exc))
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            policy_obj = TOOL_CATALOG.get(spec_name)
            if policy_obj and ctx:
                from oracle_cpq_mcp.security.policy import get_tool_policy

                tp = get_tool_policy(spec_name)
                if tp:
                    emit_audit_event(
                        context=ctx,
                        tool_name=spec_name,
                        policy=tp,
                        settings=_settings,
                        kwargs=validated or kwargs,
                        authorization_result=authorization_result,
                        policy_result=policy_result,
                        confirmation_required=confirmation_required,
                        confirmation_result=confirmation_result,
                        execution_result=execution_result,
                        error_code=error_code,
                        duration_ms=duration_ms,
                    )

    return mcp.tool(**mcp_tool_kwargs(spec))(safe_fn)
