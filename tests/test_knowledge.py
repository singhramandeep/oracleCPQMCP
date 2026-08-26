"""Tests for knowledge markdown loading."""

from __future__ import annotations

from pathlib import Path

from oracle_cpq_mcp.core.knowledge import (
    load_base_knowledge,
    load_customer_knowledge,
)


def test_load_base_and_customer_knowledge(tmp_path: Path) -> None:
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    (knowledge / "CPQBaseKnowledge.md").write_text("# Base\nRule A", encoding="utf-8")
    (knowledge / "focalpoint.md").write_text("# FP\nRule B", encoding="utf-8")

    assert "Rule A" in load_base_knowledge(tmp_path)
    assert "Rule B" in load_customer_knowledge("focalpoint.md", project_root=tmp_path)


def test_missing_customer_knowledge_returns_empty(tmp_path: Path) -> None:
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    (knowledge / "CPQBaseKnowledge.md").write_text("base", encoding="utf-8")
    assert load_customer_knowledge("missing.md", project_root=tmp_path) == ""


def test_unsafe_customer_knowledge_path_rejected(tmp_path: Path) -> None:
    knowledge = tmp_path / "knowledge"
    knowledge.mkdir()
    assert load_customer_knowledge("../secret.md", project_root=tmp_path) == ""
    assert load_customer_knowledge(r"..\secret.md", project_root=tmp_path) == ""
