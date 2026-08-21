"""Contract tests: every catalog tool returns the standard stamped envelope."""

from __future__ import annotations

import re
from typing import Any
from unittest.mock import MagicMock

import pytest

from oracle_cpq_mcp.core.config import CPQProfile, CredentialSet
from oracle_cpq_mcp.core.errors import CPQAPIError
from oracle_cpq_mcp.registry.tool_registry import TOOL_CATALOG
from oracle_cpq_mcp.security.context import reset_session_tool_calls
from oracle_cpq_mcp.security.rate_limit import reset_rate_limits
from oracle_cpq_mcp.security.replay import reset_replay_store
from oracle_cpq_mcp.security.settings import SecuritySettings
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

SUCCESS_STATUSES = frozenset(
    {
        "ok",
        "preflight_ok",
        "preflight_failed",
        "confirmation_required",
        "read_only_blocked",
    }
)

ISO_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

TOOL_KWARGS: dict[str, dict[str, Any]] = {
    "list_users": {},
    "export_users_excel": {},
    "get_user": {"party_number": "BM_testUser"},
    "get_user_groups": {"party_number": "BM_testUser"},
    "update_user": {
        "party_number": "BM_testUser",
        "patch_body": {"firstName": "Contract"},
        "dry_run": True,
    },
    "list_groups": {},
    "get_group": {"group_var_name": "admins"},
    "list_group_users": {"group_var_name": "admins"},
    "create_group": {
        "group_body": {"variableName": "contract_group"},
        "dry_run": True,
    },
    "list_datatables": {},
    "get_datatable": {"table_name": "ModelMaster"},
    "get_datatable_rows": {"table_name": "ModelMaster"},
    "list_datatable_fields": {"table_name": "ModelMaster"},
    "get_datatable_field": {"table_name": "ModelMaster", "field_name": "Model"},
    "deploy_datatables": {"table_names": ["ModelMaster"], "dry_run": True},
    "create_datatable": {"body": {"name": "contract_new_table"}, "dry_run": True},
    "export_datatables": {"body": {"selections": ["ModelMaster"]}, "dry_run": True},
    "get_all_bml_code": {"delivery": "json"},
    "get_bml_function": {"function_id": "util.sampleFunction"},
    "search_bml_scripts": {"q_expr": "util.", "limit": 5},
    "list_bml_common_functions": {"limit": 5},
    "get_bml_common_function": {"name": "atoi"},
    "list_bml_library_folders": {"limit": 5},
    "get_bml_dependent_attributes": {"body": {"selections": ["util.sampleFunction"]}},
    "export_bml_library_functions": {
        "body": {"selections": ["util.sampleFunction"]},
        "dry_run": True,
    },
    "get_task": {"task_id": "task-123"},
    "download_task_file": {"task_id": "task-123", "file_name": "export.zip"},
    "list_product_families": {"limit": 5},
    "get_product_family": {"prod_fam_var_name": "products"},
    "list_product_lines": {"prod_fam_var_name": "products", "limit": 5},
    "get_product_line": {
        "prod_fam_var_name": "products",
        "prod_line_var_name": "servers",
    },
    "list_models": {
        "prod_fam_var_name": "products",
        "prod_line_var_name": "servers",
        "limit": 5,
    },
    "get_model": {
        "prod_fam_var_name": "products",
        "prod_line_var_name": "servers",
        "model_var_name": "modelA",
    },
    "list_config_attributes": {
        "scope": "family",
        "prod_fam_var_name": "products",
        "limit": 5,
    },
    "get_config_attribute": {
        "scope": "family",
        "prod_fam_var_name": "products",
        "attribute_var_name": "color",
    },
    "list_array_sets": {
        "scope": "model",
        "prod_fam_var_name": "products",
        "prod_line_var_name": "servers",
        "model_var_name": "modelA",
        "limit": 5,
    },
    "get_array_set": {
        "scope": "model",
        "prod_fam_var_name": "products",
        "prod_line_var_name": "servers",
        "model_var_name": "modelA",
        "array_set_var_name": "options",
    },
    "list_array_set_attributes": {
        "scope": "model",
        "prod_fam_var_name": "products",
        "prod_line_var_name": "servers",
        "model_var_name": "modelA",
        "array_set_var_name": "options",
        "limit": 5,
    },
    "get_array_set_attribute": {
        "scope": "model",
        "prod_fam_var_name": "products",
        "prod_line_var_name": "servers",
        "model_var_name": "modelA",
        "array_set_var_name": "options",
        "attribute_var_name": "qty",
    },
    "list_config_menu_items": {
        "scope": "family",
        "parent_kind": "attribute",
        "prod_fam_var_name": "products",
        "attribute_var_name": "color",
        "limit": 5,
    },
    "get_config_menu_item": {
        "scope": "family",
        "parent_kind": "attribute",
        "prod_fam_var_name": "products",
        "attribute_var_name": "color",
        "menu_item_id": "1",
    },
    "get_config_layout": {
        "scope": "model",
        "prod_fam_var_name": "products",
        "prod_line_var_name": "servers",
        "model_var_name": "modelA",
        "layout_var_name": "default",
    },
    "get_layout_cache_attributes": {
        "prod_fam_var_name": "products",
        "prod_line_var_name": "servers",
        "model_var_name": "modelA",
    },
    "get_commerce_attributes": {"process_var_name": "oraclecpqo"},
    "get_commerce_actions": {"process_var_name": "oraclecpqo"},
    "get_commerce_attribute": {
        "attribute_var_name": "status_t",
        "process_var_name": "oraclecpqo",
    },
    "get_commerce_action": {
        "action_var_name": "generateProposal",
        "process_var_name": "oraclecpqo",
    },
    "list_commerce_processes": {"limit": 5, "offset": 0},
    "get_line_attributes": {"process_var_name": "oraclecpqo"},
    "get_line_actions": {"process_var_name": "oraclecpqo"},
    "list_transactions": {"limit": 5, "offset": 0, "process_var_name": "oraclecpqo"},
    "get_transaction": {"transaction_id": "12345", "process_var_name": "oraclecpqo"},
    "list_transaction_lines": {
        "transaction_id": "12345",
        "limit": 5,
        "process_var_name": "oraclecpqo",
    },
    "get_transaction_line": {
        "transaction_id": "12345",
        "document_number": "1",
        "process_var_name": "oraclecpqo",
    },
    "get_document_layout": {"process_var_name": "oraclecpqo"},
    "generate_proposal": {
        "transaction_id": "12345",
        "process_var_name": "oraclecpqo",
        "dry_run": True,
    },
    "export_attachment": {
        "transaction_id": "12345",
        "attribute_var_name": "proposalAttachment_t",
        "process_var_name": "oraclecpqo",
        "dry_run": True,
    },
    "download_attachment": {
        "transaction_id": "12345",
        "attribute_var_name": "proposalAttachment_t",
        "process_var_name": "oraclecpqo",
    },
    "copy_transaction": {
        "transaction_id": "12345",
        "process_var_name": "oraclecpqo",
        "dry_run": True,
    },
    "copy_transaction_lines": {
        "transaction_id": "12345",
        "process_var_name": "oraclecpqo",
        "dry_run": True,
    },
    "list_performance_logs": {"limit": 5, "offset": 0},
    "get_performance_log": {"log_id": "12345"},
    "export_performance_logs": {"dry_run": True},
    "list_parts": {"limit": 5, "offset": 0},
    "get_part": {"part_id": "FSM1C"},
    "search_parts": {"body": {"criteria": {"partNumber": "FSM1C"}}},
    "discover_tools": {},
    "list_saved_prompts": {},
    "search_saved_prompts": {},
    "get_saved_prompt": {"prompt_id": "00000000-0000-0000-0000-000000000001"},
    "record_prompt_use": {"prompt_id": "00000000-0000-0000-0000-000000000001"},
    "save_refined_prompt": {
        "title": "Example",
        "original_user_prompt": "list users",
        "refined_prompt": "List {{status_filter}} users",
    },
    "offer_save_refined_prompt": {
        "title": "Example",
        "original_user_prompt": "list users",
        "refined_prompt": "List {{status_filter}} users",
        "save": False,
    },
    "set_auto_save_refined_prompt": {"enabled": False},
    "set_saved_prompt_enabled": {
        "prompt_id": "00000000-0000-0000-0000-000000000001",
        "enabled": True,
    },
    "start_prompt_picker": {},
    "list_local_data": {},
    "get_local_data_status": {"domain": "users"},
    "load_local_data": {"domain": "users"},
    "offer_use_local_data": {"domain": "users", "choice": "fetch_fresh"},
    "set_local_data_policy": {"policy": "ask"},
    "sync_users_local": {},
    "sync_groups_local": {},
    "sync_bml_local": {},
    "sync_commerce_metadata_local": {"process_var_name": "oraclecpqo"},
    "sync_datatable_local": {"table_name": "ModelMaster"},
    "sync_datatables_local": {"table_names": ["ModelMaster"]},
}


