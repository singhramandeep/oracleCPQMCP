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
    assert "Profile credentials (never edit)" in text
    assert "username" in text and "password" in text
    assert "Live CPQ only via Oracle CPQ MCP tools" in text
    assert "tmp/{profile}/{env}/" in text
    assert "Scratch files" in text
    assert "append_customer_knowledge" in text
    assert "get_customer_knowledge" in text
    assert "1–3 Mermaid" in text
    assert "Kroki/mermaid.ink" in text
    assert "dry_run" in text
    assert "confirmation_token" in text


def test_build_instructions_ask_mode() -> None:
    text = build_server_instructions(
        refined_prompt=True,
        auto_save_refined_prompt=False,
        local_data_policy="ask",
        post_response_export="ask",
    )
    assert "offer_save_refined_prompt" in text
    assert "offer_use_local_data" in text
    assert "offer_export_response" in text
    assert "POST_RESPONSE_EXPORT=ask" in text
    assert "1–3 Mermaid" in text
    assert "Output format" in text
    assert "Cached data" in text
    assert "output_format" in text
    assert "Refined prompt gate" in text
    assert "Search / Adaptive Search" in text
    assert "{{entity}}" in text or "{{q}}" in text
    assert "Turn metrics" in text
    assert "Elapsed" in text
    assert "Do not include token counts" in text
    assert "**Tokens:**" not in text
    assert "Document templates" in text
    assert "ensure_prompt_studio" in text
    # Compression target: full refined instructions under ~2000 tokens (~8000 chars)
    assert len(text) < 9500


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
    assert "do not ask" in text or "AUTO_SAVE" in text
    assert "LOCAL_DATA_POLICY=prefer" in text
    assert "POST_RESPONSE_EXPORT=always_excel" in text
    assert "export_response_excel" in text


def test_build_instructions_never_local_data() -> None:
    text = build_server_instructions(
        refined_prompt=False,
        local_data_policy="never",
        post_response_export="never",
    )
    assert "LOCAL_DATA_POLICY=never" in text
    assert "LOCAL_DATA_POLICY=ask" not in text
    assert "offer_use_local_data" not in text
    assert "POST_RESPONSE_EXPORT=never" in text
    assert "POST_RESPONSE_EXPORT=ask" not in text
    assert "offer_export_response" not in text


def test_build_instructions_frugal_mode() -> None:
    text = build_server_instructions(
        refined_prompt=True,
        auto_save_refined_prompt=True,
        local_data_policy="prefer",
        post_response_export="always_excel",
        frugal_mode=True,
    )
    assert "Frugal mode" in text
    assert "Do NOT emit refined-prompt footer" in text
    assert "Document templates" not in text
    assert "Refined prompt gate" not in text
    assert "Search / Adaptive Search" not in text
    assert "POST_RESPONSE_EXPORT=always_excel" not in text
    assert "Prompt Studio (YES-gate only)" not in text
    assert "Profile credentials" in text
    assert "limit" in text and "25" in text
    assert len(text) < 4000  # ~900 tokens budget with headroom
    # Frugal must be shorter than full refined policy
    full = build_server_instructions(
        refined_prompt=True,
        local_data_policy="prefer",
        post_response_export="always_excel",
    )
    assert len(text) < len(full)


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
    assert "process_var_name=oraclecpqo" in text
    assert "table_name=ModelMaster" in text
    assert "prod_fam_var_name=laptop" in text
    assert "product_line_var_name=hp" in text
    assert "model_var_name=elite840" in text


def test_build_instructions_missing_customer_knowledge_ok() -> None:
    text = build_server_instructions(
        refined_prompt=False,
        shared_knowledge="base only",
        customer_knowledge="",
        commerce_process_aliases={},
    )
    assert "base only" in text
    assert "\n## Customer knowledge\n" not in text
    assert "## Property aliases" not in text
    assert "append_customer_knowledge" in text


def test_build_instructions_fusion_modules_note() -> None:
    empty = build_server_instructions(refined_prompt=False, fusion_modules=[])
    assert "Fusion CX modules enabled on profile" not in empty

    text = build_server_instructions(
        refined_prompt=False,
        fusion_modules=["Sales", "Service"],
    )
    assert "Fusion CX modules enabled on profile: Sales, Service" in text
    assert "registered CX tools" in text
    assert "dedicated module tools" not in text
    assert "list_partner_lov" not in text

    prm_text = build_server_instructions(
        refined_prompt=False,
        fusion_modules=["PRM"],
    )
    assert "list_partner_lov" in prm_text
    assert "LookupCode" in prm_text
