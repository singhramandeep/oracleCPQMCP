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
    assert "Document templates" in text
    assert ".config/template" in text
    assert "AGENTS.md" in text
    assert "ALWAYS clone the branded package" in text
    assert "Heading 1 / Heading 2 / Heading 3" in text
    assert "open_pptx_presentation" in text
    assert "Profile credentials (never edit)" in text
    assert "Never create, edit, delete, reformat, quote, or rewrite username / password" in text
    assert "Live CPQ access must go only through Oracle CPQ MCP tools" in text
    assert "Treat .config/template/ as read-only" in text
    assert "tmp/{profile}/{env}/" in text
    assert "Scratch files" in text
    assert "1–3 Mermaid diagrams" in text
    assert "expected, not merely optional" in text
    assert "without waiting for the user to ask" in text or "do not wait for the user to ask" in text
    assert "## / ###" in text or "## / bullets" in text
    assert "npm i -g @mermaid-js/mermaid-cli" in text
    assert "Kroki/mermaid.ink" in text


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
    assert "1–3 Mermaid diagrams" in text
    assert "diagrams [{title, mermaid?, image_path?, caption?}]" in text
    assert "without waiting for the user to ask" in text
    assert "never Kroki/mermaid.ink" in text
    assert "Output format" in text
    assert "Cached data" in text
    assert "output_format" in text
    assert "Refined prompt gate" in text
    assert "When the gate is NO" in text
    assert "none (local file read only)" in text
    assert "YES-gate site/cache data" in text
    assert "Only when the refined-prompt gate is YES" in text
    assert "Turn metrics" in text
    assert "Elapsed" in text
    assert "Tokens" in text
    assert "not available" in text
    assert "Document templates" in text
    assert ".config/template" in text
    assert "ensure_prompt_studio" in text
    assert "Prompt Studio (YES-gate only)" in text


def test_build_instructions_includes_prompt_studio_when_refined_off() -> None:
    text = build_server_instructions(
        refined_prompt=False,
        local_data_policy="ask",
    )
    assert "ensure_prompt_studio" in text
    assert "Refined prompt" not in text


def test_build_instructions_auto_save_mode() -> None:
    text = build_server_instructions(
        refined_prompt=True,
        auto_save_refined_prompt=True,
        local_data_policy="prefer",
        post_response_export="always_excel",
    )
    assert "save_refined_prompt" in text
    assert "do not ask" in text
    assert "Only when the refined-prompt gate is YES" in text
    assert "When the gate is NO, do not call save_refined_prompt" in text
    assert "LOCAL_DATA_POLICY=prefer" in text
    assert "POST_RESPONSE_EXPORT=always_excel" in text
    assert "export_response_excel" in text
    assert "output_format" in text
    assert "refined-prompt gate is NO" in text

def test_build_instructions_never_local_data() -> None:
    text = build_server_instructions(
        refined_prompt=False,
        local_data_policy="never",
        post_response_export="never",
    )
    assert "LOCAL_DATA_POLICY=never" in text
    assert "LOCAL_DATA_POLICY=ask" not in text
    assert "when a snapshot exists, call offer_use_local_data" not in text
    assert "POST_RESPONSE_EXPORT=never" in text
    assert "POST_RESPONSE_EXPORT=ask" not in text
    assert "call offer_export_response (omit choice)" not in text


def test_build_instructions_includes_knowledge_and_aliases() -> None:
    text = build_server_instructions(
        refined_prompt=False,
        local_data_policy="ask",
        shared_knowledge="# Shared\nAlways confirm writes.",
        customer_knowledge="# Customer\nUse ModelMaster carefully.",
        commerce_process_aliases={"base commerce process": "oraclecpqo"},
        custom_data_table_aliases={"model master": "ModelMaster"},
        product_family_aliases={"laptop family": "laptop"},
        product_line_aliases={"hp line": "hp"},
        product_model_aliases={"elite 840": "elite840"},
    )
    assert "## Shared knowledge" in text
    assert "Always confirm writes." in text
    assert "## Customer knowledge" in text
    assert "Use ModelMaster carefully." in text
    assert "## Property aliases" in text
    assert 'process_var_name=oraclecpqo' in text
    assert 'table_name=ModelMaster' in text
    assert 'prod_fam_var_name=laptop' in text
    assert 'product_line_var_name=hp' in text
    assert 'model_var_name=elite840' in text


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
