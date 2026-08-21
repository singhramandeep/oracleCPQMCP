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
    )
    assert "offer_save_refined_prompt" in text
    assert "AUTO_SAVE_REFINED_PROMPT" in text
    assert "offer_use_local_data" in text
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
    )
    assert "save_refined_prompt" in text
    assert "do not ask" in text
    assert "LOCAL_DATA_POLICY=prefer" in text
    assert "output_format" in text


def test_build_instructions_never_local_data() -> None:
    text = build_server_instructions(
        refined_prompt=False,
        local_data_policy="never",
    )
    assert "LOCAL_DATA_POLICY=never" in text
    assert "offer_use_local_data" not in text