class FakeMcp:
    """Capture tools registered via mcp.tool(...)(fn)."""

    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self, **_kwargs: Any):
        def decorator(fn: Any) -> Any:
            self.tools[fn.__name__] = fn
            return fn

        return decorator


class FakeCPQClient:
    """Minimal CPQ client for offline contract runs."""

    def __init__(self, profile: CPQProfile) -> None:
        self.profile = profile

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        # create_group preflight expects 404 when the group name is free
        if path.endswith("/groups/contract_group"):
            raise CPQAPIError(
                "not found",
                status_code=404,
                method="GET",
                path=path,
                body={"title": "Not Found"},
            )
        if path.endswith("/datatables/contract_new_table"):
            raise CPQAPIError(
                "not found",
                status_code=404,
                method="GET",
                path=path,
                body={"title": "Not Found"},
            )
        if path.startswith("/tasks/") and "/files/" not in path:
            return {"taskId": path.rsplit("/", 1)[-1], "status": "SUCCEEDED"}
        if path.startswith("/users/") and path.count("/") == 2:
            return {"partyNumber": path.rsplit("/", 1)[-1], "login": "contract_user"}
        if path.startswith("/performanceLogs/") and path.count("/") == 2:
            return {"id": int(path.rsplit("/", 1)[-1]), "event": "Logout", "login": "contract_user"}
        if "/commerceDocuments" in path and "/actions/" not in path:
            # Single transaction / line resource or collection
            if path.rstrip("/").endswith("Transaction") or path.endswith("/transactionLine"):
                return {
                    "items": [],
                    "hasMore": False,
                    "offset": 0,
                    "limit": 100,
                    "count": 0,
                }
            return {"id": 12345, "transactionId": 12345, "proposalAttachment_t": {
                "fileName": "proposal.pdf",
                "fileLocation": (
                    "https://dev.example.com/rest/v18/commerceProcesses/oraclecpqo/"
                    "documents/1/attachmentAttributes/proposalAttachment_t/"
                    "transactions/12345/documentNumbers/1"
                ),
            }}
        if path.startswith("/commerceProcesses/") and "/layouts/" in path:
            return {"layout": True}
        if path.startswith("/datatables/") and path.count("/") == 2:
            return {"name": path.rsplit("/", 1)[-1], "variableName": path.rsplit("/", 1)[-1]}
        if "/groups/" in path and not path.endswith("/users") and path.count("/") >= 4:
            return {"variableName": path.rsplit("/", 1)[-1]}
        return {
            "items": [],
            "hasMore": False,
            "offset": 0,
            "limit": 100,
            "count": 0,
            "totalResults": 0,
        }

    def get_bytes(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        accept: str = "application/zip",
    ) -> bytes:
        return b"PK\x03\x04fake-zip"

    def post_bytes(
        self,
        path: str,
        *,
        json_body: Any = None,
        params: dict[str, Any] | None = None,
        accept: str = "*/*",
    ) -> bytes:
        return b'{"exported": true}'

    def post(self, path: str, *, json_body: Any = None, params: dict[str, Any] | None = None) -> Any:
        return {"status": "ok"}

    def patch(self, path: str, *, json_body: Any) -> Any:
        return {"status": "ok"}

    def put(self, path: str, *, json_body: Any) -> Any:
        return {"status": "ok"}

    def delete(self, path: str) -> Any:
        return {"status": "ok"}


