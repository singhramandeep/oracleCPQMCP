"""Tests for tool schema integrity verification."""

from __future__ import annotations

from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG, _spec
from oracle_cpq_mcp.security.schema_integrity import (
    collect_version_bump_violations,
    compute_tool_manifest_hash,
    load_expected_manifest_hash,
    tool_definition_sha256,
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


def test_version_bump_required_when_identity_changes() -> None:
    spec = TOOL_CATALOG["list_users"]
    previous = {
        "list_users": {
            "version": spec.version,
            "definition_sha256": "0" * 64,
        }
    }
    violations = collect_version_bump_violations(previous)
    assert any(v.startswith("list_users:") for v in violations)


def test_version_bump_ok_when_version_changed() -> None:
    spec = TOOL_CATALOG["list_users"]
    previous = {
        "list_users": {
            "version": "0.9.0",
            "definition_sha256": "0" * 64,
        }
    }
    assert collect_version_bump_violations(previous) == []


def test_version_bump_ok_when_hash_unchanged() -> None:
    spec = TOOL_CATALOG["list_users"]
    previous = {
        "list_users": {
            "version": spec.version,
            "definition_sha256": tool_definition_sha256(spec, include_version=False),
        }
    }
    assert collect_version_bump_violations(previous) == []


def test_identity_hash_excludes_version() -> None:
    base = TOOL_CATALOG["get_user"]
    bumped = _spec(
        base.name,
        domain=base.domain,
        operation=base.operation,
        description=base.description,
        tags=set(base.tags) - {base.domain, base.operation},
        read_only=base.read_only,
        destructive=base.destructive,
        http_method=base.http_method,
        api_path=base.api_path,
        title=base.title,
        version="9.9.9",
    )
    assert tool_definition_sha256(base, include_version=False) == tool_definition_sha256(
        bumped, include_version=False
    )
