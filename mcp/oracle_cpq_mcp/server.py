"""FastMCP server entrypoint."""

from __future__ import annotations

import logging
import os
import sys

from fastmcp import FastMCP

from oracle_cpq_mcp import __version__
from oracle_cpq_mcp.core.config import CPQProfile, connection_mode_message, load_profile
from oracle_cpq_mcp.core.cpq_client import CPQClient
from oracle_cpq_mcp.security.schema_integrity import verify_schema_integrity
from oracle_cpq_mcp.security.settings import load_security_settings
from oracle_cpq_mcp.prompts.instructions import build_server_instructions
from oracle_cpq_mcp.prompts.mcp_surface import register_saved_prompt_resources_and_prompts
from oracle_cpq_mcp.tools._register import configure_security
from oracle_cpq_mcp.tools.bml import register_bml_tools
from oracle_cpq_mcp.tools.commerce import register_commerce_tools
from oracle_cpq_mcp.tools.configuration import register_configuration_tools
from oracle_cpq_mcp.tools.datatables import register_datatable_tools
from oracle_cpq_mcp.tools.discovery import register_discovery_tools
from oracle_cpq_mcp.tools.groups import register_group_tools
from oracle_cpq_mcp.tools.local_data import register_local_data_tools
from oracle_cpq_mcp.tools.parts import register_parts_tools
from oracle_cpq_mcp.tools.performance import register_performance_tools
from oracle_cpq_mcp.tools.saved_prompts import register_saved_prompt_tools
from oracle_cpq_mcp.tools.tasks import register_tasks_tools
from oracle_cpq_mcp.tools.transactions import register_transaction_tools
from oracle_cpq_mcp.tools.users import register_user_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    stream=sys.stderr,
)


def _load_startup_profile() -> CPQProfile:
    settings = load_security_settings()
    verify_schema_integrity(enabled=settings.schema_integrity_enabled)
    profile = load_profile()
    configure_security(profile, settings)
    logging.getLogger(__name__).info("Oracle CPQ MCP server version %s", __version__)
    logging.getLogger(__name__).info(
        "Loaded profile %s (%s) env=%s rest=%s credentials=%d active_index=%d "
        "user=%s read_only=%s refined_prompt=%s auto_save_refined_prompt=%s "
        "local_data_policy=%s",
        profile.customer_id,
        profile.customer_name,
        profile.environment,
        profile.rest_version,
        len(profile.credentials),
        profile.credential_index,
        profile.username,
        profile.read_only,
        profile.refined_prompt,
        profile.auto_save_refined_prompt,
        profile.local_data_policy,
    )
    logging.getLogger(__name__).info(connection_mode_message(profile.read_only))
    return profile


_profile = _load_startup_profile()
SERVER_INSTRUCTIONS = build_server_instructions(
    refined_prompt=_profile.refined_prompt,
    auto_save_refined_prompt=_profile.auto_save_refined_prompt,
    local_data_policy=_profile.local_data_policy,
)

mcp = FastMCP(
    "Oracle CPQ",
    version=__version__,
    instructions=SERVER_INSTRUCTIONS,
)

_client = CPQClient(_profile)


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


register_user_tools(mcp, _client)
register_group_tools(mcp, _client)
register_datatable_tools(mcp, _client)
register_bml_tools(mcp, _client)
register_commerce_tools(mcp, _client)
register_transaction_tools(mcp, _client)
register_parts_tools(mcp, _client)
register_performance_tools(mcp, _client)
register_tasks_tools(mcp, _client)
register_configuration_tools(mcp, _client)
register_local_data_tools(mcp, _client)
register_discovery_tools(mcp)
register_saved_prompt_tools(mcp)
register_saved_prompt_resources_and_prompts(mcp)
_maybe_enable_tool_search()


def main() -> None:
    """Run the MCP server over stdio (default for Cursor)."""
    mcp.run()


if __name__ == "__main__":
    main()