def _lead_envelope(result: Any) -> dict[str, Any]:
    if isinstance(result, list):
        assert result, "attachment tool returned empty list"
        assert isinstance(result[0], dict), "attachment lead must be a dict"
        return result[0]
    assert isinstance(result, dict), f"expected dict envelope, got {type(result)}"
    return result


def _assert_stamped_envelope(envelope: dict[str, Any]) -> None:
    status = envelope.get("status")
    assert status in SUCCESS_STATUSES | {"error"}, f"unexpected status: {status}"
    assert envelope.get("environment") == "dev"
    assert envelope.get("customer_id") == "test"
    retrieved = envelope.get("retrieved_at")
    assert isinstance(retrieved, str) and ISO_Z_RE.match(retrieved), retrieved

    if status == "error":
        assert "code" in envelope and "message" in envelope
        details = envelope.get("details") or {}
        assert "curl" not in details
        assert "response" not in details
        assert "body" not in details
        blob = str(envelope).lower()
        assert "password" not in blob or "must-not" in blob
        return

    assert envelope.get("tool")
    assert "data" in envelope


@pytest.fixture()
def registered_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    reset_session_tool_calls()
    reset_rate_limits()
    reset_replay_store()

    cfg = tmp_path / ".config"
    cfg.mkdir()
    (cfg / "test.env").write_text(
        "CUSTOMER_NAME=Test\nDEFAULT_ENVIRONMENT=dev\n"
        "DEV_URL=https://dev.example.com\n"
        "DEV_USERNAME=user\nDEV_PASSWORD=secret\n"
        "AUTO_SAVE_REFINED_PROMPT=false\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CPQ_CONFIG_DIR", str(cfg))
    monkeypatch.setenv("CPQ_LOCAL_DATA_DIR", str(tmp_path / "data"))

    profile = CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v18",
        company_login_name="_host",
        read_only=False,
        custom_data_table_names=["ModelMaster"],
        commerce_process_var_names=["oraclecpqo"],
    )
    settings = SecuritySettings(
        confirmation_secret="test-secret-key-for-hmac",
        confirmation_ttl_seconds=300,
        schema_integrity_enabled=False,
        max_tool_calls_per_session=100,
        rate_limit_enabled=False,
        audit_enabled=False,
        allow_prod=False,
        max_response_bytes=2_000_000,
        replay_window_seconds=60,
        read_calls_per_minute=120,
        write_calls_per_minute=10,
        privileged_calls_per_minute=5,
    )
    configure_security(profile, settings)

    mcp = FakeMcp()
    client = FakeCPQClient(profile)
    register_user_tools(mcp, client)  # type: ignore[arg-type]
    register_group_tools(mcp, client)  # type: ignore[arg-type]
    register_datatable_tools(mcp, client)  # type: ignore[arg-type]
    register_bml_tools(mcp, client)  # type: ignore[arg-type]
    register_commerce_tools(mcp, client)  # type: ignore[arg-type]
    register_transaction_tools(mcp, client)  # type: ignore[arg-type]
    register_parts_tools(mcp, client)  # type: ignore[arg-type]
    register_performance_tools(mcp, client)  # type: ignore[arg-type]
    register_tasks_tools(mcp, client)  # type: ignore[arg-type]
    register_configuration_tools(mcp, client)  # type: ignore[arg-type]
    register_local_data_tools(mcp, client)  # type: ignore[arg-type]
    register_discovery_tools(mcp)
    register_saved_prompt_tools(mcp)

    missing = set(TOOL_CATALOG) - set(mcp.tools)
    assert not missing, f"tools not registered: {sorted(missing)}"
    return mcp.tools


