"""FastMCP server entrypoint."""

from __future__ import annotations

import logging
import os
import sys

from fastmcp import FastMCP

from oracle_cpq_mcp.core.config import connection_mode_message, load_profile
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.security.schema_integrity import verify_schema_integrity
from oracle_cpq_mcp.security.settings import load_security_settings
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.bml import register_bml_tools
from oracle_cpq_mcp.tools.commerce import register_commerce_tools
from oracle_cpq_mcp.tools.datatables import register_datatable_tools
from oracle_cpq_mcp.tools.discovery import register_discovery_tools
from oracle_cpq_mcp.tools.groups import register_group_tools
from oracle_cpq_mcp.tools.users import register_user_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    stream=sys.stderr,
)

mcp = FastMCP(
    "Oracle CPQ",
    instructions=(
        "Oracle CPQ MCP server for Users, Groups, Data Tables, BML, and Commerce metadata. "
        "All calls use the active customer profile from CPQ_CUSTOMER_PROFILE "
        "and environment from CPQ_ENVIRONMENT or the profile default. "
        "Use discover_tools to find tools by domain (users/groups/datatables/bml/commerce) or "
        "operation (read/write). Read-only tools are safe for exploration; write tools "
        "(update_user, create_group, deploy_datatables) default to dry_run=true preflight "
        "mode and require a server-issued confirmation_token before mutating CPQ data. "
        "Never execute writes without user approval and a valid confirmation_token. "
        "When profile READ_ONLY=true (default), all create/update/deploy operations are blocked. "
        "On failure, tools return structured errors: {status: 'error', code, message, hint, details}."
    ),
)


def _build_client() -> CPQClient:
    settings = load_security_settings()
    verify_schema_integrity(enabled=settings.schema_integrity_enabled)
    profile = load_profile()
    configure_security(profile, settings)
    logging.getLogger(__name__).info(
        "Loaded profile %s (%s) env=%s rest=%s credentials=%d active_index=%d user=%s read_only=%s",
        profile.customer_id,
        profile.customer_name,
        profile.environment,
        profile.rest_version,
        len(profile.credentials),
        profile.credential_index,
        profile.username,
        profile.read_only,
    )
    logging.getLogger(__name__).info(connection_mode_message(profile.read_only))
    return CPQClient(profile)


def _maybe_enable_tool_search() -> None:
    if os.environ.get("CPQ_TOOL_SEARCH", "").lower() not in ("1", "true", "yes"):
        return
    from fastmcp.server.transforms.search import BM25SearchTransform

    mcp.add_transform(
        BM25SearchTransform(
            always_visible=["discover_tools"],
            max_results=5,
        )
    )
    logging.getLogger(__name__).info(
        "CPQ_TOOL_SEARCH enabled — list_tools returns discover_tools, search_tools, call_tool"
    )


_client = _build_client()
register_user_tools(mcp, _client)
register_group_tools(mcp, _client)
register_datatable_tools(mcp, _client)
register_bml_tools(mcp, _client)
register_commerce_tools(mcp, _client)
register_discovery_tools(mcp)
_maybe_enable_tool_search()


def main() -> None:
    """Run the MCP server over stdio (default for Cursor)."""
    mcp.run()


if __name__ == "__main__":
    main()
