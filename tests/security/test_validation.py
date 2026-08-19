"""Tests for strict tool input validation."""

from __future__ import annotations

import pytest

from oracle_cpq_mcp.security.exceptions import ValidationSecurityError
from oracle_cpq_mcp.security.validation import validate_tool_input


def test_get_user_valid() -> None:
    result = validate_tool_input("get_user", {"party_number": "BM_abc123"})
    assert result["party_number"] == "BM_abc123"


def test_get_user_rejects_extra_fields() -> None:
    with pytest.raises(ValidationSecurityError):
        validate_tool_input("get_user", {"party_number": "abc", "tenant_id": "evil"})


def test_get_user_rejects_invalid_id() -> None:
    with pytest.raises(ValidationSecurityError):
        validate_tool_input("get_user", {"party_number": "../../etc/passwd"})


def test_update_user_requires_patch_body() -> None:
    with pytest.raises(ValidationSecurityError):
        validate_tool_input(
            "update_user",
            {"party_number": "abc", "patch_body": {}},
        )
