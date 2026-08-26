"""Tests for MCP server instruction composition."""

from __future__ import annotations

from oracle_cpq_mcp.prompts.instructions import build_server_instructions


def test_build_instructions_refined_off() -> None:
    text = build_server_instructions(
        refined_prompt=False,
        auto_save_refined_prompt=False,
        local_data_policy="ask",
    )
    assert "Refined prompt" not in text
    assert "start_prompt_picker" in text
    assert "OracleCPQ_SavedPrompts" in text
    assert "list_local_data" in text
    assert "offer_use_local_data" in text


def test_build_instructions_ask_mode() -> None:
    text = build_server_instructions(
        refined_prompt=True,
        auto_save_refined_prompt=False,
        local_data_policy="ask",
        post_response_export="ask",
    )
    assert "offer_save_refined_prompt" in text
    assert "AUTO_SAVE_REFINED_PROMPT" in text
    assert "offer_use_local_data" in text
    assert "offer_export_response" in text
    assert "POST_RESPONSE_EXPORT=ask" in text
    assert "Output format" in text
    assert "Cached data" in text
    assert "output_format" in text
    assert "Skip the entire section if no Oracle CPQ MCP tools" not in text
    assert "local file read only" in text


def test_build_instructions_auto_save_mode() -> None:
    text = build_server_instructions(
        refined_prompt=True,
        auto_save_refined_prompt=True,
        local_data_policy="prefer",
        post_response_export="always_excel",
    )
    assert "save_refined_prompt" in text
    assert "do not ask" in text
    assert "LOCAL_DATA_POLICY=prefer" in text
    assert "POST_RESPONSE_EXPORT=always_excel" in text
    assert "export_response_excel" in text
    assert "output_format" in text


def test_build_instructions_never_local_data() -> None:
    text = build_server_instructions(
        refined_prompt=False,
        local_data_policy="never",
        post_response_export="never",
    )
    assert "LOCAL_DATA_POLICY=never" in text
    assert "offer_use_local_data" not in text
    assert "POST_RESPONSE_EXPORT=never" in text
    assert "offer_export_response" not in text


def test_build_instructions_includes_knowledge_and_aliases() -> None:
    text = build_server_instructions(
        refined_prompt=False,
        local_data_policy="ask",
        shared_knowledge="# Shared\nAlways confirm writes.",
        customer_knowledge="# Customer\nUse ModelMaster carefully.",
        commerce_process_aliases={"base commerce process": "oraclecpqo"},
        custom_data_table_aliases={"model master": "ModelMaster"},
    )
    assert "## Shared knowledge" in text
    assert "Always confirm writes." in text
    assert "## Customer knowledge" in text
    assert "Use ModelMaster carefully." in text
    assert "## Property aliases" in text
    assert 'process_var_name=oraclecpqo' in text
    assert 'table_name=ModelMaster' in text


def test_build_instructions_missing_customer_knowledge_ok() -> None:
    text = build_server_instructions(
        refined_prompt=False,
        shared_knowledge="base only",
        customer_knowledge="",
        commerce_process_aliases={},
    )
    assert "base only" in text
    assert "## Customer knowledge" not in text
    assert "## Property aliases" not in text