@pytest.mark.parametrize("tool_name", sorted(TOOL_CATALOG))
def test_tool_contract_envelope(tool_name: str, registered_tools: dict[str, Any]) -> None:
    assert tool_name in TOOL_KWARGS, f"add default kwargs for {tool_name}"
    fn = registered_tools[tool_name]
    result = fn(**TOOL_KWARGS[tool_name])
    envelope = _lead_envelope(result)
    _assert_stamped_envelope(envelope)


def test_error_contract_omits_unsafe_details(registered_tools: dict[str, Any]) -> None:
    """Force a CPQ error through get_user and assert sanitization."""
    client = MagicMock()
    client.profile = CPQProfile(
        customer_name="Test",
        customer_id="test",
        environment="dev",
        base_url="https://dev.example.com",
        credentials=[CredentialSet(username="user", password="secret")],
        rest_version="v18",
        company_login_name="_host",
        read_only=False,
    )

    def boom(path: str, *, params: dict[str, Any] | None = None) -> Any:
        raise CPQAPIError(
            "CPQ API error 500",
            status_code=500,
            method="GET",
            path=path,
            body={"password": "leak-me", "token": "abc"},
            curl_command="curl -u 'user:secret' https://example/x",
        )

    client.get.side_effect = boom

    reset_session_tool_calls()
    mcp = FakeMcp()
    configure_security(
        client.profile,
        SecuritySettings(
            confirmation_secret="test-secret-key-for-hmac",
            confirmation_ttl_seconds=300,
            schema_integrity_enabled=False,
            max_tool_calls_per_session=100,
            rate_limit_enabled=False,
            audit_enabled=False,
            allow_prod=False,
            max_response_bytes=2_000_000,
            replay_window_seconds=60,
            read_calls_per_minute=120,
            write_calls_per_minute=10,
            privileged_calls_per_minute=5,
        ),
    )
    register_user_tools(mcp, client)
    result = mcp.tools["get_user"](party_number="BM_x")
    envelope = _lead_envelope(result)
    assert envelope["status"] == "error"
    _assert_stamped_envelope(envelope)
    details = envelope.get("details") or {}
    assert "curl" not in details
    assert "response" not in details
    assert "leak-me" not in str(envelope)
