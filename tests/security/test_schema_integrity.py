"""Tests for tool schema integrity verification."""

from __future__ import annotations

import pytest

from oracle_cpq_mcp.security.schema_integrity import (
    compute_tool_manifest_hash,
    load_expected_manifest_hash,
    verify_schema_integrity,
)


def test_manifest_hash_matches_committed() -> None:
    expected = load_expected_manifest_hash()
    assert expected is not None
    assert compute_tool_manifest_hash() == expected


def test_verify_schema_integrity_passes_when_enabled() -> None:
    verify_schema_integrity(enabled=True)


def test_verify_schema_integrity_skipped_when_disabled() -> None:
    verify_schema_integrity(enabled=False)
